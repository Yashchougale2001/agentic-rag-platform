# # from typing import List, Dict
# # from datetime import datetime
# # from src.embeddings.embedder import EmbeddingService
# # from src.db.vector_store import VectorStore
# # from src.utils.config_loader import load_settings


# # class Retriever:
# #     def __init__(self):
# #         self.embedder = EmbeddingService()
# #         self.store = VectorStore()
# #         self.settings = load_settings()
# #         self.top_k = self.settings.get("retrieval", {}).get("top_k", 5)
# #         self.min_relevance = self.settings.get("retrieval", {}).get(
# #             "min_relevance_score", 0.2
# #         )

# #     def retrieve(self, query: str) -> List[Dict]:
# #         q_emb = self.embedder.embed_query(query)
# #         results = self.store.similarity_search(
# #             query_embedding=q_emb,
# #             top_k=self.top_k,
# #         )

# #         if not results:
# #             return []

# #         # Convert distance to similarity score; Chroma uses distance, assume 0 is best.
# #         for r in results:
# #             # naive similarity: 1 / (1 + distance)
# #             dist = r.get("distance", 1.0)
# #             r["score"] = 1.0 / (1.0 + dist)

# #         # Prioritize recent (ingested_at)
# #         def recency_boost(meta):
# #             ts = meta.get("ingested_at")
# #             if not ts:
# #                 return 0.0
# #             try:
# #                 dt = datetime.fromisoformat(ts)
# #                 # simple recency scaled; more recent gets small boost
# #                 return (datetime.utcnow() - dt).total_seconds() * -1e-7
# #             except Exception:
# #                 return 0.0

# #         for r in results:
# #             r["score"] += recency_boost(r["metadata"])

# #         # Filter low scores
# #         filtered = [r for r in results if r["score"] >= self.min_relevance]
# #         filtered.sort(key=lambda x: x["score"], reverse=True)

# #         return filtered
# from typing import List, Dict
# from datetime import datetime
# import logging

# from src.embeddings.embedder import EmbeddingService
# from src.db.vector_store import VectorStore
# from src.utils.config_loader import load_settings, load_model_config

# logger = logging.getLogger(__name__)


# class Retriever:
#     def __init__(self):
#         self.embedder = EmbeddingService()
#         self.store = VectorStore()

#         # App-level settings (legacy) + model config
#         self.settings = load_settings()
#         self.model_cfg = load_model_config()

#         # Prefer model.yaml:retrieval, fall back to settings.yaml:retrieval if needed
#         model_retrieval = self.model_cfg.get("retrieval", {})
#         settings_retrieval = self.settings.get("retrieval", {})

#         self.top_k = model_retrieval.get(
#             "top_k",
#             settings_retrieval.get("top_k", 5),
#         )
#         self.min_relevance = model_retrieval.get(
#             "min_relevance_score",
#             settings_retrieval.get("min_relevance_score", 0.2),
#         )

#         self.use_reranker = model_retrieval.get("use_reranker", False)
#         self.reranker = None

#         if self.use_reranker:
#             try:
#                 from src.retrieval.reranker import BGEReranker, RerankerConfig

#                 reranker_model = model_retrieval.get(
#                     "reranker_model", "BAAI/bge-reranker-base"
#                 )
#                 self.reranker = BGEReranker(
#                     RerankerConfig(model_name=reranker_model)
#                 )
#                 logger.info("Initialized BGE reranker with model %s", reranker_model)
#             except ImportError:
#                 logger.warning(
#                     "Reranker is enabled in config but FlagEmbedding is not installed. "
#                     "Install with `pip install FlagEmbedding` to enable reranking. "
#                     "Falling back to dense retrieval only."
#                 )
#                 self.reranker = None
#             except Exception as e:
#                 logger.warning("Failed to initialize reranker: %s", e)
#                 self.reranker = None

