from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, List

from prisma import Prisma

from src.core.s3 import S3Client, MockS3Client
from src.core.config.settings import settings
from src.modules.mark_service.services.document_processor import DigitalInspectorProcessor
from src.modules.mark_service.utils import build_labeled_pdf, draw_boxes_on_page, yolo_results_to_detections
from src.core.utils.pdf import pdf_to_images
from src.modules.sessions.labels_payload import DetectionOut, DocumentArtifacts, LabelsPositionPayload, PageArtifacts
from src.modules.text_service.client import trigger_document_ocr


def _make_s3() -> S3Client | MockS3Client:
    return MockS3Client() if settings.USE_STUB_ADAPTER else S3Client()


async def process_document_async(session_id: int, document_id: int, file_path: Path, work_root: Path) -> None:
    """
    Background task: process a single PDF, upload artifacts to S3, store JSONB payload
    and detections summary into DB, and finalize status.
    """
    db = Prisma()
    await db.connect()
    try:
        s3 = _make_s3()
        processor = DigitalInspectorProcessor(s3_client=s3)

        # 1) PDF → images
        doc_hash, pages = pdf_to_images(file_path, work_root)
        doc_dir = work_root / doc_hash
        original_pdf_path = doc_dir / "original.pdf"

        # 2) Upload original
        original_key = f"sessions/{session_id}/documents/{document_id}/original.pdf"
        original_url = s3.upload_file(str(original_pdf_path), original_key)

        # 3) Upload pages
        page_urls: Dict[int, str] = {}
        for p in pages:
            key = f"sessions/{session_id}/documents/{document_id}/pages/page_{p.index}.png"
            url = s3.upload_file(str(p.path), key)
            page_urls[p.index] = url

        # 4) Trigger text service stub
        trigger_document_ocr(document_id, [page_urls[i] for i in sorted(page_urls)])

        # 5) Inference
        page_dets_raw = processor.run_inference_on_pages(pages, conf_thres=0.25)
        # Convert to DetectionOut (camelCase)
        page_dets: Dict[int, List[DetectionOut]] = {}
        has_qr = has_stamp = has_signature = False
        for idx, dets in page_dets_raw.items():
            out_list: List[DetectionOut] = []
            for d in dets:
                if d.category == "qr":
                    has_qr = True
                elif d.category == "stamp":
                    has_stamp = True
                elif d.category == "signature":
                    has_signature = True
                out_list.append(
                    DetectionOut(
                        category=d.category,
                        x=d.x,
                        y=d.y,
                        width=d.w,
                        height=d.h,
                        area=d.area,
                        confidence=d.confidence,
                    )
                )
            page_dets[idx] = out_list

        # 6) Labeled images and PDF
        labeled_pages: List[PageArtifacts] = []
        for p in pages:
            labeled_path = draw_boxes_on_page(p, page_dets_raw.get(p.index, []))
            key = f"sessions/{session_id}/documents/{document_id}/labeled/page_{p.index}.png"
            labeled_url = s3.upload_file(str(labeled_path), key)
            labeled_pages.append(PageArtifacts(pageIndex=p.index, imageUrl=page_urls[p.index], labeledImageUrl=labeled_url))

        labeled_pdf_path = build_labeled_pdf(doc_dir, pages, page_dets_raw)
        labeled_pdf_key = f"sessions/{session_id}/documents/{document_id}/labeled/labeled.pdf"
        labeled_pdf_url = s3.upload_file(str(labeled_pdf_path), labeled_pdf_key)

        payload = LabelsPositionPayload(
            artifacts=DocumentArtifacts(
                originalPdfUrl=original_url,
                labeledPdfUrl=labeled_pdf_url,
                pages=labeled_pages,
            ),
            detections=page_dets,
        )

        # 7) Persist to DB
        await db.sessiondocument.update(
            where={"id": document_id},
            data={
                "labelsPosition": payload.model_dump(),
                "hasSignature": has_signature,
                "hasQR": has_qr,
                "hasStamp": has_stamp,
                "status": "SUCCESSFUL",
            },
        )

        # Mark session SUCCESS if all documents are SUCCESSFUL
        total_docs = await db.sessiondocument.count(where={"sessionId": session_id})
        successful_docs = await db.sessiondocument.count(
            where={"sessionId": session_id, "status": "SUCCESSFUL"}
        )
        if total_docs > 0 and successful_docs == total_docs:
            await db.session.update(
                where={"id": session_id},
                data={"status": "SUCCESS"},
            )
    except Exception as e:
        # Mark document failed
        try:
            await db.sessiondocument.update(
                where={"id": document_id},
                data={"status": "FAILED"},
            )
            # If no documents remain in PENDING, but some FAILED, leave session as is
        except Exception:
            pass
        print(f"[PROCESSOR] Document {document_id} failed: {e}")
    finally:
        await db.disconnect()
