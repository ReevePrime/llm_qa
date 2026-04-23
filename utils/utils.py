import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import openai

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


def extract_and_store(files):
    """Extract text from PDF files, create embeddings, and store them in ChromaDB."""

    text_splitter, collection = initialize()
    for file in files:
        reader = PdfReader(file)
        for page_num, page in enumerate(reader.pages):
            page_content = page.extract_text()
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
                ids=[f"{file.name}_{page_num}_{i}" for i, _ in enumerate(chunks_to_strings)]
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
