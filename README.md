# AskTheDocs

AskTheDocs is an AI-powered document Q&A tool built as a portfolio project in order to practice containerisation and cloud deployment of LLM applications on Azure.

Upload a PDF or text file, ask a question in natural language, and get an answer based on your document.
The tool uses a Retrieval-Augmented Generation (RAG) pipeline.

![Progress](https://progress-bar.xyz/40/?title=Project%20Completion&width=500&color=1E3A5F)

🔗 **Live demo (WIP):** [askthedocs.greenpebble-51fc3c0a.westeurope.azurecontainerapps.io](https://askthedocs.greenpebble-51fc3c0a.westeurope.azurecontainerapps.io/static/index.html)
(Please ask for the Admin key)

---

## How it works

1. Upload a document via `/ingest` — it is chunked, embedded, and stored in a vector database
2. Ask a question via `/query` — the most relevant chunks are retrieved and passed to an LLM for context

---

## Tech stack

- **Backend:** Python, FastAPI
- **Vector database:** ChromaDB
- **Embeddings & LLM:** OpenAI API
- **File storage:** Azure Blob Storage
- **Deployment:** Docker, Azure Container Apps
- **CI/CD:** GitHub Actions (runs Pytest before every deployment)

---

## Running locally

### 1. Set up the environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Create a `.env` file

Copy `.env.example` to `.env` and fill in your values:

```
OPENAI_API_KEY=<your OpenAI API key>
API_KEY=<a secret key for API authentication>
AZURE_STORAGE_CONNECTION_STRING=<your Azure Blob Storage connection string>
AZURE_STORAGE_CONTAINER_NAME=<your container name>
```

> You will need an [OpenAI API key](https://platform.openai.com/api-keys) to run the application.

### 3. Start the server

```bash
uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`. The `--reload` flag restarts automatically on code changes.

---

## API reference

All endpoints except `/health` require an `x-api-key` header matching your `API_KEY` environment variable.

| Endpoint  | Method | Auth | Purpose                                 |
|-----------|--------|------|-----------------------------------------|
| `/`       | GET    | ✓    | Opens the frontend UI                   |
| `/health` | GET    | ✗    | Health check                            |
| `/ingest` | POST   | ✓    | Upload PDF or text files for ingestion  |
| `/query`  | POST   | ✓    | Ask a question over ingested documents  |

### Examples

```bash
# Ingest a file
curl -X POST http://localhost:8000/ingest \
  -H "x-api-key: your_api_key" \
  -F "files=@document.pdf"

# Query
curl -X POST http://localhost:8000/query \
  -H "x-api-key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'
```

> The `/ingest` endpoint also uploads files to Azure Blob Storage. A valid `AZURE_STORAGE_CONNECTION_STRING` is required for ingestion to work end-to-end.

---

## Running tests

Tests run automatically via GitHub Actions on every push. To run them locally:

```bash
pytest
```

---

## Roadmap

I am following an agile sprint structure with the intention is to release a fully deployable application from the start.
The following features are currently in progress:

- [ ] **Retrieval quality improvements** — hybrid search (BM25 + vector) and re-ranking using a cross-encoder model for more accurate results
- [ ] **Evaluation pipeline** — automated eval script measuring retrieval hit rate and answer correctness, running as part of CI
- [ ] **React frontend** — replacing the current static HTML frontend with a React application
- [ ] **Azure Monitor integration** — structured log ingestion, dashboards, and alerting
- [ ] **Async document processing** — event-driven ingestion via Azure Service Bus so large file uploads return immediately and are processed in the background

---

## Project structure

```
askthedocs/
├── main.py               # FastAPI app and route definitions
├── utils.py              # Ingestion and query logic
├── requirements.txt
├── Dockerfile
├── .env.example
├── static/               # Frontend (HTML/CSS/JS)
└── tests/                # Pytest test suite
```

---

## License

MIT
