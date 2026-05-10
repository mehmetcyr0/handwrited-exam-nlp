"""
Map semantic similarity to scores and human-readable feedback.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GradeResult:
    similarity_percent: float
    final_score: float
    max_score: float
    feedback: str


def similarity_to_score(similarity_percent: float, max_score: float = 100.0) -> float:
    """
    Rubric from spec:
    - 90-100 → full score
    - 70-89 → high partial
    - 50-69 → medium
    - below 50 → low
    We map bands to proportional points within max_score.
    """
    s = max(0.0, min(100.0, float(similarity_percent)))
    if s >= 90:
        ratio = 1.0
    elif s >= 70:
        ratio = 0.85
    elif s >= 50:
        ratio = 0.60
    else:
        ratio = 0.30 * (s / 50.0) if s > 0 else 0.0

    return round(ratio * max_score, 2)


def build_feedback(similarity_percent: float, final_score: float, max_score: float) -> str:
    s = similarity_percent
    parts = [
        f"Anlamsal benzerlik: %{s:.1f}.",
        f"Not (maks {max_score:.0f}): {final_score:.1f}.",
    ]
    if s >= 90:
        parts.append("Cevap anahtarıyla güçlü anlamsal uyum; tam veya tam sayılır puan bandı.")
    elif s >= 70:
        parts.append("Yüksek kısmi puan: ana fikirler büyük ölçüde örtüşüyor; eş anlamlı ifadeler kabul edildi.")
    elif s >= 50:
        parts.append("Orta düzey: kısmen doğru; bazı kavramlar eksik veya farklı yapıda.")
    else:
        parts.append("Düşük uyum: cevap anahtarıyla anlamsal olarak zayıf örtüşüyor; tekrar değerlendirme önerilir.")
    return " ".join(parts)


def grade(similarity_percent: float, max_score: float = 100.0) -> GradeResult:
    final = similarity_to_score(similarity_percent, max_score)
    fb = build_feedback(similarity_percent, final, max_score)
    logger.info("Graded: sim=%.2f score=%.2f/%s", similarity_percent, final, max_score)
    return GradeResult(
        similarity_percent=round(float(similarity_percent), 2),
        final_score=final,
        max_score=max_score,
        feedback=fb,
    )
