from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.core.config import settings

router = APIRouter(tags=["upload"])


def ensure_upload_dir() -> Path:
    p = Path(settings.upload_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.post("/upload")
async def upload_report(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF files are supported")

    upload_id = str(uuid.uuid4())
    out_path = ensure_upload_dir() / f"{upload_id}.pdf"

    data = await file.read()
    out_path.write_bytes(data)

    return {"upload_id": upload_id, "saved_as": str(out_path)}
