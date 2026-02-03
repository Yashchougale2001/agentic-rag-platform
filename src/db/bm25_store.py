# src/retrieval/bm25_store.py
from typing import List, Dict
import re

from rank_bm25 import BM25Okapi


def _simple_tokenize(text: str) -> List[str]:
    # very simple word tokenizer
    return re.findall(r"\w+", text.lower())


class BM25Store:
    """
    Lightweight BM25 index over already-ingested chunks.

    Docs should be a list of:
        {"id": str, "text": str, "metadata": {...}}
    """

    def __init__(self, docs: List[Dict]):
        self.docs = docs or []
        self._corpus_tokens = [
            _simple_tokenize(d.get("text", "")) for d in self.docs
        ]
        if self._corpus_tokens:
            self._bm25 = BM25Okapi(self._corpus_tokens)
        else:
            self._bm25 = None

    def is_empty(self) -> bool:
        return not self.docs or self._bm25 is None

    def search(self, query: str, top_k: int) -> List[Dict]:
        """
        Returns a list of docs with an added 'bm25_score' field.
        """
        if self.is_empty():
            return []

        q_tokens = _simple_tokenize(query)
        scores = self._bm25.get_scores(q_tokens)
        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)
        top = indexed[:top_k]

        results: List[Dict] = []
        for idx, score in top:
            d = self.docs[idx]
            results.append(
                {
                    "id": d["id"],
                    "text": d["text"],
                    "metadata": d.get("metadata", {}),
                    "bm25_score": float(score),
                }
            )
        return results