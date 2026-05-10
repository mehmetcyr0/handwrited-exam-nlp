"""
Çoklu OCR: PaddleOCR (tr) + EasyOCR (tr/en) + RapidOCR (ONNX, Latin).
Kutular okuma sırasına göre satırlara gruplanır; NMS ile birleştirilir.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from services.image_processing import (
    ensure_ocr_long_edge,
    prepare_bgr_for_ocr,
    prepare_bgr_for_ocr_bilateral,
    prepare_bgr_for_ocr_percentile,
    prepare_bgr_for_ocr_sharp,
    read_image_bgr,
)
from services.turkish_ocr_repair import normalize_extracted_student_text, repair_turkish_handwriting_text

logger = logging.getLogger(__name__)

_ocr_engine = None
_easyocr_reader: Any = None  # None: henüz denenmedi; False: yüklenemedi; aksi halde Reader
_rapid_ocr_engine: Any = None  # False: RapidOCR yok; aksi halde RapidOCR örneği


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR

        # Tespit: daha düşük eşik + genişletilmiş kutu + dilasyon (ince bağlantılar)
        # Not: PaddleOCR içinde rec_image_shape sabitleniyor; iyileştirme ağırlıklı olarak det + ön işleme.
        _ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang="tr",
            show_log=False,
            det_limit_side_len=2880,
            det_db_thresh=0.18,
            det_db_box_thresh=0.45,
            det_db_unclip_ratio=1.85,
            use_dilation=True,
            drop_score=0.12,
        )
    return _ocr_engine


def _get_easyocr():
    """Türkçe + İngilizce el yazısı için ikinci motor (torch gerekir). Başarısızsa None."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr

            _easyocr_reader = easyocr.Reader(["tr", "en"], gpu=False, verbose=False)
            logger.info("EasyOCR (tr+en) yüklendi")
        except Exception as e:
            logger.warning("EasyOCR kullanılamıyor, yalnızca Paddle: %s", e)
            _easyocr_reader = False
    return _easyocr_reader if _easyocr_reader is not False else None


def _get_rapidocr():
    """
    RapidOCR (ONNX Runtime): Torch gerektirmez; Latin tanıma Türkçe harfler için uygundur.
    İlk çalıştırmada modeller indirilir (ağ gerekir).
    """
    global _rapid_ocr_engine
    if _rapid_ocr_engine is None:
        try:
            from rapidocr import EngineType, LangDet, LangRec, ModelType, OCRVersion, RapidOCR

            base = {
                "Det.engine_type": EngineType.ONNXRUNTIME,
                "Cls.engine_type": EngineType.ONNXRUNTIME,
                "Rec.engine_type": EngineType.ONNXRUNTIME,
                "Det.lang_type": LangDet.MULTI,
                "Det.model_type": ModelType.MOBILE,
                "Det.ocr_version": OCRVersion.PPOCRV4,
                "Rec.lang_type": LangRec.LATIN,
                "Rec.model_type": ModelType.MOBILE,
                "Rec.ocr_version": OCRVersion.PPOCRV5,
            }
            try:
                _rapid_ocr_engine = RapidOCR(params=base)
            except Exception as e:
                logger.warning("RapidOCR PP-OCRv5 tanıma denemesi başarısız, v4 deneniyor: %s", e)
                base["Rec.ocr_version"] = OCRVersion.PPOCRV4
                _rapid_ocr_engine = RapidOCR(params=base)
            logger.info("RapidOCR (ONNX, Latin) yüklendi")
        except Exception as e:
            logger.warning("RapidOCR kullanılamıyor: %s", e)
            _rapid_ocr_engine = False
    return _rapid_ocr_engine if _rapid_ocr_engine is not False else None


def _rapidocr_read_items(engine: Any, img_bgr: np.ndarray) -> list[dict[str, Any]]:
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    items: list[dict[str, Any]] = []
    try:
        result = engine(rgb, use_det=True, use_cls=True, use_rec=True)
    except Exception as e:
        logger.warning("RapidOCR çıkarım: %s", e)
        return items
    if result is None:
        return items
    boxes = getattr(result, "boxes", None)
    txts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    if boxes is None or txts is None or scores is None:
        return items
    for i, raw_txt in enumerate(txts):
        text = (raw_txt or "").strip()
        if not text:
            continue
        try:
            b = boxes[i]
            box = [[float(p[0]), float(p[1])] for p in b]
            conf = float(scores[i]) if i < len(scores) else 0.5
        except (TypeError, IndexError, ValueError):
            continue
        items.append({"box": box, "text": text, "conf": conf})
    return items


