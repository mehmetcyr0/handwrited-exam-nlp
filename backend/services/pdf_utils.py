"""Render PDF pages to PNG for OCR pipeline."""
from __future__ import annotations

import logging
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)


def pdf_first_page_to_png(pdf_path: Path, out_dir: Path) -> Path:
    pdf_path = Path(pdf_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Bellekten aç: Windows’ta Unicode dosya yolu fitz.open(str) ile sorun çıkarabiliyor
    raw = pdf_path.read_bytes()
    doc = fitz.open(stream=raw, filetype="pdf")
    try:
        if doc.page_count < 1:
            raise ValueError("PDF has no pages")
        page = doc.load_page(0)
        # Daha yüksek çözünürlük: ince el yazısı / OCR için (eskisi 2x)
        pix = page.get_pixmap(matrix=fitz.Matrix(3.5, 3.5))
        out = out_dir / f"{pdf_path.stem}_page1.png"
        # write_bytes: Unicode yol güvenli (pix.save(str) Windows'ta sorun çıkarabilir)
        out.write_bytes(pix.tobytes("png"))
        logger.info("Rendered PDF page 1 to %s", out)
        return out
    finally:
        doc.close()
