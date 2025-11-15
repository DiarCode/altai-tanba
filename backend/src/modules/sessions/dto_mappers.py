from __future__ import annotations

from typing import List

from src.modules.sessions.types import (
    SessionDTO,
    SessionDocumentDTO,
    SessionDocumentStatus,
)
from src.modules.sessions.labels_payload import LabelsPositionPayload


def map_session_to_dto(session) -> SessionDTO:
    return SessionDTO(
        id=str(session.id),
        total_documents=session.documentsCount,
        created_at=session.createdAt,
        updated_at=session.updatedAt,
    )


def map_document_to_dto(doc) -> SessionDocumentDTO:
    # Resolve documentUrl from labelsPosition if available
    artifacts_url = None
    if doc.labelsPosition:
        # Try legacy payload first
        try:
            payload = LabelsPositionPayload.model_validate(doc.labelsPosition)
            artifacts_url = payload.artifacts.originalPdfUrl
        except Exception:
            # Fallback to challenge JSON shape with embedded artifacts
            lp = doc.labelsPosition
            try:
                if isinstance(lp, dict):
                    # Direct artifacts on root
                    if "artifacts" in lp and isinstance(lp["artifacts"], dict):
                        artifacts_url = lp["artifacts"].get("originalPdfUrl")
                    else:
                        # Nested under safe key
                        first_val = next(iter(lp.values())) if lp else None
                        if isinstance(first_val, dict) and "artifacts" in first_val:
                            art = first_val["artifacts"]
                            if isinstance(art, dict):
                                artifacts_url = art.get("originalPdfUrl")
            except Exception:
                artifacts_url = None

    return SessionDocumentDTO(
        id=str(doc.id),
        document_url=artifacts_url or doc.documentId,
        original_name=doc.originalName,
        status=SessionDocumentStatus(doc.status),
        created_at=doc.createdAt,
        updated_at=doc.updatedAt,
        verification={
            "hasQR": bool(doc.hasQR),
            "hasStamp": bool(doc.hasStamp),
            "hasSignature": bool(doc.hasSignature),
        },
    )
