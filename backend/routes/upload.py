import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from database.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()
UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"
ALLOWED = {".jpg", ".jpeg", ".png", ".pdf"}


@router.post("/upload")
async def upload_exam(file: UploadFile = File(...)):
    """
    Upload exam image or PDF. Files are stored under backend/uploads/.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Dosya adı gerekli")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenen formatlar: {', '.join(sorted(ALLOWED))}",
        )

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    stored_path = UPLOAD_ROOT / stored_name

    try:
        with stored_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO uploads (original_filename, stored_path, content_type)
                VALUES (?, ?, ?)
                """,
                (file.filename, str(stored_path), file.content_type or ""),
            )
            upload_id = cur.lastrowid
    except Exception as e:
        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass
        logger.exception("Upload DB insert failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    logger.info("Uploaded id=%s path=%s", upload_id, stored_path)
    return {
        "id": upload_id,
        "filename": file.filename,
        "stored_path": str(stored_path),
        "message": "Yükleme başarılı",
    }