#     def _recency_boost(self, metadata: Dict) -> float:
#         """
#         Same behavior as before: newer docs get a small positive boost.
#         """
#         ts = metadata.get("ingested_at")
#         if not ts:
#             return 0.0
#         try:
#             dt = datetime.fromisoformat(ts)
#             # negative seconds -> smaller (more recent) gives slightly higher boost
#             return (datetime.utcnow() - dt).total_seconds() * -1e-7
#         except Exception:
#             return 0.0

#     def retrieve(self, query: str) -> List[Dict]:
#         q_emb = self.embedder.embed_query(query)
#         results = self.store.similarity_search(
#             query_embedding=q_emb,
#             top_k=self.top_k,
#         )

#         if not results:
#             return []

#         # Compute similarity score from Chroma distance and add recency boost.
#         for r in results:
#             dist = r.get("distance", 1.0)
#             # naive similarity: 1 / (1 + distance)
#             base_sim = 1.0 / (1.0 + dist)
#             boost = self._recency_boost(r.get("metadata", {}))
#             r["score"] = base_sim + boost

#         # Filter low scores
#         filtered = [r for r in results if r["score"] >= self.min_relevance]
#         if not filtered:
#             return []

#         # Sort by dense+recency score first
#         filtered.sort(key=lambda x: x["score"], reverse=True)

#         # Optional cross-encoder reranking
#         if self.use_reranker and self.reranker is not None:
#             try:
#                 filtered = self.reranker.rerank(query, filtered)
#             except Exception as e:
#                 logger.warning("Reranker failed; falling back to dense ranking: %s", e)

#         return filtered
from typing import List, Dict
from datetime import datetime
import logging

