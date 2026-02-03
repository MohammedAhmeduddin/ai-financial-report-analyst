import json
from pathlib import Path

from app.core.config import settings


def _write_metrics(tmp_path: Path, upload_id: str, metrics: dict):
    p = Path(settings.storage_dir) / "metrics"
    p.mkdir(parents=True, exist_ok=True)

    out = p / f"{upload_id}.json"
    out.write_text(
        json.dumps({"upload_id": upload_id, "metrics": metrics}, indent=2),
        encoding="utf-8",
    )


def test_variance_missing_metrics(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    r = client.post("/variance/base123/comp456")
    assert r.status_code == 404


def test_variance_happy_path_saves_file(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    base_id = "base1"
    comp_id = "comp1"

    _write_metrics(
        tmp_path,
        base_id,
        {"revenue": 1000, "gross_profit": 600, "operating_income": 300, "net_income": 200},
    )
    _write_metrics(
        tmp_path,
        comp_id,
        {"revenue": 900, "gross_profit": 450, "operating_income": 200, "net_income": 120},
    )

    r = client.post(f"/variance/{base_id}/{comp_id}")
    assert r.status_code == 200

    data = r.json()
    assert data["base_upload_id"] == base_id
    assert data["compare_upload_id"] == comp_id
    assert "saved_as" in data

    saved_path = Path(data["saved_as"])
    assert saved_path.exists()

    saved_json = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved_json["base_upload_id"] == base_id
    assert saved_json["compare_upload_id"] == comp_id
    assert "net_income_change" in saved_json
    assert "drivers" in saved_json
