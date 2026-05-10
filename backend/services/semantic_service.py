"""
Semantic similarity with sentence-transformers (all-MiniLM-L6-v2).
"""
from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Loaded sentence-transformers model: %s", MODEL_NAME)
    return _model


def embed_texts(texts: Sequence[str]) -> np.ndarray:
    model = _get_model()
    cleaned = [t.strip() if t else "" for t in texts]
    return np.asarray(model.encode(cleaned, convert_to_numpy=True, show_progress_bar=False))


def similarity_percentage(reference: str, candidate: str) -> float:
    """
    Cosine similarity between two texts, returned as 0-100 percentage.
    Empty reference or candidate yields 0.
    """
    ref = (reference or "").strip()
    cand = (candidate or "").strip()
    if not ref or not cand:
        return 0.0

    emb = embed_texts([ref, cand])
    sim = cosine_similarity(emb[0:1], emb[1:2])[0][0]
    # Clamp to [0, 1] in case of numerical drift
    sim = float(max(0.0, min(1.0, sim)))
    return round(sim * 100.0, 2)


def average_similarity(reference_blocks: Sequence[str], candidate_blocks: Sequence[str]) -> float:
    """Pairwise alignment by index; averages similarities for available pairs."""
    if not reference_blocks or not candidate_blocks:
        return similarity_percentage(" ".join(reference_blocks), " ".join(candidate_blocks))

    n = min(len(reference_blocks), len(candidate_blocks))
    scores = [similarity_percentage(reference_blocks[i], candidate_blocks[i]) for i in range(n)]
    return round(sum(scores) / max(len(scores), 1), 2)
