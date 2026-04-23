import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import openai

def initialize():
    # Initialize the text splitter and the ChromaDB collection
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        length_function=len,
    )
    client = chromadb.PersistentClient(path="./chroma_data")
    collection = client.get_or_create_collection("openai_embeddings")
    return text_splitter, collection

def extract_and_store(args):
  text_splitter, collection = initialize()
  # Loop through each PDF file, extract text and split it into chunks
  for file in args.files:
      reader = PdfReader(file)
      for page_num, page in enumerate(reader.pages):
          page_content = page.extract_text()
          chunks = text_splitter.create_documents([page_content])
          chunks_to_strings = [chunk.page_content for chunk in chunks]
          response = openai.embeddings.create(
            input=chunks_to_strings,
            model="text-embedding-3-small"
          )

          # Extract the embeddings from the response and add them to the ChromaDB collection
          embeddings = [item.embedding for item in response.data]
          collection.add(
              embeddings=embeddings,
              documents=chunks_to_strings,
              ids=[f"{file.name}_{page_num}_{i}" for i, _ in enumerate(chunks_to_strings)]
          )