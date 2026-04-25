import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import openai
import magic
import os
import io
import fnmatch
import logging
from fastapi import HTTPException
from pythonjsonlogger.json import JsonFormatter
import time
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)
# Handlers control where the logs are written.
handler = logging.FileHandler("logs.json")
handler.setFormatter(JsonFormatter(                       # setFormatter controls the way log entries look.
    fmt="%(asctime)s %(levelname)s %(message)s"))
# Links the handler to the logger. (Handlers can have multiple loggers)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

CHROMA_PATH = "./chroma_data"
COLLECTION_NAME = "openai_embeddings"
EMBEDDING_MODEL = "text-embedding-3-small"


def initialize():
    """Initialize the text splitter and ChromaDB client."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        length_function=len,
    )
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)
    return text_splitter, collection


async def extract_and_store(files):
    """Extract text from PDF files, create embeddings, and store them in ChromaDB."""

    text_splitter, collection = initialize()

    for file in files:
        start_time = time.time()
        contents = await file.read()

        # --- Validate file (size and type) ---
        if len(contents) > MAX_FILE_SIZE:
            logger.warning("File size limit exceeded", extra={
                "endpoint": "/api/upload",
                "latency": time.time() - start_time,
                "file_name": file.filename,
                "size": len(contents),
                "document_id": None,
                "status_code": 413,
                "error": "File size exceeds 10MB limit",
            })
            raise HTTPException(
                status_code=413, detail=f"{file.filename} exceeds the 10MB size limit")

        if not validate_upload(contents, allowed_mime_types=["text/*", "application/pdf"]):
            logger.warning("Unsupported file type", extra={
                "endpoint": "/api/upload",
                "latency": time.time() - start_time,
                "file_name": file.filename,
                "document_id": None,
                "status_code": 415,
                "error": f"File '{file.filename}' has an unsupported file type",
            })
            raise HTTPException(
                status_code=415, detail=f"{file.filename} has an unsupported file type")

        try:
            # --- Extract pages from text ---
            if file.filename.endswith(".pdf"):
                reader = PdfReader(io.BytesIO(contents))
                pages = [page.extract_text() for page in reader.pages]
            else:
                pages = [contents.decode("utf-8")]

            # --- Upload original file to Blob Storage ---
            file_url = upload_to_azure_blob(
                file_bytes=contents, file_name=file.filename)

            # --- Chunk, embed, and store each page ---
            for page_num, page_content in enumerate(pages):
                chunks = text_splitter.create_documents([page_content])
                chunks_to_strings = [chunk.page_content for chunk in chunks]

                response = openai.embeddings.create(
                    input=chunks_to_strings,
                    model=EMBEDDING_MODEL
                )
                embeddings = [item.embedding for item in response.data]

                collection.add(
                    embeddings=embeddings,        # The vector representations of the text chunks
                    documents=chunks_to_strings,  # The original text chunks
                    ids=[f"{file.filename}_{page_num}_{i}" for i,
                         _ in enumerate(chunks_to_strings)],
                    # Adds the file URL as metadata to each chunk
                    metadatas=[{"source": file_url} for _ in chunks_to_strings]
                )

            logger.info("File ingested successfully", extra={
                "endpoint": "/api/upload",
                "latency": time.time() - start_time,
                "file_name": file.filename,
                "status_code": 200,
            })

        except HTTPException:
            raise
        except Exception:
            logger.error("Failed to process file", exc_info=True, extra={
                "endpoint": "/api/upload",
                "latency": time.time() - start_time,
                "file_name": file.filename,
                "document_id": None,
                "status_code": 500,
                "error": f"Failed to process file '{file.filename}'",
            })
            raise HTTPException(
                status_code=500, detail=f"Failed to process {file.filename}")


def query_llm(query: str) -> str:
    """Query the LLM with a question, retrieve relevant context from ChromaDB, and return the answer."""
    start_time = time.time()
    try:
        query_embedding = openai.embeddings.create(
            input=query,
            model=EMBEDDING_MODEL
        ).data[0].embedding

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(COLLECTION_NAME)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        context = "\n\n".join(results["documents"][0])

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                    "content": "Answer the question using only the context provided."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
        )

        logger.info("Query completed successfully", extra={
            "endpoint": "/api/query",
            "latency": time.time() - start_time,
            "query": query,
            "status_code": 200,
        })
        return response.choices[0].message.content
    except Exception:
        logger.error("Failed to process query", exc_info=True, extra={
            "endpoint": "/api/query",
            "latency": time.time() - start_time,
            "query": query,
            "status_code": 500,
            "error": f"Failed to process query '{query}'",
        })
        raise


def validate_upload(file_bytes: bytes, allowed_mime_types: list[str]) -> bool:
    detected = magic.from_buffer(file_bytes, mime=True)
    # Run wildcard pattern matching against the detected MIME type to allow for patterns like "text/*"
    return any(fnmatch.fnmatch(detected, pattern) for pattern in allowed_mime_types)


def upload_to_azure_blob(file_bytes: bytes, file_name: str):
    try:
        # --- Connect to storage ---
        blob_service_client = BlobServiceClient.from_connection_string(
            os.environ.get("AZURE_STORAGE_CONNECTION_STRING"))
        blob_client = blob_service_client.get_blob_client(
            container=os.environ.get("AZURE_STORAGE_CONTAINER_NAME"), blob=file_name)

        # --- Upload and return the URL ---
        blob_client.upload_blob(file_bytes)
        return blob_client.url

    except Exception:
        logger.error("Failed to upload file to Azure Blob Storage", exc_info=True, extra={
            "endpoint": "/api/upload",
            "file_name": file_name,
            "status_code": 500,
            "error": f"Failed to upload file '{file_name}' to Azure Blob Storage",
        })
        raise HTTPException(
            status_code=500, detail=f"Failed to upload {file_name} to Azure Blob Storage")
