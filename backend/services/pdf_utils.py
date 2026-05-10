"""Render PDF pages to PNG for OCR pipeline."""
from __future__ import annotations

import logging
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)


def pdf_first_page_to_png(pdf_path: Path, out_dir: Path) -> Path:
    pdf_path = Path(pdf_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    try:
        if doc.page_count < 1:
            raise ValueError("PDF has no pages")
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        out = out_dir / f"{pdf_path.stem}_page1.png"
        pix.save(str(out))
        logger.info("Rendered PDF page 1 to %s", out)
        return out
    finally:
        doc.close()
