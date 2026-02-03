from app.core.config import settings


def test_chunks_missing_upload(client):
    r = client.get("/uploads/does-not-exist/chunks")
    assert r.status_code == 404


def test_upload_extract_then_chunks(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "extracted_dir", str(tmp_path / "extracted"))

    pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\n%%EOF\n"
    up = client.post("/upload", files={"file": ("a.pdf", pdf, "application/pdf")})
    assert up.status_code == 200
    upload_id = up.json()["upload_id"]

    ex = client.post(f"/extract/{upload_id}")
    assert ex.status_code == 200

    ch = client.get(f"/uploads/{upload_id}/chunks")
    assert ch.status_code == 200
    data = ch.json()
    assert data["upload_id"] == upload_id
    assert data["chunk_count"] >= 1
    assert "chunks" in data
