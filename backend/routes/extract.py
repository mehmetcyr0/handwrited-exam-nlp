import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.db import get_connection
from services.image_processing import prepare_bgr_for_ocr, read_image_bgr, write_bgr_path
from services.ocr_service import extract_text_from_array, parse_question_answer_heuristic, structured_to_json
from services.pdf_utils import pdf_first_page_to_png

logger = logging.getLogger(__name__)

router = APIRouter()


class ExtractRequest(BaseModel):
    upload_id: int = Field(..., ge=1)


@router.post("/extract")
def extract_text(req: ExtractRequest):
    """
    Process stored upload (image or PDF), run OpenCV pipeline + PaddleOCR.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, stored_path, original_filename FROM uploads WHERE id = ?",
            (req.upload_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Yükleme bulunamadı")

    stored = Path(row["stored_path"])
    if not stored.is_file():
        raise HTTPException(status_code=404, detail="Dosya diskte yok")

    suffix = stored.suffix.lower()
    work_image = stored
    temp_pdf_png: Path | None = None

    try:
        if suffix == ".pdf":
            temp_pdf_png = pdf_first_page_to_png(stored, stored.parent)
            work_image = temp_pdf_png

        bgr = read_image_bgr(work_image)
        if bgr is None:
            raise ValueError(f"Görüntü okunamadı: {work_image}")
        ocr_bgr = prepare_bgr_for_ocr(bgr)
        ocr_out = extract_text_from_array(ocr_bgr)
        preview_path = write_bgr_path(
            work_image.with_name(f"{work_image.stem}_ocr_preview.png"), ocr_bgr
        )
        qa = parse_question_answer_heuristic(ocr_out["full_text"])
        structured = ocr_out["structured"]
        structured["question_answers"] = qa

        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO extractions (upload_id, extracted_text, structured_json)
                VALUES (?, ?, ?)
                """,
                (
                    req.upload_id,
                    ocr_out["full_text"],
                    structured_to_json(structured),
                ),
            )
            extraction_id = cur.lastrowid

        logger.info("Extraction id=%s for upload_id=%s", extraction_id, req.upload_id)
        return {
            "extraction_id": extraction_id,
            "upload_id": req.upload_id,
            "extracted_text": ocr_out["full_text"],
            "structured": structured,
            "processed_image": str(preview_path),
        }
    except Exception as e:
        logger.exception("Extract failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if temp_pdf_png and temp_pdf_png.is_file():
            try:
                temp_pdf_png.unlink()
            except OSError:
                pass
