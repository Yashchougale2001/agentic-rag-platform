from typing import List, Dict
from datetime import datetime
from src.embeddings.embedder import EmbeddingService
from src.db.vector_store import VectorStore
from src.utils.config_loader import load_settings


class Retriever:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.store = VectorStore()
        self.settings = load_settings()
        self.top_k = self.settings.get("retrieval", {}).get("top_k", 5)
        self.min_relevance = self.settings.get("retrieval", {}).get(
            "min_relevance_score", 0.2
        )

    def retrieve(self, query: str) -> List[Dict]:
        q_emb = self.embedder.embed_query(query)
        results = self.store.similarity_search(
            query_embedding=q_emb,
            top_k=self.top_k,
        )

        if not results:
            return []

        # Convert distance to similarity score; Chroma uses distance, assume 0 is best.
        for r in results:
            # naive similarity: 1 / (1 + distance)
            dist = r.get("distance", 1.0)
            r["score"] = 1.0 / (1.0 + dist)

        # Prioritize recent (ingested_at)
        def recency_boost(meta):
            ts = meta.get("ingested_at")
            if not ts:
                return 0.0
            try:
                dt = datetime.fromisoformat(ts)
                # simple recency scaled; more recent gets small boost
                return (datetime.utcnow() - dt).total_seconds() * -1e-7
            except Exception:
                return 0.0

        for r in results:
            r["score"] += recency_boost(r["metadata"])

        # Filter low scores
        filtered = [r for r in results if r["score"] >= self.min_relevance]
        filtered.sort(key=lambda x: x["score"], reverse=True)

        return filtered