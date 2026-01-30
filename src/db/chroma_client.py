from typing import Optional
from pathlib import Path
import chromadb

from src.utils.config_loader import load_paths


class ChromaClient:
    _client = None

    @classmethod
    def get_client(cls) -> chromadb.Client:
        if cls._client is None:
            paths = load_paths()
            db_dir = paths.get("db_dir", "data/chroma_db")
            Path(db_dir).mkdir(parents=True, exist_ok=True)
            cls._client = chromadb.PersistentClient(path=db_dir)
        return cls._client

    @classmethod
    def get_collection(cls, name: str = "it_assets"):
        client = cls.get_client()
        return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})