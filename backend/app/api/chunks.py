from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.chunking import chunk_pages
from app.services.parsing import load_extracted_pages

router = APIRouter(tags=["chunks"])


@router.get("/uploads/{upload_id}/chunks")
def get_chunks(upload_id: str, max_tokens: int = 700, overlap_tokens: int = 120):
    try:
        pages = load_extracted_pages(settings.storage_dir, upload_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="upload_id not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    chunks = chunk_pages(
        upload_id=upload_id,
        pages=pages,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        meta={"source": "pdf"},
    )

    return {
        "upload_id": upload_id,
        "chunk_count": len(chunks),
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "token_count": c.token_count,
                "text_preview": c.text[:220],
            }
            for c in chunks
        ],
    }
