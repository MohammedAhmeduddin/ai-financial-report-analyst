from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_pdf_returns_upload_id():
    pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
    r = client.post("/upload", files={"file": ("test.pdf", pdf_bytes, "application/pdf")})
    assert r.status_code == 200
    assert "upload_id" in r.json()
