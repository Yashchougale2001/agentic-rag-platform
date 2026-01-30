import logging
from fastapi import FastAPI

from src.utils.config_loader import ensure_directories
from api.routes import query, ingest

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="IT Agentic RAG Chatbot API", version="0.1.0")

ensure_directories()

app.include_router(query.router)
app.include_router(ingest.router)


@app.get("/")
async def root():
    return {"message": "IT Agentic RAG Chatbot API"}