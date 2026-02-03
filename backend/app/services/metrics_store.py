from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def metrics_path(storage_dir: str, upload_id: str) -> Path:
    return Path(storage_dir) / "metrics" / f"{upload_id}.json"


def save_metrics(storage_dir: str, upload_id: str, payload: Dict[str, Any]) -> Path:
    path = metrics_path(storage_dir, upload_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_metrics(storage_dir: str, upload_id: str) -> Dict[str, Any]:
    path = metrics_path(storage_dir, upload_id)
    if not path.exists():
        raise FileNotFoundError(f"Metrics not found for upload_id={upload_id} at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid metrics format: expected a dict")
    return data
