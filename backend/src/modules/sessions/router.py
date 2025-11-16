from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, HTTPException, Query
from prisma import Prisma

from src.core.db.prisma import get_db
from src.modules.sessions.dto_mappers import map_document_to_dto, map_session_to_dto
from src.modules.sessions.service import create_session_with_documents
from src.modules.sessions.types import (
    SessionDTO,
    SessionDocumentDTO,
    SessionDocumentDetailsDto,
    SessionDocumentStatus,
)
from src.modules.sessions.labels_payload import LabelsPositionPayload

router = APIRouter(
    prefix="/sessions",    
    tags=["sessions"],      
)


WORK_ROOT = Path.cwd() / "work_dir"


@router.get("", response_model=List[SessionDTO])
async def list_sessions(
    status: str | None = Query(
        None,
        description="Filter by session status: PROCESSING|FAILED|SUCCESS",
    ),
    db: Prisma = Depends(get_db),
) -> List[SessionDTO]:
    where = {"status": status} if status else None
    sessions = await db.session.find_many(
        where=where,
        order={"createdAt": "desc"},
    )
    return [map_session_to_dto(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionDTO)
async def get_session(
    session_id: int,
    db: Prisma = Depends(get_db)
    ) -> SessionDTO:
    s = await db.session.find_unique(where={"id": session_id})
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return map_session_to_dto(s)


@router.get("/{session_id}/documents", response_model=List[SessionDocumentDTO])
async def list_session_documents(
    session_id: int,
    status: SessionDocumentStatus | None = Query(None),
    db: Prisma = Depends(get_db),
) -> List[SessionDocumentDTO]:

    where = {"sessionId": session_id}
    if status:
        where["status"] = status.value
    docs = await db.sessiondocument.find_many(
        where=where, order={"createdAt": "desc"}
    )
    return [map_document_to_dto(d) for d in docs]


@router.get("/{session_id}/documents/labels-map")
async def get_session_documents_labels_map(
    session_id: int,
    db: Prisma = Depends(get_db),
):
    """Return a mapping of original file name -> pages -> annotations, page_size.

    Reuses the challenge JSON shape produced by the processing pipeline, but
    normalizes the top-level key to the original file name.
    """
    docs = await db.sessiondocument.find_many(
        where={"sessionId": session_id}, order={"createdAt": "asc"}
    )

    result: dict = {}

    for d in docs:
        lp = d.labelsPosition
        if not lp or not isinstance(lp, dict):
            continue

        def pick_value(obj: dict) -> dict | None:
            # If object already looks like a page-mapping or contains artifacts/original_name, use it
            if any(k.startswith("page_") for k in obj.keys()) or "artifacts" in obj or "original_name" in obj:
                return obj
            # Otherwise, try first nested value
            try:
                first_val = next(iter(obj.values())) if obj else None
                if isinstance(first_val, dict):
                    return first_val
            except Exception:
                return None
            return None

        value = pick_value(lp)
        if not value:
            continue

        # Determine original file name
        name = None
        if isinstance(value, dict):
            name = value.get("original_name")
        if not name:
            name = d.originalName or f"document_{d.id}.pdf"

        # Build pages-only mapping (exclude helper fields)
        pages_obj: dict = {}
        for k, v in value.items():
            if k.startswith("page_") and isinstance(v, dict):
                pages_obj[k] = v

        # Handle duplicate names by suffixing
        out_key = name
        suffix = 1
        while out_key in result:
            suffix += 1
            out_key = f"{name} ({suffix})"

        result[out_key] = pages_obj

    return result


@router.get("/{session_id}/documents/{doc_id}", response_model=SessionDocumentDetailsDto)
async def get_session_document(
    session_id: int,
    doc_id: int,    
    db: Prisma = Depends(get_db),
) -> SessionDocumentDetailsDto:
    d = await db.sessiondocument.find_unique(where={"id": doc_id})
    if not d or d.sessionId != session_id:
        raise HTTPException(status_code=404, detail="Document not found")

    base = map_document_to_dto(d).model_dump(by_alias=True)
    labeled = None
    if d.labelsPosition:
        # Try legacy payload first
        try:
            payload = LabelsPositionPayload.model_validate(d.labelsPosition)
            labeled = payload.artifacts.labeledPdfUrl
        except Exception:
            # Fallback to challenge JSON shape with embedded artifacts
            lp = d.labelsPosition
            try:
                if isinstance(lp, dict):
                    if "artifacts" in lp and isinstance(lp["artifacts"], dict):
                        labeled = lp["artifacts"].get("labeledPdfUrl")
                    else:
                        first_val = next(iter(lp.values())) if lp else None
                        if isinstance(first_val, dict) and "artifacts" in first_val:
                            art = first_val["artifacts"]
                            if isinstance(art, dict):
                                labeled = art.get("labeledPdfUrl")
            except Exception:
                labeled = None
    base["labeledDocumentUrl"] = labeled
    # Expose raw labelsPosition JSON (challenge format or legacy) in DTO
    base["labelsPosition"] = d.labelsPosition if d.labelsPosition else None
    return base


@router.post("", response_model=SessionDTO)
async def create_session(
    background: BackgroundTasks,
    files: List[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
    db: Prisma = Depends(get_db),
) -> SessionDTO:
    # Accept either `files` (multiple) or `file` (single) for Postman friendliness
    incoming: List[UploadFile] = []
    if files:
        incoming.extend(files)
    if file:
        incoming.append(file)
    session_id = await create_session_with_documents(incoming, background, WORK_ROOT)
    # Return session base data

    s = await db.session.find_unique(where={"id": session_id})
    return map_session_to_dto(s)