def _easyocr_read_items(reader, img_bgr: np.ndarray) -> list[dict[str, Any]]:
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    items: list[dict[str, Any]] = []
    try:
        raw = reader.readtext(
            rgb,
            paragraph=False,
            detail=1,
            text_threshold=0.52,
            low_text=0.32,
            link_threshold=0.34,
        )
    except Exception as e:
        logger.warning("EasyOCR readtext: %s", e)
        return items
    for row in raw:
        if not row or len(row) < 3:
            continue
        box_pts, text, conf = row[0], row[1], row[2]
        text = (text or "").strip()
        if not text:
            continue
        box = [[float(p[0]), float(p[1])] for p in box_pts]
        items.append({"box": box, "text": text, "conf": float(conf)})
    return items


def _box_center(box: list | tuple) -> tuple[float, float]:
    ys = [float(p[1]) for p in box]
    xs = [float(p[0]) for p in box]
    return (sum(ys) / len(ys), sum(xs) / len(xs))


def _axis_aligned_bbox(box: list | tuple) -> tuple[float, float, float, float]:
    xs = [float(p[0]) for p in box]
    ys = [float(p[1]) for p in box]
    return min(xs), min(ys), max(xs), max(ys)


def _iou_xyxy(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    aa = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    ba = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = aa + ba - inter
    return inter / union if union > 0 else 0.0


def _nms_items(items: list[dict[str, Any]], iou_thresh: float = 0.38) -> list[dict[str, Any]]:
    """Çoklu OCR geçişlerinde üst üste binen aynı kelime kutularını tekilleştir (yüksek güven kazanır)."""
    if not items:
        return []
    items = sorted(items, key=lambda x: -x["conf"])
    kept: list[dict[str, Any]] = []
    boxes_kept: list[tuple[float, float, float, float]] = []
    for it in items:
        bb = _axis_aligned_bbox(it["box"])
        if any(_iou_xyxy(bb, kb) >= iou_thresh for kb in boxes_kept):
            continue
        kept.append(it)
        boxes_kept.append(bb)
    kept.sort(key=lambda x: _box_center(x["box"]))
    return kept


def _slice_kw(h: int, w: int) -> dict[str, int]:
    if max(h, w) < 2000:
        return {}
    return {
        "horizontal_stride": 360,
        "vertical_stride": 360,
        "merge_x_thres": 65,
        "merge_y_thres": 42,
    }


def _page_to_items(page: list | None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not page:
        return items
    for item in page:
        if not item or len(item) < 2:
            continue
        box, rec = item[0], item[1]
        if not isinstance(rec, (list, tuple)) or len(rec) < 2:
            continue
        text, conf = rec[0], rec[1]
        text = (text or "").strip()
        if not text:
            continue
        items.append({"box": box, "text": text, "conf": float(conf)})
    return items


def _run_ocr_pass(ocr, img_bgr: np.ndarray, slice_arg: dict[str, int]) -> list[dict[str, Any]]:
    if slice_arg:
        result = ocr.ocr(img_bgr, cls=True, slice=slice_arg)
    else:
        result = ocr.ocr(img_bgr, cls=True)
    page = result[0] if result and isinstance(result, (list, tuple)) else result
    return _page_to_items(page)


def _norm_token(s: str) -> str:
    return " ".join((s or "").lower().split())


def _repair_turkish_ocr(text: str) -> str:
    return repair_turkish_handwriting_text(text)


def _items_to_physical_lines(items: list[dict[str, Any]]) -> list[str]:
    """
    Aynı yazı satırındaki kutuları (benzer y) soldan sağa birleştir.
    Böylece her kutu için ayrı satır yerine gerçek paragraflar elde edilir.
    """
    if not items:
        return []

    heights: list[float] = []
    for it in items:
        box = it["box"]
        ys = [float(p[1]) for p in box]
        heights.append(max(ys) - min(ys))
    heights.sort()
    med_h = heights[len(heights) // 2] if heights else 22.0
    y_tol = max(med_h * 0.65, 14.0)

    sorted_items = sorted(items, key=lambda it: _box_center(it["box"]))

    rows: list[list[dict[str, Any]]] = []
    row: list[dict[str, Any]] = []
    row_cy: float | None = None

    for it in sorted_items:
        cy, cx = _box_center(it["box"])
        if row_cy is None:
            row = [it]
            row_cy = cy
        elif abs(cy - row_cy) <= y_tol:
            row.append(it)
            row_cy = sum(_box_center(x["box"])[0] for x in row) / len(row)
        else:
            row.sort(key=lambda x: _box_center(x["box"])[1])
            rows.append(row)
            row = [it]
            row_cy = cy
    if row:
        row.sort(key=lambda x: _box_center(x["box"])[1])
        rows.append(row)

    line_strings: list[str] = []
    for r in rows:
        parts: list[str] = []
        for it in r:
            w = it["text"].strip()
            if not w:
                continue
            if parts and _norm_token(parts[-1]) == _norm_token(w):
                continue
            parts.append(w)
        line = _repair_turkish_ocr(" ".join(parts))
        if line:
            line_strings.append(line)
    return line_strings


def _bgr_mild_only(scaled_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(scaled_bgr, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def extract_text_from_array(img_bgr: np.ndarray) -> dict[str, Any]:
    if img_bgr is None or img_bgr.size == 0:
        raise ValueError("OCR için geçersiz görüntü")

    ocr = _get_ocr()
    scaled = ensure_ocr_long_edge(img_bgr, min_long=1920, max_long=4200)
    h, w = scaled.shape[:2]
    sl = _slice_kw(h, w)

    # Çoklu ön işleme: farklı kağıt/kalem tiplerinde tamamlayıcı sinyal
    pass_a = _run_ocr_pass(ocr, prepare_bgr_for_ocr(scaled, denoise_h=5), sl)
    pass_b = _run_ocr_pass(ocr, prepare_bgr_for_ocr(scaled, denoise_h=0), sl)
    pass_c = _run_ocr_pass(ocr, _bgr_mild_only(scaled), sl)
    pass_d = _run_ocr_pass(ocr, prepare_bgr_for_ocr_sharp(scaled), sl)
    pass_e = _run_ocr_pass(ocr, prepare_bgr_for_ocr_bilateral(scaled), sl)

    paddle_items = _nms_items(pass_a + pass_b + pass_c + pass_d + pass_e, iou_thresh=0.36)

    easy_reader = _get_easyocr()
    easy_items: list[dict[str, Any]] = []
    if easy_reader is not None:
        # İki tamamlayıcı ön işleme; slice EasyOCR'da yok — büyük görüntüde canvas içinde parça parça okur
        e1 = _easyocr_read_items(easy_reader, prepare_bgr_for_ocr(scaled, denoise_h=5))
        e2 = _easyocr_read_items(easy_reader, prepare_bgr_for_ocr_sharp(scaled))
        easy_items = _nms_items(e1 + e2, iou_thresh=0.34)

    rapid_engine = _get_rapidocr()
    rapid_items: list[dict[str, Any]] = []
    if rapid_engine is not None:
        z1 = _rapidocr_read_items(rapid_engine, prepare_bgr_for_ocr(scaled, denoise_h=5))
        z2 = _rapidocr_read_items(rapid_engine, prepare_bgr_for_ocr_sharp(scaled))
        z3 = _rapidocr_read_items(rapid_engine, prepare_bgr_for_ocr_percentile(scaled))
        rapid_items = _nms_items(z1 + z2 + z3, iou_thresh=0.34)

    merged_items = _nms_items(paddle_items + easy_items + rapid_items, iou_thresh=0.36)
    line_strings = _items_to_physical_lines(merged_items)

    # Tek paragraf: OCR gürültüsü + tekrarlar temizlenir (puanlama / görüntüleme)
    full_text = normalize_extracted_student_text(" ".join(line_strings))
    full_text_multiline = "\n".join(
        normalize_extracted_student_text(line) for line in line_strings if line.strip()
    )

    blocks = [{"text": m["text"], "confidence": m["conf"], "box": m["box"]} for m in merged_items]
    structured = {
        "blocks": blocks,
        "line_count": len(line_strings),
        "lines": line_strings,
        "full_text_multiline": full_text_multiline,
    }
    logger.info(
        "OCR: %d kutu (Paddle 5 + Easy %d + Rapid %d) -> %d satır, paragraf %d karakter",
        len(merged_items),
        len(easy_items),
        len(rapid_items),
        len(line_strings),
        len(full_text),
    )
    return {"full_text": full_text, "structured": structured}


def extract_text_from_image(image_path: Path) -> dict[str, Any]:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    img = read_image_bgr(path)
    if img is None:
        raise ValueError(f"OCR için görüntü okunamadı: {path}")

    out = extract_text_from_array(img)
    logger.info("OCR extracted from %s", path)
    return out


def structured_to_json(structured: dict[str, Any]) -> str:
    return json.dumps(structured, ensure_ascii=False)


def parse_question_answer_heuristic(full_text: str) -> list[dict[str, str]]:
    """
    Cevap anahtarı / öğrenci metnini soru dilimlerine böler.
    - Satır başı: 1. 2) Soru 1 Q2
    - Tek paragraf (OCR): boşluk + 1-99 + . veya ) + boşluk (ör. "... bir 2. ikinci cevap")
    """
    text = full_text.strip()
    if not text:
        return []

    pattern = re.compile(
        r"(?:^|\n)\s*(?:(\d+)[.)]\s*|(?:Soru|soru|Q|q)\s*(\d+)\s*[:.)]?\s*)"
        r"|(?<=[\s])([1-9]\d{0,1})[.)]\s+(?=\S)",
        re.MULTILINE | re.IGNORECASE,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return [{"question_id": "1", "answer": text}]

    pairs: list[dict[str, str]] = []
    for i, m in enumerate(matches):
        qid = m.group(1) or m.group(2) or m.group(3) or str(i + 1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = text[start:end].strip()
        pairs.append({"question_id": qid, "answer": segment})
    return pairs
