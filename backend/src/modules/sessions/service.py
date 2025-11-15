from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import List, Tuple

from fastapi import BackgroundTasks, HTTPException, UploadFile

from src.modules.sessions.processors import process_document_async
from src.core.db.prisma import get_db


def _collect_pdfs_from_zip(data: bytes) -> List[Tuple[str, bytes]]:
    out: List[Tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.lower().endswith(".pdf"):
                out.append((Path(name).name, zf.read(name)))
    return out


async def create_session_with_documents(files: List[UploadFile], background: BackgroundTasks, work_root: Path) -> int:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    pdf_blobs: List[Tuple[str, bytes]] = []
    for f in files:
        data = await f.read()
        if f.filename and f.filename.lower().endswith(".zip"):
            pdf_blobs.extend(_collect_pdfs_from_zip(data))
        elif f.filename and f.filename.lower().endswith(".pdf"):
            pdf_blobs.append((Path(f.filename).name, data))
        else:
            # skip non-pdf
            continue

    if not pdf_blobs:
        raise HTTPException(status_code=400, detail="No PDFs found in upload")

    db = await get_db()
    session = await db.session.create(
        data={
            "documentsCount": len(pdf_blobs),
            "status": "PROCESSING",
        }
    )

    # Create docs and schedule background processing
    for original_name, blob in pdf_blobs:
        doc = await db.sessiondocument.create(
            data={
                "originalName": original_name,
                "documentId": original_name,
                "sessionId": session.id,
                "status": "PENDING",
            }
        )

        # write blob to temp file under work_root
        doc_temp_dir = work_root / "uploads" / str(session.id)
        doc_temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = doc_temp_dir / f"{doc.id}.pdf"
        temp_path.write_bytes(blob)

        background.add_task(process_document_async, session.id, doc.id, temp_path, work_root)

    return session.id
