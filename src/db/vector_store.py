from typing import List, Dict, Any, Optional
from datetime import datetime
from src.db.chroma_client import ChromaClient


class VectorStore:
    def __init__(self, collection_name: str = "it_assets"):
        self.collection = ChromaClient.get_collection(collection_name)

    def add_documents(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings=None,
    ):
        # Add timestamp
        now = datetime.utcnow().isoformat()
        if metadatas is None:
            metadatas = [{} for _ in texts]
        for m in metadatas:
            if "ingested_at" not in m:
                m["ingested_at"] = now

        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def similarity_search(
        self,
        query_embedding,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ):
        res = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        # Flatten result
        results = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            results.append({"text": doc, "metadata": meta, "distance": dist})
        return results