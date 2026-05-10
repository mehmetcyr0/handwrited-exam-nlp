"""
Benzerlik yüzdelerinden not ve geri bildirim.
Birleşik benzerlik = (anlamsal + kelime) / 2.
Alınan not = anlamsal ve kelime için ayrı ayrı eğri uygulanıp ortalaması (eşit katkı).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GradeResult:
    similarity_percent: float
    final_score: float
    max_score: float
    feedback: str


def _lerp(s: float, s0: float, r0: float, s1: float, r1: float) -> float:
    """s in [s0,s1] aralığında r0→r1 doğrusal."""
    if s1 == s0:
        return r0
    t = (s - s0) / (s1 - s0)
    return r0 + t * (r1 - r0)


def similarity_to_score(similarity_percent: float, max_score: float = 100.0) -> float:
    """
    Tek bir benzerlik yüzdesi → maksimuma oran (parça doğrusu).
    Köşe: %80→tam puan, %60→%80, %40→%50, %20→%20; %0–20 doğrusal.
    """
    if not math.isfinite(float(similarity_percent)):
        similarity_percent = 0.0
    s = max(0.0, min(100.0, float(similarity_percent)))

    if s >= 80:
        ratio = 1.0
    elif s >= 60:
        ratio = _lerp(s, 60, 0.8, 80, 1.0)
    elif s >= 40:
        ratio = _lerp(s, 40, 0.5, 60, 0.8)
    elif s >= 20:
        ratio = _lerp(s, 20, 0.2, 40, 0.5)
    else:
        ratio = _lerp(s, 0, 0.0, 20, 0.2)

    ratio = max(0.0, min(1.0, ratio))
    return round(ratio * max_score, 2)


def build_feedback(similarity_percent: float, final_score: float, max_score: float) -> str:
    s = similarity_percent
    parts = [
        f"Birleşik benzerlik: %{s:.1f}.",
        f"Not (maks {max_score:.0f}): {final_score:.1f}.",
    ]
    if s >= 80:
        parts.append("Güçlü uyum; bu benzerlik bandında tam puan (veya üstü) uygulanır.")
    elif s >= 60:
        parts.append("İyi düzey: ana fikirler ve terimler çoğunlukla örtüşüyor.")
    elif s >= 40:
        parts.append("Orta düzey: kısmen doğru; bazı kavramlar eksik veya farklı yapıda.")
    elif s >= 20:
        parts.append("Düşük–orta: örtüşme sınırlı; tekrar gözden geçirme faydalı olur.")
    else:
        parts.append("Çok düşük uyum; cevap anahtarıyla örtüşme zayıf.")
    return " ".join(parts)


def grade(
    semantic_percent: float,
    lexical_percent: float,
    max_score: float = 100.0,
) -> GradeResult:
    """
    Anlamsal ve kelime yüzdeleri eşit ağırlıkla nota dönüşür:
    - Gösterilen birleşik benzerlik = (anlamsal + kelime) / 2
    - Not = (eğri(anlamsal) + eğri(kelime)) / 2
    """
    sem = float(semantic_percent)
    lex = float(lexical_percent)
    if not math.isfinite(sem):
        sem = 0.0
    if not math.isfinite(lex):
        lex = 0.0
    sem = max(0.0, min(100.0, sem))
    lex = max(0.0, min(100.0, lex))

    combined = round((sem + lex) / 2, 2)
    part_sem = similarity_to_score(sem, max_score)
    part_lex = similarity_to_score(lex, max_score)
    final = round((part_sem + part_lex) / 2, 2)

    fb = build_feedback(combined, final, max_score)
    logger.info("Graded: sem=%.2f lex=%.2f combined=%.2f score=%.2f/%s", sem, lex, combined, final, max_score)
    return GradeResult(
        similarity_percent=combined,
        final_score=final,
        max_score=max_score,
        feedback=fb,
    )
