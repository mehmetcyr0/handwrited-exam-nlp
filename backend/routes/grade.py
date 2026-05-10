import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.db import get_connection
from services.grading_service import grade as run_grade
from services.ocr_service import parse_question_answer_heuristic
from services.semantic_service import similarity_breakdown

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
    try:
        return _grade_exam_impl(req)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Grade failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


def _grade_exam_impl(req: GradeRequest):
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
    semantic_avg = None
    lexical_avg = None
    per_question = []

    if key_qa and stu_qa and len(key_qa) == len(stu_qa):
        sem_scores: list[float] = []
        lex_scores: list[float] = []
        for k, s in zip(key_qa, stu_qa):
            _, sem, lex = similarity_breakdown(k.get("answer", ""), s.get("answer", ""))
            sem_scores.append(sem)
            lex_scores.append(lex)
            per_question.append(
                {
                    "question_id": s.get("question_id", k.get("question_id")),
                    "similarity_percent": round((sem + lex) / 2, 2),
                }
            )
        n = len(sem_scores)
        semantic_avg = round(sum(sem_scores) / n, 2) if n else 0.0
        lexical_avg = round(sum(lex_scores) / n, 2) if n else 0.0
        similarity = round((semantic_avg + lexical_avg) / 2, 2) if n else 0.0
    elif key_qa and stu_qa:
        # Different counts: fall back to whole-document similarity
        similarity, semantic_avg, lexical_avg = similarity_breakdown(key_text, student_text)
        per_question = []
    else:
        similarity, semantic_avg, lexical_avg = similarity_breakdown(key_text, student_text)

    result = run_grade(semantic_avg, lexical_avg, req.max_score)

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO grades (
                extraction_id, answer_key_text, similarity_percent,
                semantic_percent, lexical_percent,
                final_score, max_score, feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                req.extraction_id,
                key_text[:50000],
                result.similarity_percent,
                semantic_avg,
                lexical_avg,
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
