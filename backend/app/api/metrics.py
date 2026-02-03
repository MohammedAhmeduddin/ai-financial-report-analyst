from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.parsing import load_extracted_pages
from app.services.metrics import extract_basic_metrics
from app.services.metrics_store import save_metrics

router = APIRouter(tags=["metrics"])


@router.post("/metrics/{upload_id}")
def build_metrics(upload_id: str):
    try:
        pages = load_extracted_pages(settings.storage_dir, upload_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="upload_id not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    extracted = extract_basic_metrics(pages)

    payload = {
        "upload_id": upload_id,
        "metrics": extracted["metrics"],
        "evidence": extracted["evidence"],
    }

    out_path = save_metrics(settings.storage_dir, upload_id, payload)

    return {
        "upload_id": upload_id,
        "saved_as": str(out_path),
        "metrics": payload["metrics"],
    }
