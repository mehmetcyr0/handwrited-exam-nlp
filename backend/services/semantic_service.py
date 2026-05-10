"""
Anlamsal benzerlik: önce sentence-transformers (+ PyTorch), yoksa TF-IDF (torch kurulamazsa).
Puanlama için ayrıca kelime kümesi (Jaccard + anahtar kelime geri çağırma) ile birleştirilir.
"""
from __future__ import annotations

import logging
import math
import re
from difflib import SequenceMatcher
from typing import Sequence

import numpy as np

from services.turkish_ocr_repair import normalize_for_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Birleşik gösterim: anlamsal ve kelime eşit ağırlık (aritmetik ortalama)
_SEMANTIC_BLEND_WEIGHT = 0.5
_LEXICAL_BLEND_WEIGHT = 0.5

# Çok sık geçen bağlaçlar / zamirler (kelime skorunda gürültüyü azaltır)
_TR_STOPWORDS = frozenset(
    {
        "ve",
        "veya",
        "bir",
        "bu",
        "şu",
        "su",
        "o",
        "ile",
        "için",
        "icin",
        "da",
        "de",
        "daha",
        "mi",
        "mı",
        "mu",
        "mü",
        "ne",
        "gibi",
        "kadar",
        "olan",
        "olarak",
        "en",
        "çok",
        "cok",
        "az",
        "her",
        "hiç",
        "hic",
        "the",
        "a",
        "an",
        "is",
        "are",
        "of",
        "to",
        "in",
    }
)

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None
_use_tfidf_only: bool = False


def _get_sentence_model():
    """SentenceTransformer veya None (torch / paket yoksa)."""
    global _model, _use_tfidf_only
    if _use_tfidf_only:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(MODEL_NAME)
            logger.info("sentence-transformers model: %s", MODEL_NAME)
        except (OSError, ImportError, RuntimeError) as e:
            _use_tfidf_only = True
            _model = None
            logger.warning(
                "PyTorch / sentence-transformers acilamadi (ornek: WinError 127, shm.dll). "
                "Puanlama TF-IDF kosinus ile surer; kalite dusuk olabilir. Ayrinti: %s",
                e,
            )
    return _model


def _similarity_tfidf_pair(ref: str, cand: str) -> float:
    """Iki metin arasinda TF-IDF + kosinus (torch gerekmez)."""
    try:
        vec = TfidfVectorizer(min_df=1, lowercase=True)
        mat = vec.fit_transform([ref, cand])
        if mat.shape[1] == 0:
            return 0.0
        sim = cosine_similarity(mat[0:1], mat[1:2])[0][0]
        sim = float(sim)
    except (ValueError, TypeError):
        return 0.0
    if not math.isfinite(sim):
        sim = 0.0
    sim = max(0.0, min(1.0, sim))
    return round(sim * 100.0, 2)


def _word_tokens(text: str) -> set[str]:
    """Unicode kelimeler; kısa ve stop kelimeler elenir."""
    raw = re.findall(r"[\w]+", (text or "").lower(), flags=re.UNICODE)
    return {w for w in raw if len(w) >= 2 and w not in _TR_STOPWORDS}


def _fuzzy_token_in_candidate(token: str, cand_tokens: set[str]) -> bool:
    """OCR kaynaklı tek harf farklarını (fotosenter/fotosentez) kabaca tolere eder."""
    if token in cand_tokens:
        return True
    if len(token) < 3:
        return False
    max_delta = max(2, len(token) // 3)
    for c in cand_tokens:
        if len(c) < 2:
            continue
        if abs(len(token) - len(c)) > max_delta:
            continue
        if SequenceMatcher(None, token, c).ratio() >= 0.87:
            return True
    return False


def lexical_similarity_percentage(reference: str, candidate: str) -> float:
    """
    Kelime benzerliği (0–100): Jaccard + anahtar kelime geri çağırma (tam + hafif fuzzy).
    """
    ref = (reference or "").strip()
    cand = (candidate or "").strip()
    if not ref or not cand:
        return 0.0

    a = _word_tokens(ref)
    b = _word_tokens(cand)
    if not a and not b:
        return 100.0
    if not a or not b:
        return 0.0

    inter = a & b
    union = a | b
    jacc = len(inter) / len(union) if union else 0.0
    matched_fuzzy = sum(1 for t in a if _fuzzy_token_in_candidate(t, b))
    recall = matched_fuzzy / len(a) if a else 0.0
    score = 0.38 * jacc + 0.62 * recall
    pct = round(100.0 * max(0.0, min(1.0, score)), 2)
    return pct


def embed_texts(texts: Sequence[str]) -> np.ndarray:
    """Yalnizca transformer yukluyse; aksi halde RuntimeError."""
    model = _get_sentence_model()
    if model is None:
        raise RuntimeError("sentence-transformers kullanilamiyor; embed_texts devre disi")
    cleaned = [t.strip() if t else "" for t in texts]
    return np.asarray(model.encode(cleaned, convert_to_numpy=True, show_progress_bar=False))


def _semantic_similarity_percentage(reference: str, candidate: str) -> float:
    """Yalnızca vektör / TF-IDF anlamsal benzerlik (0–100)."""
    ref = (reference or "").strip()
    cand = (candidate or "").strip()
    if not ref or not cand:
        return 0.0

    model = _get_sentence_model()
    if model is not None:
        emb = np.asarray(
            model.encode([ref, cand], convert_to_numpy=True, show_progress_bar=False)
        )
        sim = cosine_similarity(emb[0:1], emb[1:2])[0][0]
        sim = float(sim)
        if not math.isfinite(sim):
            sim = 0.0
        sim = max(0.0, min(1.0, sim))
        return round(sim * 100.0, 2)

    return _similarity_tfidf_pair(ref, cand)


def similarity_breakdown(reference: str, candidate: str) -> tuple[float, float, float]:
    """
    (birleşik_yüzde, anlamsal_yüzde, kelime_yüzde).
    birleşik = (anlamsal + kelime) / 2. (İç puanlama için sem/lex ayrı kullanılır.)
    """
    ref = (reference or "").strip()
    cand_raw = (candidate or "").strip()
    if not ref or not cand_raw:
        return 0.0, 0.0, 0.0

    ref_c = ref.casefold()
    cand_c = normalize_for_similarity(cand_raw)

    sem = _semantic_similarity_percentage(ref_c, cand_c)
    lex = lexical_similarity_percentage(ref_c, cand_c)
    combined = (
        _SEMANTIC_BLEND_WEIGHT * sem
        + _LEXICAL_BLEND_WEIGHT * lex
    )
    combined = round(max(0.0, min(100.0, combined)), 2)
    return combined, sem, lex


def similarity_percentage(reference: str, candidate: str) -> float:
    """
    Puanlama için birleşik benzerlik (0–100): anlamsal + kelime örtüşmesi.
    Geriye dönük uyumluluk: tek skor döner; ayrıntı için similarity_breakdown.
    """
    c, _, _ = similarity_breakdown(reference, candidate)
    return c


def average_similarity(reference_blocks: Sequence[str], candidate_blocks: Sequence[str]) -> float:
    """Indeks bazli eslestirme; ortalama benzerlik."""
    if not reference_blocks or not candidate_blocks:
        return similarity_percentage(" ".join(reference_blocks), " ".join(candidate_blocks))

    n = min(len(reference_blocks), len(candidate_blocks))
    scores = [similarity_percentage(reference_blocks[i], candidate_blocks[i]) for i in range(n)]
    return round(sum(scores) / max(len(scores), 1), 2)
