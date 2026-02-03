from app.core.config import settings


def test_extract_missing_upload(client):
    r = client.post("/extract/does-not-exist")
    assert r.status_code == 404


def test_upload_then_extract(client, tmp_path, monkeypatch):
    # redirect storage to temp dirs for clean testing
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\n%%EOF\n"

    up = client.post("/upload", files={"file": ("a.pdf", pdf, "application/pdf")})
    assert up.status_code == 200
    upload_id = up.json()["upload_id"]

    ex = client.post(f"/extract/{upload_id}")
    assert ex.status_code == 200