from src.embeddings.embedder import EmbeddingService
from src.db.vector_store import VectorStore
from src.utils.config_loader import load_settings, load_model_config

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.store = VectorStore()

        # App-level settings (legacy) + model config
        self.settings = load_settings()
        self.model_cfg = load_model_config()

        model_retrieval = self.model_cfg.get("retrieval", {})
        settings_retrieval = self.settings.get("retrieval", {})

        # Final top-k to return
        self.top_k = model_retrieval.get(
            "top_k",
            settings_retrieval.get("top_k", 5),
        )
        self.min_relevance = model_retrieval.get(
            "min_relevance_score",
            settings_retrieval.get("min_relevance_score", 0.2),
        )

        # Retrieval mode: dense | hybrid | lexical
        self.mode = model_retrieval.get("mode", "dense").lower()

        # Expansion sizes
        self.dense_k = model_retrieval.get("dense_k", self.top_k)
        self.lexical_k = model_retrieval.get("lexical_k", self.top_k)
        self.dense_weight = model_retrieval.get("hybrid_dense_weight", 0.5)

        # Reranker
        self.use_reranker = model_retrieval.get("use_reranker", False)
        self.reranker = None
        if self.use_reranker:
            try:
                from src.retrieval.reranker import BGEReranker, RerankerConfig

                reranker_model = model_retrieval.get(
                    "reranker_model", "BAAI/bge-reranker-base"
                )
                self.reranker = BGEReranker(
                    RerankerConfig(model_name=reranker_model)
                )
                logger.info("Initialized BGE reranker with model %s", reranker_model)
            except ImportError:
                logger.warning(
                    "Reranker is enabled but FlagEmbedding is not installed. "
                    "Install with `pip install FlagEmbedding` to enable reranking. "
                    "Falling back to retrieval without reranking."
                )
                self.reranker = None
            except Exception as e:
                logger.warning("Failed to initialize reranker: %s", e)
                self.reranker = None

        # Hybrid / lexical setup
        self.bm25_store = None
        self.hybrid_retriever = None

        if self.mode in ("hybrid", "lexical"):
            try:
                from src.retrieval.bm25_store import BM25Store

                all_docs = self.store.get_all_documents()
                if not all_docs:
                    logger.warning(
                        "BM25 index requested (mode=%s) but no documents found in vector store.",
                        self.mode,
                    )
                else:
                    self.bm25_store = BM25Store(all_docs)
                    if self.bm25_store.is_empty():
                        logger.warning(
                            "BM25 index is empty after initialization; "
                            "lexical/hybrid retrieval will be ineffective."
                        )
                    else:
                        logger.info(
                            "Initialized BM25 store with %d documents", len(all_docs)
                        )
            except ImportError:
                logger.warning(
                    "rank_bm25 is not installed, cannot use lexical/hybrid retrieval. "
                    "Install with `pip install rank_bm25`. Falling back to dense."
                )
                self.mode = "dense"
            except Exception as e:
                logger.warning("Failed to initialize BM25 store: %s", e)
                self.mode = "dense"

        # Hybrid retriever
        if self.mode == "hybrid" and self.bm25_store is not None:
            try:
                from src.retrieval.hybrid_retriever import (
                    HybridRetriever,
                    HybridRetrievalConfig,
                )

                cfg = HybridRetrievalConfig(
                    top_k=self.top_k,
                    dense_k=self.dense_k,
                    lexical_k=self.lexical_k,
                    dense_weight=self.dense_weight,
                    min_relevance=self.min_relevance,
                )

                self.hybrid_retriever = HybridRetriever(
                    vector_store=self.store,
                    bm25_store=self.bm25_store,
                    embedder=self.embedder,
                    cfg=cfg,
                    recency_boost_fn=self._recency_boost,
                )
                logger.info("Hybrid retriever initialized.")
            except Exception as e:
                logger.warning(
                    "Failed to initialize HybridRetriever (%s). Falling back to dense.",
                    e,
                )
                self.mode = "dense"
                self.hybrid_retriever = None

    def _recency_boost(self, metadata: Dict) -> float:
        """
        Newer docs get a small positive boost.
        """
        ts = metadata.get("ingested_at")
        if not ts:
            return 0.0
        try:
            dt = datetime.fromisoformat(ts)
            return (datetime.utcnow() - dt).total_seconds() * -1e-7
        except Exception:
            return 0.0

    def _dense_retrieve(self, query: str) -> List[Dict]:
        q_emb = self.embedder.embed_query(query)
        results = self.store.similarity_search(
            query_embedding=q_emb,
            top_k=self.dense_k,
        )

        if not results:
            return []

        for r in results:
            dist = r.get("distance", 1.0)
            base_sim = 1.0 / (1.0 + dist)
            boost = self._recency_boost(r.get("metadata", {}))
            r["score"] = base_sim + boost

        filtered = [r for r in results if r["score"] >= self.min_relevance]
        filtered.sort(key=lambda x: x["score"], reverse=True)

        return filtered[: self.top_k]

    def _lexical_retrieve(self, query: str) -> List[Dict]:
        if self.bm25_store is None or self.bm25_store.is_empty():
            logger.warning(
                "Lexical retrieval requested but BM25 store is not available; returning empty."
            )
            return []

        docs = self.bm25_store.search(query, top_k=self.lexical_k)
        for d in docs:
            boost = self._recency_boost(d.get("metadata", {}))
            # Use raw BM25 score + tiny recency boost for ranking
            d["score"] = d["bm25_score"] + boost

        docs.sort(key=lambda x: x["score"], reverse=True)
        return docs[: self.top_k]

    def retrieve(self, query: str) -> List[Dict]:
        # Choose retrieval mode
        if self.mode == "hybrid" and self.hybrid_retriever is not None:
            docs = self.hybrid_retriever.retrieve(query)
        elif self.mode == "lexical":
            docs = self._lexical_retrieve(query)
        else:
            docs = self._dense_retrieve(query)

        if not docs:
            return []

        # Optional cross-encoder reranking on top of the chosen retrieval
        if self.use_reranker and self.reranker is not None:
            try:
                docs = self.reranker.rerank(query, docs)
            except Exception as e:
                logger.warning("Reranker failed; returning pre-rerank results: %s", e)

        return docs