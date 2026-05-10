"""
Türkçe el yazısı / Latin OCR sonrası düzeltmeler (Paddle/EasyOCR/RapidOCR ortak).
"""
from __future__ import annotations

import re

# Sık yanlış tanınan tam kelimeler
_TR_LEXICON: dict[str, str] = {
    "gunes": "güneş",
    "günes": "güneş",
    "gönes": "güneş",
    "g8nes": "güneş",
    "g0nes": "güneş",
    "goenes": "güneş",
    "gunesten": "güneşten",
    "guneste": "güneşte",
    "isigi": "ışığı",
    "isigini": "ışığını",
    "isik": "ışık",
    "isiktan": "ışıktan",
    "isikta": "ışıkta",
    "fotosentex": "fotosentez",
    "fotosentet": "fotosentez",
    "fotosentetz": "fotosentez",
    "fotosentesi": "fotosentez",
    "fotosenter": "fotosentez",
    "fotosenters": "fotosentez",
    "fotocentez": "fotosentez",
    "karbondioksid": "karbondioksit",
    "karbondioksidten": "karbondioksitten",
    "karbondioksitden": "karbondioksitten",
    "kerbondi": "karbondi",
    "kerbondioksit": "karbondioksit",
    "kerbondioksitten": "karbondioksitten",
    "kulanarak": "kullanarak",
    "kulanilir": "kullanılır",
    "luileerek": "kullanarak",
    "lullenerek": "kullanarak",
    "besi": "besin",
    "uretir": "üretir",
    "uretilir": "üretilir",
    "uretim": "üretim",
    "hucresel": "hücresel",
    "hucresi": "hücresi",
    "hucresinin": "hücresinin",
    "enerji": "enerji",
    "mitokondri": "mitokondri",
    "kloroplast": "kloroplast",
    "glukoz": "glukoz",
    "oksijen": "oksijen",
    "azot": "azot",
    "dna": "DNA",
    "rna": "RNA",
}

# Bölünmüş bileşik kelimeler (OCR boşluk ekler)
_COMPOUND_FIXES: tuple[tuple[str, str], ...] = (
    (r"\bkarbondi\s+oksitten\b", "karbondioksitten"),
    (r"\bkarbondi\s+oksit\b", "karbondioksit"),
    (r"\bkerbondi\s+oksitten\b", "karbondioksitten"),
    (r"\bkerbondi\s+oksit\b", "karbondioksit"),
    (r"\bfoto\s+sentez\b", "fotosentez"),
    (r"\bfoto\s+sentet\b", "fotosentez"),
    (r"\bfoto\s+sentezi\b", "fotosentez"),
)


def _collapse_consecutive_duplicate_words(text: str) -> str:
    """Ardışık aynı kelimeyi teke indir (ve ve, denir denir)."""
    parts = text.split()
    if not parts:
        return text
    out: list[str] = [parts[0]]
    for w in parts[1:]:
        if w.lower() == out[-1].lower():
            continue
        out.append(w)
    return " ".join(out)


def _strip_ocr_junk_chars(text: str) -> str:
    """Tek başına kalan gürültü karakterleri kaldır."""
    t = text
    t = re.sub(r"\s*\^\s*", " ", t)
    t = re.sub(r"(?<=[a-zçğıöşüA-ZÇĞİÖŞÜ0-9])\s*\d+\$\s*(?=[a-zçğıöşüA-ZÇĞİÖŞÜ0-9])", " ", t)
    t = re.sub(r"\b\d+\$\b", " ", t)
    return t


def _fix_duplicate_sentence_endings(text: str) -> str:
    """Örn. 'denir. derir.' veya 'fotosentez denir. derir.'"""
    t = text
    t = re.sub(
        r"\b(denir|derir|denır|derır)\.\s*(denir|derir|denır|derır)\.",
        r"\1.",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(fotosentez|fotosenter)\s+(denir|derir)\.\s*(denir|derir)\.",
        r"fotosentez \2.",
        t,
        flags=re.IGNORECASE,
    )
    return t


def repair_turkish_handwriting_text(text: str) -> str:
    if not text:
        return text
    t = text

    t = _strip_ocr_junk_chars(t)

    for pat, rep in _COMPOUND_FIXES:
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)

    t = re.sub(r"\$\s*1\$?\s*igini\b", "ışığını", t, flags=re.IGNORECASE)
    t = re.sub(r"\b1\$igini\b", "ışığını", t, flags=re.IGNORECASE)
    t = re.sub(r"\$\s*1\$?\s*igi\b", "ışığı", t, flags=re.IGNORECASE)
    t = re.sub(r"\b1\$ig\b", "ışığ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgüneş\s+1\$\s*güneş\b", "güneş", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgüneş\s+1\$\s*g8nes\b", "güneş", t, flags=re.IGNORECASE)

    for wrong, right in _TR_LEXICON.items():
        t = re.sub(rf"\b{re.escape(wrong)}\b", right, t, flags=re.IGNORECASE)

    t = _fix_duplicate_sentence_endings(t)
    t = _collapse_consecutive_duplicate_words(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_extracted_student_text(text: str) -> str:
    """
    OCR çıktısı için tam boru hattı: tamir + tekrar temizliği (veritabanına yazılmadan önce).
    """
    if not text:
        return text
    t = repair_turkish_handwriting_text(text)
    t = repair_turkish_handwriting_text(t)
    return t


def normalize_for_similarity(candidate: str) -> str:
    """Puanlama öncesi: OCR tamiri + küçük harf (anahtar ile hizalı karşılaştırma)."""
    return normalize_extracted_student_text(candidate or "").casefold().strip()
