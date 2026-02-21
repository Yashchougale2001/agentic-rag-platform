# api/main.py

from __future__ import annotations

import logging
from fastapi import FastAPI
from dotenv import load_dotenv  # NEW

from src.utils.logging_config import setup_logging
from src.utils.config_loader import ensure_directories

# Load .env first
load_dotenv()

# Configure logging BEFORE importing routers
setup_logging()
logger = logging.getLogger(__name__)

from api.routes import query, ingest, feedback  # noqa: E402


app = FastAPI(
    title="Agentic RAG Chatbot API",
    version="0.1.0",
)

# Ensure data/db/logs/tmp directories exist
ensure_directories()

# Register routers
app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(feedback.router)


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Agentic RAG Chatbot API"}


@app.on_event("startup")
async def on_startup():
    logger.info("API startup complete.")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("API shutting down.")