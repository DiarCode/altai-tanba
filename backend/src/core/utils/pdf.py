from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF

from modules.mark_service.types import PageImage


def compute_doc_hash(pdf_path: Path) -> str:
    h = hashlib.sha256()
    with pdf_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


essential_pages_subdir = "pages"


def pdf_to_images(pdf_path: Path, work_dir: Path) -> Tuple[str, List[PageImage]]:
    """
    Convert PDF to PNG pages using PyMuPDF and return (doc_hash, pages).
    Creates work_dir/<doc_hash>/original.pdf and pages/*.png
    """
    pdf_path = pdf_path.resolve()
    doc_hash = compute_doc_hash(pdf_path)

    doc_dir = work_dir / doc_hash
    pages_dir = doc_dir / essential_pages_subdir
    pages_dir.mkdir(parents=True, exist_ok=True)

    # copy original
    original_copy = doc_dir / "original.pdf"
    if original_copy != pdf_path:
        original_copy.write_bytes(pdf_path.read_bytes())

    page_images: List[PageImage] = []

    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=300)
            out_path = pages_dir / f"page_{i}.png"
            pix.save(str(out_path))
            page_images.append(PageImage(index=i, path=out_path, width=pix.width, height=pix.height))
    finally:
        doc.close()

    return doc_hash, page_images
