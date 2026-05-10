"""
PaddleOCR: detect regions and extract handwritten/printed text.
Returns structured blocks (lines/regions) and merged full text.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ocr_engine = None


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR

        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en")
    return _ocr_engine


def extract_text_from_image(image_path: Path) -> dict[str, Any]:
    """
    Run OCR on a single image file.
    Returns dict with keys: full_text, blocks (list of {text, confidence, box}).
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    ocr = _get_ocr()
    result = ocr.ocr(str(path), cls=True)
    blocks: list[dict[str, Any]] = []
    lines: list[str] = []

    page = None
    if result:
        page = result[0] if isinstance(result, (list, tuple)) else result

    if page:
        for item in page:
            if not item or len(item) < 2:
                continue
            box, rec = item[0], item[1]
            if isinstance(rec, (list, tuple)) and len(rec) >= 2:
                text, conf = rec[0], rec[1]
            else:
                continue
            text = (text or "").strip()
            if not text:
                continue
            blocks.append({"text": text, "confidence": float(conf), "box": box})
            lines.append(text)

    full_text = "\n".join(lines)
    structured = {"blocks": blocks, "line_count": len(lines)}
    logger.info("OCR extracted %d lines from %s", len(lines), path)
    return {"full_text": full_text, "structured": structured}


def structured_to_json(structured: dict[str, Any]) -> str:
    return json.dumps(structured, ensure_ascii=False)


def parse_question_answer_heuristic(full_text: str) -> list[dict[str, str]]:
    """
    Best-effort split into Q/A pairs using patterns like '1.', 'Q1', 'Soru 1', etc.
    Falls back to single segment if no pattern matches.
    """
    text = full_text.strip()
    if not text:
        return []

    pattern = re.compile(
        r"(?:^|\n)\s*(?:(\d+)[.)]\s*|(?:Q|q|Soru|soru)\s*(\d+)\s*[:.)]?\s*)([^\n]*)",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return [{"question_id": "1", "answer": text}]

    pairs: list[dict[str, str]] = []
    for i, m in enumerate(matches):
        qid = m.group(1) or m.group(2) or str(i + 1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = text[start:end].strip()
        pairs.append({"question_id": qid, "answer": segment or m.group(3).strip()})
    return pairs
