# src/retrieval/hybrid_retriever.py
from typing import List, Dict, Callable
from dataclasses import dataclass
import logging

from src.db.vector_store import VectorStore
from src.retrieval.bm25_store import BM25Store
from src.embeddings.embedder import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class HybridRetrievalConfig:
    top_k: int
    dense_k: int
    lexical_k: int
    dense_weight: float
    min_relevance: float


class HybridRetriever:
    """
    Hybrid retriever: combines dense similarity (Chroma) and BM25 scores.

    - Pulls `dense_k` candidates with embeddings from Chroma.
    - Pulls `lexical_k` candidates via BM25.
    - Normalizes both scores and merges them using `dense_weight`.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        bm25_store: BM25Store,
        embedder: EmbeddingService,
        cfg: HybridRetrievalConfig,
        recency_boost_fn: Callable[[Dict], float],
    ):
        self.vs = vector_store
        self.bm25 = bm25_store
        self.embedder = embedder
        self.cfg = cfg
        self._recency_boost = recency_boost_fn

    def retrieve(self, query: str) -> List[Dict]:
        if self.bm25.is_empty():
            logger.warning("BM25 store is empty; falling back to dense-only in hybrid.")
            return []

        # ---- Dense retrieval ----
        dense_docs: List[Dict] = []
        if self.cfg.dense_k > 0:
            q_emb = self.embedder.embed_query(query)
            dense_results = self.vs.similarity_search(
                query_embedding=q_emb,
                top_k=self.cfg.dense_k,
            )
            for r in dense_results:
                dist = r.get("distance", 1.0)
                base_sim = 1.0 / (1.0 + dist)
                boost = self._recency_boost(r.get("metadata", {}))
                dense_score = base_sim + boost
                dense_docs.append(
                    {
                        "id": r.get("id") or r["metadata"].get("id"),
                        "text": r["text"],
                        "metadata": r.get("metadata", {}),
                        "dense_score": dense_score,
                        "distance": dist,
                    }
                )

        # ---- Lexical retrieval (BM25) ----
        lexical_docs = self.bm25.search(query, top_k=self.cfg.lexical_k)

        # ---- Merge by id ----
        combined: Dict[str, Dict] = {}

        for d in dense_docs:
            _id = d["id"]
            if _id is None:
                # fallback if id is not present in metadata
                _id = d["metadata"].get("source", "") + "#" + d["text"][:32]
                d["id"] = _id
            combined[_id] = d

        for d in lexical_docs:
            _id = d["id"]
            if _id in combined:
                combined[_id]["bm25_score"] = d["bm25_score"]
            else:
                combined[_id] = {
                    "id": _id,
                    "text": d["text"],
                    "metadata": d.get("metadata", {}),
                    "dense_score": 0.0,
                    "bm25_score": d["bm25_score"],
                }

        docs = list(combined.values())
        if not docs:
            return []

        # Ensure bm25_score field exists
        for d in docs:
            if "bm25_score" not in d:
                d["bm25_score"] = 0.0

        # Normalize scores to [0,1] and combine
        max_dense = max((d.get("dense_score", 0.0) for d in docs), default=0.0)
        max_bm25 = max((d.get("bm25_score", 0.0) for d in docs), default=0.0)

        for d in docs:
            dense_norm = (
                d.get("dense_score", 0.0) / max_dense if max_dense > 0 else 0.0
            )
            bm25_norm = (
                d.get("bm25_score", 0.0) / max_bm25 if max_bm25 > 0 else 0.0
            )
            hybrid_score = (
                self.cfg.dense_weight * dense_norm
                + (1.0 - self.cfg.dense_weight) * bm25_norm
            )
            d["score"] = hybrid_score
            d["hybrid_score"] = hybrid_score

        # Filter & sort
        filtered = [
            d for d in docs if d["score"] >= self.cfg.min_relevance
        ]
        filtered.sort(key=lambda x: x["score"], reverse=True)

        return filtered[: self.cfg.top_k]