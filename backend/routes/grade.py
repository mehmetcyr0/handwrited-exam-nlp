import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.db import get_connection
from services.grading_service import grade as run_grade
from services.ocr_service import parse_question_answer_heuristic
from services.semantic_service import similarity_percentage

logger = logging.getLogger(__name__)

router = APIRouter()


class GradeRequest(BaseModel):
    extraction_id: int = Field(..., ge=1)
    answer_key: str = Field(..., min_length=1, description="Cevap anahtarı metni")
    max_score: float = Field(100.0, gt=0, le=1000)


@router.post("/grade")
def grade_exam(req: GradeRequest):
    """
    Compare extracted student text with answer key using semantic similarity (cosine on embeddings).
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, extracted_text, structured_json
            FROM extractions WHERE id = ?
            """,
            (req.extraction_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Çıkarım kaydı bulunamadı")

    student_text = row["extracted_text"] or ""
    key_text = req.answer_key.strip()

    structured = {}
    if row["structured_json"]:
        try:
            structured = json.loads(row["structured_json"])
        except json.JSONDecodeError:
            pass

    key_qa = parse_question_answer_heuristic(key_text)
    stu_qa = structured.get("question_answers") or parse_question_answer_heuristic(student_text)

    similarity = None
    per_question = []

    if key_qa and stu_qa and len(key_qa) == len(stu_qa):
        scores = []
        for k, s in zip(key_qa, stu_qa):
            pct = similarity_percentage(k.get("answer", ""), s.get("answer", ""))
            scores.append(pct)
            per_question.append(
                {
                    "question_id": s.get("question_id", k.get("question_id")),
                    "similarity_percent": pct,
                }
            )
        similarity = round(sum(scores) / len(scores), 2) if scores else 0.0
    elif key_qa and stu_qa:
        # Different counts: fall back to whole-document similarity
        similarity = similarity_percentage(key_text, student_text)
        per_question = []
    else:
        similarity = similarity_percentage(key_text, student_text)

    result = run_grade(similarity, req.max_score)

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO grades (
                extraction_id, answer_key_text, similarity_percent,
                final_score, max_score, feedback
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                req.extraction_id,
                key_text[:50000],
                result.similarity_percent,
                result.final_score,
                result.max_score,
                result.feedback,
            ),
        )
        grade_id = cur.lastrowid

    logger.info("Grade id=%s extraction_id=%s sim=%s", grade_id, req.extraction_id, similarity)
    return {
        "grade_id": grade_id,
        "extraction_id": req.extraction_id,
        "similarity_percent": result.similarity_percent,
        "final_score": result.final_score,
        "max_score": result.max_score,
        "feedback": result.feedback,
        "per_question": per_question,
        "extracted_preview": student_text[:2000],
    }
