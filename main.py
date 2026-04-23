from dotenv import load_dotenv
from utils import extract_and_store, query_llm
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

@app.get("/")
async def first_api():
    return {"message": "Hello World!"}


@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    extract_and_store(files)
    return {"message": f"Ingested {len(files)} file(s)"}

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def query(request: QueryRequest):
    answer = query_llm(request.query)
    return {"answer": answer}


