import json
from pathlib import Path

from app.core.config import settings


def _write_metrics(tmp_path: Path, upload_id: str, metrics: dict):
    p = tmp_path / "metrics"
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{upload_id}.json").write_text(
        json.dumps({"upload_id": upload_id, "metrics": metrics}, indent=2),
        encoding="utf-8",
    )


def _write_extracted(tmp_path: Path, upload_id: str, text: str):
    p = tmp_path / "extracted"
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{upload_id}.json").write_text(
        json.dumps([{"page": 1, "text": text}], indent=2),
        encoding="utf-8",
    )


def test_ask_compare_returns_variance_and_citations(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    base_id = "base1"
    comp_id = "comp1"

    _write_metrics(tmp_path, base_id, {"revenue": 1000, "gross_profit": 600, "operating_income": 300, "net_income": 200})
    _write_metrics(tmp_path, comp_id, {"revenue": 900, "gross_profit": 450, "operating_income": 200, "net_income": 120})

    _write_extracted(tmp_path, base_id, "Net income increased due to revenue growth and improved gross margin.")
    _write_extracted(tmp_path, comp_id, "Net income decreased due to lower revenue and higher operating expenses.")

    r = client.post(f"/ask/{base_id}", json={"question": "Compare net income drivers", "compare_upload_id": comp_id})
    assert r.status_code == 200

    data = r.json()
    assert data["upload_id"] == base_id
    assert data["compare_upload_id"] == comp_id
    assert "numbers_first" in data
    assert "variance" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert "net_income_change" in data["variance"]
