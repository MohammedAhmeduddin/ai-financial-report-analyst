import json
from pathlib import Path

from app.core.config import settings


def _write_extracted(tmp_path, upload_id: str):
    # matches parsing.py expectation: list of {"page","text"}
    extracted_dir = Path(tmp_path) / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    (extracted_dir / f"{upload_id}.json").write_text(
        json.dumps(
            [{"page": 1, "text": "Net income was 200 for the period."}],
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_metrics(tmp_path, upload_id: str):
    metrics_dir = Path(tmp_path) / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    (metrics_dir / f"{upload_id}.json").write_text(
        json.dumps({"upload_id": upload_id, "metrics": {"net_income": 200}}, indent=2),
        encoding="utf-8",
    )


def test_ask_numbers_first_returns_metric_and_citations(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    upload_id = "u1"
    _write_extracted(tmp_path, upload_id)
    _write_metrics(tmp_path, upload_id)

    r = client.post(f"/ask/{upload_id}", json={"question": "What is net income?"})
    assert r.status_code == 200

    data = r.json()
    assert data["upload_id"] == upload_id
    assert "computed" in data
    assert data["computed"]["net_income"] == 200
    assert "citations" in data
    assert len(data["citations"]) >= 1
