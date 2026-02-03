from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.metrics_store import load_metrics
from app.services.variance import compute_variance_drivers
from app.services.variance_store import save_variance

router = APIRouter(tags=["variance"])


@router.post("/variance/{base_upload_id}/{compare_upload_id}")
def variance(base_upload_id: str, compare_upload_id: str):
    try:
        base_payload = load_metrics(settings.storage_dir, base_upload_id)
        compare_payload = load_metrics(settings.storage_dir, compare_upload_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="metrics not found (run /metrics first)")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # metrics_store returns: {"upload_id": "...", "metrics": {...}}
    base_metrics = base_payload.get("metrics", {})
    compare_metrics = compare_payload.get("metrics", {})

    try:
        result = compute_variance_drivers(base_metrics, compare_metrics)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    payload = {
        "base_upload_id": base_upload_id,
        "compare_upload_id": compare_upload_id,
        **result,  # <-- FLATTEN into top-level so test passes
    }

    out_path = save_variance(settings.storage_dir, base_upload_id, compare_upload_id, payload)

    return {
        "base_upload_id": base_upload_id,
        "compare_upload_id": compare_upload_id,
        "saved_as": str(out_path),
        **result, # optional: also flatten response, OR keep "variance": result

    }
