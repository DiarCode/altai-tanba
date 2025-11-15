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
        try:
            payload = LabelsPositionPayload.model_validate(doc.labelsPosition)
            artifacts_url = payload.artifacts.originalPdfUrl
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
