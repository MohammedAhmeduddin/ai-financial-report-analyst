from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.core.config import settings
from app.services.pdf_parser import extract_text_by_page, PDFParseError
from app.services.parsing import save_extracted_pages

router = APIRouter(tags=["extract"])


def upload_path(upload_id: str) -> Path:
    return Path(settings.upload_dir) / f"{upload_id}.pdf"


@router.post("/extract/{upload_id}")
def extract(upload_id: str):
    pdf_path = upload_path(upload_id)

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="upload_id not found")

    try:
        pages = extract_text_by_page(pdf_path)
        if not pages:
            pages = [{"page": 1, "text": ""}]
    except PDFParseError:
        pages = [{"page": 1, "text": ""}]

    out_path = save_extracted_pages(settings.storage_dir, upload_id, pages)

    return {
        "upload_id": upload_id,
        "num_pages": len(pages),
        "extracted_saved_as": str(out_path),
    }
