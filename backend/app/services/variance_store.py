# backend/app/services/variance_store.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def variance_path(storage_dir: str, base_upload_id: str, compare_upload_id: str) -> Path:
    return Path(storage_dir) / "variance" / f"{base_upload_id}__vs__{compare_upload_id}.json"


def save_variance(
    storage_dir: str,
    base_upload_id: str,
    compare_upload_id: str,
    payload: Dict[str, Any],
) -> Path:
    out_path = variance_path(storage_dir, base_upload_id, compare_upload_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
