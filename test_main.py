from fastapi.testclient import TestClient
from main import app, verify_api_key
from utils.utils import validate_upload, initialize
from unittest.mock import patch, AsyncMock, MagicMock
import io
import os
import tempfile

# Override the API key dependency - app.dependency_overrides lets you swap any dependency for a different implementation during testing.
# Here we replace it with a lambda that always returns True
app.dependency_overrides[verify_api_key] = lambda: True
client = TestClient(app)


# --- Unit test: no HTTP, no auth ---
def test_validate_upload_accepts_pdf():
    # %PDF magic bytes for libmagic to detect application/pdf during testing
    pdf_bytes = b"%PDF-1.4 minimal test content"
    assert validate_upload(pdf_bytes, ["application/pdf"]) is True

def test_validate_upload_rejects_exe():
    # PNG signature — unambiguously detected as image/png by libmagic
    fake_exe = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    assert validate_upload(fake_exe, ["text/*", "application/pdf"]) is False


# --- Integration test: HTTP layer, auth skipped ---
def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200

def test_ingest_endpoint():
    fake_file = io.BytesIO(b"hello world")
    with patch("main.extract_and_store", new=AsyncMock(return_value=None)):
        resp = client.post("/ingest", files={"files": ("test.txt", fake_file, "text/plain")})
    assert resp.status_code == 200


# --- Integration test: upload PDF and query ---
def test_ingest_and_query_real_pdf():
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.pdf")
    FAKE_ANSWER = "The document is about sample PDF content."

    def fake_embed(*args, **kwargs):
        inp = kwargs.get("input", args[0] if args else [])
        count = len(inp) if isinstance(inp, list) else 1
        result = MagicMock()
        result.data = [MagicMock(embedding=[0.1] * 1536) for _ in range(count)]
        return result

    def fake_chat(*args, **kwargs):
        result = MagicMock()
        result.choices[0].message.content = FAKE_ANSWER
        return result

    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("utils.utils.CHROMA_PATH", tmp_dir), \
             patch("openai.embeddings.create", side_effect=fake_embed), \
             patch("openai.chat.completions.create", side_effect=fake_chat), \
             patch("utils.utils.upload_to_azure_blob", return_value="https://fake.blob/test.pdf"):

            with open(pdf_path, "rb") as f:
                ingest_resp = client.post(
                    "/ingest",
                    files={"files": ("test.pdf", f, "application/pdf")}
                )
            assert ingest_resp.status_code == 200

            query_resp = client.post("/query", json={"query": "What is this document about?"})
            assert query_resp.status_code == 200
            assert query_resp.json()["answer"] == FAKE_ANSWER


# --- Unit test: text splitter chunking ---
def test_chunking_count_and_overlap():
    # chunk_size=512, chunk_overlap=64
    # A 1100-char string produces 3 chunks: [0:512], [448:960], [896:1100]
    text = "A" * 1100
    text_splitter, _ = initialize()
    chunks = text_splitter.create_documents([text])

    assert len(chunks) == 3

    # The tail of each chunk must appear at the head of the next
    for i in range(len(chunks) - 1):
        tail = chunks[i].page_content[-64:]
        head = chunks[i + 1].page_content[:64]
        assert tail == head, f"Overlap missing between chunk {i} and chunk {i + 1}"