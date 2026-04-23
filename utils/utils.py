import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import openai
import magic
import os
import io
import fnmatch
from fastapi import HTTPException

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
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"{file.filename} exceeds the 10MB size limit")
        if not validate_upload(contents, allowed_mime_types=["text/*", "application/pdf"]):
            raise HTTPException(status_code=415, detail=f"{file.filename} has an unsupported file type")
        if file.filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(contents))
            pages = [page.extract_text() for page in reader.pages]
        else:
            pages = [contents.decode("utf-8")]
        for page_num, page_content in enumerate(pages):
            chunks = text_splitter.create_documents([page_content])
            chunks_to_strings = [chunk.page_content for chunk in chunks]
            response = openai.embeddings.create(
                input=chunks_to_strings,
                model=EMBEDDING_MODEL
            )
            embeddings = [item.embedding for item in response.data]
            collection.add(
                embeddings=embeddings,
                documents=chunks_to_strings,
                ids=[f"{file.filename}_{page_num}_{i}" for i, _ in enumerate(chunks_to_strings)]
            )


def query_llm(query: str) -> str:
    """Query the LLM with a question, retrieve relevant context from ChromaDB, and return the answer."""
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
            {"role": "system", "content": "Answer the question using only the context provided."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )

    return response.choices[0].message.content

def validate_upload(file_bytes: bytes, allowed_mime_types: list[str]) -> bool:
    detected = magic.from_buffer(file_bytes, mime=True)
    # Run wildcard pattern matching against the detected MIME type to allow for patterns like "text/*"
    return any(fnmatch.fnmatch(detected, pattern) for pattern in allowed_mime_types)



