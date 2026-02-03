from app.core.config import settings


def test_ask_missing_metrics(client):
    r = client.post("/ask/does-not-exist", json={"question": "What is revenue?"})
    assert r.status_code in (404, 422)


def test_upload_extract_metrics_then_ask(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "extracted_dir", str(tmp_path / "extracted"))

    pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\n%%EOF\n"
    up = client.post("/upload", files={"file": ("a.pdf", pdf, "application/pdf")})
    upload_id = up.json()["upload_id"]

    ex = client.post(f"/extract/{upload_id}")
    assert ex.status_code == 200

    m = client.post(f"/metrics/{upload_id}")
    assert m.status_code == 200

    r = client.post(f"/ask/{upload_id}", json={"question": "What is net income?"})
    assert r.status_code == 200
    data = r.json()

    assert data["upload_id"] == upload_id
    assert "numbers_first" in data
    assert "metrics" in data["numbers_first"]
    assert "evidence" in data
