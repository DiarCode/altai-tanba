from __future__ import annotations

import uuid
from pathlib import Path
import shutil
import os
from typing import Dict, List

from prisma import Prisma, Json

from src.core.s3.s3_service import s3_service
from src.core.config.settings import settings
from src.modules.mark_service.services.document_processor import DigitalInspectorProcessor
from src.modules.mark_service.utils import build_labeled_pdf, draw_boxes_on_page, yolo_results_to_detections
from src.modules.mark_service.formatters import build_challenge_json
from src.core.utils.pdf import pdf_to_images
from src.modules.sessions.labels_payload import DetectionOut, PageArtifacts
from src.modules.document_analysis.document_analysis_service import document_analysis_service





async def process_document_async(session_id: int, document_id: int, file_path: Path, work_root: Path) -> None:
    """
    Background task: process a single PDF, upload artifacts to S3, store JSONB payload
    and detections summary into DB, and finalize status.
    """
    db = Prisma()
    await db.connect()
    def _safe_remove(path: Path) -> None:
        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            elif path.is_file():
                path.unlink(missing_ok=True)  # py>=3.8
        except Exception as _e:
            print(f"[CLEANUP] Failed to remove {path}: {_e}")

    try:
        s3 = s3_service
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

        # 4) Trigger document analysis with unified key (numeric document id)
        try:
            await document_analysis_service.analyze_document(document_id)
        except Exception as _e:
            # Non-fatal for labels pipeline; analysis status is tracked separately
            print(f"[ANALYSIS] Document {document_id} analysis failed: {_e}")

        # 5) Inference
        page_dets_raw = processor.run_inference_on_pages(pages, conf_thres=0.25)
        # Convert to DetectionOut (camelCase) for local flags only
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

        # Build expected challenge JSON
        doc_record = await db.sessiondocument.find_unique(where={"id": document_id})
        pdf_name = doc_record.originalName if doc_record and doc_record.originalName else file_path.name

        def _safe_graphql_key(name: str) -> str:
            # GraphQL input object fields must match /^[_A-Za-z][_0-9A-Za-z]*$/
            import re, uuid as _uuid
            key = re.sub(r"[^0-9A-Za-z_]", "_", name)
            if not key or not (key[0].isalpha() or key[0] == "_"):
                key = f"k_{key}" if key else f"k_{_uuid.uuid4().hex}"
            return key

        safe_key = _safe_graphql_key(pdf_name)
        challenge_json = build_challenge_json(safe_key, pages, page_dets_raw)
        # Preserve original filename and embed artifacts (URLs) inside payload
        if safe_key in challenge_json and isinstance(challenge_json[safe_key], dict):
            challenge_json[safe_key]["original_name"] = pdf_name
            challenge_json[safe_key]["artifacts"] = {
                "originalPdfUrl": original_url,
                "labeledPdfUrl": labeled_pdf_url,
                "pages": [
                    {
                        "pageIndex": p.pageIndex,
                        "imageUrl": p.imageUrl,
                        "labeledImageUrl": p.labeledImageUrl,
                    }
                    for p in labeled_pages
                ],
            }

        # 7) Persist to DB
        await db.sessiondocument.update(
            where={"id": document_id},
            data={
                # Use Prisma Json wrapper to ensure proper GraphQL Json handling
                "labelsPosition": Json(challenge_json),
                "hasSignature": has_signature,
                "hasQR": has_qr,
                "hasStamp": has_stamp,
                "status": "SUCCESSFUL",
            },
        )

        # 8) Cleanup working artifacts (pages, labeled pdf, original copy) & temp upload
        _safe_remove(doc_dir)
        _safe_remove(file_path)

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
        # Cleanup even on failure (artifacts already useless); remove only temp upload dir & pages
        try:
            _safe_remove(doc_dir)
            _safe_remove(file_path)
        except Exception:
            pass
    finally:
        await db.disconnect()
