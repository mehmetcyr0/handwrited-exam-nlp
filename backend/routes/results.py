import json
import logging

from fastapi import APIRouter, HTTPException

from database.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/results/{grade_id}")
def get_results(grade_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT g.id, g.extraction_id, g.answer_key_text, g.similarity_percent,
                   g.final_score, g.max_score, g.feedback, g.created_at,
                   e.extracted_text, e.structured_json, e.upload_id
            FROM grades g
            JOIN extractions e ON e.id = g.extraction_id
            WHERE g.id = ?
            """,
            (grade_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Sonuç bulunamadı")

    structured = None
    if row["structured_json"]:
        try:
            structured = json.loads(row["structured_json"])
        except json.JSONDecodeError:
            structured = None

    return {
        "grade_id": row["id"],
        "extraction_id": row["extraction_id"],
        "upload_id": row["upload_id"],
        "similarity_percent": row["similarity_percent"],
        "final_score": row["final_score"],
        "max_score": row["max_score"],
        "feedback": row["feedback"],
        "answer_key": row["answer_key_text"],
        "extracted_text": row["extracted_text"],
        "structured": structured,
        "created_at": row["created_at"],
    }
