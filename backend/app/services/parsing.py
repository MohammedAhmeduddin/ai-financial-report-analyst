from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def extracted_pages_path(storage_dir: str | Path, upload_id: str) -> Path:
    storage_dir = Path(storage_dir)
    return storage_dir / "extracted" / f"{upload_id}.json"


def load_extracted_pages(storage_dir: str | Path, upload_id: str) -> List[Dict[str, Any]]:
    """
    Loads page-level extracted text for an upload_id.

    Expected JSON format:
    [
      {"page": 1, "text": "..."},
      {"page": 2, "text": "..."}
    ]
    """
    path = extracted_pages_path(storage_dir, upload_id)
    if not path.exists():
        raise FileNotFoundError(f"Extracted pages not found for upload_id={upload_id} at {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Invalid extracted pages format: expected a list")

    for i, item in enumerate(data):
        if not isinstance(item, dict) or "page" not in item or "text" not in item:
            raise ValueError(f"Invalid page object at index {i}: expected keys 'page' and 'text'")

    return data


def save_extracted_pages(storage_dir: str | Path, upload_id: str, pages: List[Dict[str, Any]]) -> Path:
    """
    Saves extracted pages to disk with stable formatting.
    """
    path = extracted_pages_path(storage_dir, upload_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
