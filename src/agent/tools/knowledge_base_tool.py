# from typing import Dict, List
# from src.retrieval.retriever import Retriever


# class BasicRetrievalTool:
#     """
#     Tool that performs retrieval given a user query.
#     """

#     def __init__(self):
#         self.retriever = Retriever()

#     def run(self, query: str) -> List[Dict]:
#         return self.retriever.retrieve(query)
# src/agent/agent_tools/knowledge_base_tool.py

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Protocol, Union
import logging

logger = logging.getLogger(__name__)


class _CallableRetriever(Protocol):
    """Callable retriever: retriever(query, top_k=5) -> List[docs]."""

    def __call__(self, query: str, top_k: int = 5) -> List[Any]:
        ...


class _ObjectRetriever(Protocol):
    """Object retriever: retriever.retrieve(query, top_k=5) -> List[docs]."""

    def retrieve(self, query: str, top_k: int = 5) -> List[Any]:
        ...


RetrieverLike = Union[_CallableRetriever, _ObjectRetriever]


class KnowledgeBaseTool:
    """
    Tool that queries your knowledge base (vector store / hybrid retriever).

    It is intentionally thin and generic: you inject your existing retriever.

    The retriever can be either:
      - a callable:  retriever(query: str, top_k: int) -> List[docs]
      - an object with .retrieve(query: str, top_k: int) -> List[docs]

    Each doc can be:
      - dict with "text" and "metadata" keys, OR
      - dict with "page_content" and "metadata" keys, OR
      - a LangChain-style Document with .page_content and .metadata.
    """

    def __init__(self, retriever: RetrieverLike, top_k: int = 5):
        self.retriever = retriever
        self.top_k = top_k

    # ------------- Public API -------------

    def run(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query the knowledge base and return normalized docs:
        [
          {
            "text": "...",
            "metadata": {"source": "...", ...}
          },
          ...
        ]
        """
        k = top_k or self.top_k

        try:
            raw_docs = self._call_retriever(query, k) or []
        except Exception as e:
            logger.exception("KnowledgeBaseTool retrieval failed: %s", e)
            return []

        docs: List[Dict[str, Any]] = []
        for d in raw_docs:
            if d is None:
                continue
            normalized = self._normalize_doc(d)
            if normalized["text"]:
                docs.append(normalized)

        return docs

    # ------------- Internal helpers -------------

    def _call_retriever(self, query: str, top_k: int) -> List[Any]:
        """
        Handle both callable retrievers and objects with .retrieve().
        """
        # Object with .retrieve()
        if hasattr(self.retriever, "retrieve") and callable(
            getattr(self.retriever, "retrieve")
        ):
            return self.retriever.retrieve(query=query, top_k=top_k)

        # Plain callable
        if callable(self.retriever):
            return self.retriever(query, top_k)

        raise TypeError(
            "KnowledgeBaseTool.retriever must be callable or have a .retrieve() method."
        )

    def _normalize_doc(self, doc: Any) -> Dict[str, Any]:
        """
        Normalize various document shapes into:
        {"text": str, "metadata": dict}
        """
        text = ""
        metadata: Dict[str, Any] = {}

        # Case 1: dict-like
        if isinstance(doc, dict):
            text = (
                doc.get("text")
                or doc.get("page_content")
                or doc.get("content")
                or ""
            )
            metadata = doc.get("metadata") or {}
        else:
            # Case 2: LangChain Document or similar object
            text = (
                getattr(doc, "text", None)
                or getattr(doc, "page_content", None)
                or getattr(doc, "content", None)
                or ""
            )
            metadata = getattr(doc, "metadata", None) or {}

        # Ensure metadata is a dict
        if not isinstance(metadata, dict):
            metadata = {"raw_metadata": metadata}

        # Fallback source
        if "source" not in metadata:
            metadata["source"] = metadata.get("file_path") or metadata.get(
                "path", "unknown"
            )

        return {"text": text, "metadata": metadata}