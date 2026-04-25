from dotenv import load_dotenv
from utils import extract_and_store, query_llm
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os


load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/index.html")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# API key verification dependency
async def verify_api_key(x_api_key: str = Header(...)):
    expected = os.getenv("API_KEY")
    if x_api_key != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

class QueryRequest(BaseModel):
    query: str

@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...), _=Depends(verify_api_key)):
    await extract_and_store(files)
    return {"message": f"Ingested {len(files)} file(s)"}

@app.post("/query")
async def query(request: QueryRequest, _=Depends(verify_api_key)):
    answer = query_llm(request.query)
    return {"answer": answer}