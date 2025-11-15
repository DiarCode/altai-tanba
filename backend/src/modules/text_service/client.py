from __future__ import annotations

from typing import List


def trigger_document_ocr(document_id: int, page_urls: List[str]) -> None:
    """Stub for Text Service integration.
    Called after all page images are uploaded to S3.
    """
    print(f"[TEXT-SERVICE] Trigger OCR for document {document_id} with {len(page_urls)} pages")
