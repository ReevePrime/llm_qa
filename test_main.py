from fastapi.testclient import TestClient
from main import app, verify_api_key
from utils.utils import validate_upload
import io

# Override the API key dependency - app.dependency_overrides lets you swap any dependency for a different implementation during testing. 
# Here we replace it with a lambda that always returns True
app.dependency_overrides[verify_api_key] = lambda: True
client = TestClient(app)


# --- Unit test: no HTTP, no auth ---
def test_validate_upload_accepts_pdf():
    with open("test.pdf", "rb") as f:
        assert validate_upload(f.read(), ["application/pdf"]) is True

def test_validate_upload_rejects_exe():
    fake_exe = b"MZ\x90\x00"  # PE header magic bytes
    assert validate_upload(fake_exe, ["text/*", "application/pdf"]) is False


# --- Integration test: HTTP layer, auth skipped ---
def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200

def test_ingest_endpoint():
    fake_file = io.BytesIO(b"hello world")
    resp = client.post("/ingest", files={"files": ("test.txt", fake_file, "text/plain")})
    assert resp.status_code == 200