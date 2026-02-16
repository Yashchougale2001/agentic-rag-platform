
# # src/agent/tools/local_search_tool.py
# import os
# import glob
# import re
# from typing import List, Dict, Any


# class LocalSearchTool:
#     """
#     Simple keyword-based search over a local directory of text files.
#     Used as a fallback when vector search finds nothing.
#     """

#     def __init__(self, local_dir: str):
#         self.local_dir = local_dir
#         os.makedirs(local_dir, exist_ok=True)

#     def run(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
#         if not os.path.exists(self.local_dir):
#             return []

#         # Better tokenization: remove punctuation, keep word chars only
#         tokens = re.findall(r"\w+", query.lower())
#         keywords = [t for t in tokens if len(t) > 2]

#         candidates: List[Dict[str, Any]] = []

#         for filepath in glob.glob(f"{self.local_dir}/**/*.*", recursive=True):
#             if os.path.isdir(filepath):
#                 continue

#             # Optional: limit to text-like files (uncomment if needed)
#             # if not filepath.lower().endswith((".txt", ".md", ".csv")):
#             #     continue

#             try:
#                 with open(filepath, "r", encoding="utf-8") as f:
#                     content = f.read()
#             except Exception:
#                 continue

#             content_lower = content.lower()
#             match_score = sum(1 for kw in keywords if kw in content_lower)
#             if match_score == 0:
#                 continue

#             chunks = self._split_into_chunks(content, os.path.basename(filepath))
#             for chunk in chunks:
#                 candidates.append(
#     {
#         "text": chunk["text"],   # <<--- key must be "text"
#         "metadata": {
#             "source": filepath,
#             "chunk_id": chunk["id"],
#             "match_score": match_score,
#         },
#     }
# )

#         candidates.sort(key=lambda x: x["metadata"]["match_score"], reverse=True)
#         return candidates[:top_k]

#     def _split_into_chunks(self, text: str, source: str, max_chars: int = 1500):
#         paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
#         chunks = []
#         current = ""
#         for para in paragraphs:
#             if len(current) + len(para) + 2 > max_chars:
#                 if current:
#                     chunks.append({"id": f"{source}_{len(chunks)}", "text": current})
#                 current = para
#             else:
#                 current += ("\n\n" if current else "") + para
#         if current:
#             chunks.append({"id": f"{source}_{len(chunks)}", "text": current})
#         return chunks


# src/agent/agent_tools/local_directory_tool.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class LocalDirectoryTool:
    """
    Simple keyword-based search over files in a local directory.

    - Walks the directory recursively.
    - Reads text-like files (.txt, .md, .csv, .json, .yaml, .html, etc.).
    - Ranks files by how many times query terms appear.
    - Returns normalized docs: {"text": snippet, "metadata": {...}}.
    """

    def __init__(
        self,
        local_dir: str,
        include_exts: Optional[Sequence[str]] = None,
        top_k: int = 5,
        max_chars: int = 4000,
    ):
        self.local_dir = Path(local_dir)
        self.top_k = top_k
        self.max_chars = max_chars

        # Default set of "text-ish" extensions
        if include_exts is None:
            include_exts = [
                ".txt",
                ".md",
                ".markdown",
                ".rst",
                ".log",
                ".csv",
                ".tsv",
                ".json",
                ".yaml",
                ".yml",
                ".html",
                ".htm",
            ]
        self.include_exts = {ext.lower() for ext in include_exts}

    # ------------- Public API -------------

    def run(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search the local directory for the query and return normalized docs:
        [
          {
            "text": "...snippet...",
            "metadata": {
                "source": "/path/to/file",
                "source_type": "local_file",
                "score": <float>,
            }
          },
          ...
        ]
        """
        k = top_k or self.top_k

        if not self.local_dir.exists() or not self.local_dir.is_dir():
            logger.warning(
                "LocalDirectoryTool: directory does not exist or is not a directory: %s",
                self.local_dir,
            )
            return []

        query = query.strip()
        if not query:
            return []

        terms = self._tokenize(query)
        if not terms:
            return []

        results: List[Dict[str, Any]] = []

        for file_path in self._iter_files():
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.debug("Skipping file %s (read error: %s)", file_path, e)
                continue

            if not text:
                continue

            score = self._score_text(text, terms)
            if score <= 0:
                continue

            snippet = self._make_snippet(text, terms, max_chars=self.max_chars)

            results.append(
                {
                    "text": snippet,
                    "metadata": {
                        "source": str(file_path),
                        "source_type": "local_file",
                        "score": float(score),
                    },
                }
            )

        # Sort descending by score and take top_k
        results.sort(key=lambda d: d["metadata"].get("score", 0.0), reverse=True)
        return results[:k]

    # ------------- Internal helpers -------------

    def _iter_files(self) -> List[Path]:
        """Yield files under local_dir with allowed extensions."""
        paths: List[Path] = []
        for p in self.local_dir.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() in self.include_exts:
                paths.append(p)
        return paths

    def _tokenize(self, text: str) -> List[str]:
        """Very simple tokenization to lowercase words."""
        return [t for t in re.findall(r"\w+", text.lower()) if len(t) > 2]

    def _score_text(self, text: str, terms: List[str]) -> int:
        """
        Simple term frequency scoring: sum of counts of each term.
        """
        lower = text.lower()
        score = 0
        for t in terms:
            if not t:
                continue
            score += lower.count(t)
        return score

    def _make_snippet(self, text: str, terms: List[str], max_chars: int) -> str:
        """
        Build a snippet around the first occurrence of any query term.
        """
        lower = text.lower()
        indices: List[int] = []

        for t in terms:
            idx = lower.find(t)
            if idx != -1:
                indices.append(idx)

        if indices:
            start_idx = min(indices)
        else:
            start_idx = 0

        # Center the snippet around the first hit if possible
        half = max_chars // 2
        start = max(0, start_idx - half)
        end = min(len(text), start + max_chars)

        snippet = text[start:end].strip()

        # Add ellipses if we truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet