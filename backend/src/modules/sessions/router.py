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
    db = Prisma()
    await db.connect()
    try:
        where = {"status": status} if status else None
        sessions = await db.session.find_many(
            where=where,
            order={"createdAt": "desc"},
        )
        return [map_session_to_dto(s) for s in sessions]
    finally:
        await db.disconnect()


@router.get("/{session_id}", response_model=SessionDTO)
async def get_session(
    session_id: int,
    db: Prisma = Depends(get_db)
    ) -> SessionDTO:
    try:
        s = await db.session.find_unique(where={"id": session_id})
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")
        return map_session_to_dto(s)
    finally:
        await db.disconnect()


@router.get("/{session_id}/documents", response_model=List[SessionDocumentDTO])
async def list_session_documents(
    session_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: SessionDocumentStatus | None = Query(None),
    db: Prisma = Depends(get_db),
) -> List[SessionDocumentDTO]:

    try:
        where = {"sessionId": session_id}
        if status:
            where["status"] = status.value
        docs = await db.sessiondocument.find_many(
            where=where, order={"createdAt": "desc"}, skip=(page - 1) * size, take=size
        )
        return [map_document_to_dto(d) for d in docs]
    finally:
        await db.disconnect()


@router.get("/{session_id}/documents/{doc_id}", response_model=SessionDocumentDetailsDto)
async def get_session_document(
    session_id: int,
    doc_id: int,    
    db: Prisma = Depends(get_db),
) -> SessionDocumentDetailsDto:
    try:
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
    finally:
        await db.disconnect()


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

    try:
        s = await db.session.find_unique(where={"id": session_id})
        return map_session_to_dto(s)
    finally:
        await db.disconnect()
