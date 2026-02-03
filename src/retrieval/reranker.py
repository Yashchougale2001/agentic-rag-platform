# src/retrieval/reranker.py
from typing import List, Dict
from dataclasses import dataclass

try:
    from FlagEmbedding import FlagReranker
except ImportError:
    FlagReranker = None


@dataclass
class RerankerConfig:
    model_name: str


class BGEReranker:
    """
    Thin wrapper around BAAI/bge-reranker-* models via FlagEmbedding.

    Usage:
        reranker = BGEReranker(RerankerConfig(model_name="BAAI/bge-reranker-base"))
        reranked_docs = reranker.rerank(query, docs)
    """

    def __init__(self, config: RerankerConfig):
        if FlagReranker is None:
            raise ImportError(
                "FlagEmbedding is not installed. "
                "Install with: pip install FlagEmbedding"
            )
        self.config = config
        # use_fp16=True is faster on GPU; safe on CPU too
        self.model = FlagReranker(self.config.model_name, use_fp16=True)

    def rerank(self, query: str, docs: List[Dict]) -> List[Dict]:
        """
        docs: list of dicts each having at least {"text": ...}
        Returns the same docs, sorted by cross-encoder score (descending),
        and adds a 'rerank_score' field to each.
        """
        if not docs:
            return docs

        pairs = [[query, d["text"]] for d in docs]
        scores = self.model.compute_score(pairs)  # list[float]

        for d, s in zip(docs, scores):
            d["rerank_score"] = float(s)

        # Sort in-place by rerank score, highest first
        docs_sorted = sorted(docs, key=lambda d: d["rerank_score"], reverse=True)
        return docs_sorted