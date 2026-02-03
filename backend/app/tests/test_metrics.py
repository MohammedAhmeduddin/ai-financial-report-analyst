from app.core.config import settings
from app.services.parsing import save_extracted_pages


def test_metrics_missing_upload(client):
    r = client.post("/metrics/does-not-exist")
    assert r.status_code == 404


def test_extract_then_metrics(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    upload_id = "abc123"

    # fake extracted pages (what /extract would have saved)
    pages = [
        {"page": 1, "text": "Net sales 123,456\nNet income (1,234)\n"},
        {"page": 2, "text": "Total assets 9,999\nTotal liabilities 8,888\n"},
    ]
    save_extracted_pages(settings.storage_dir, upload_id, pages)

    r = client.post(f"/metrics/{upload_id}")
    assert r.status_code == 200
    data = r.json()

    assert data["upload_id"] == upload_id
    assert data["metrics"]["revenue"] == 123456.0
    assert data["metrics"]["net_income"] == -1234.0
