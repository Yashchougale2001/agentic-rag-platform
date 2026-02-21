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

        logger.info(
            "LocalDirectoryTool initialized: dir=%s, exts=%s, top_k=%d",
            self.local_dir,
            sorted(self.include_exts),
            self.top_k,
        )

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
            logger.info("LocalDirectoryTool.run called with empty query.")
            return []

        terms = self._tokenize(query)
        if not terms:
            logger.info("LocalDirectoryTool: no valid terms in query: %r", query)
            return []

        files = self._iter_files()
        logger.info(
            "LocalDirectoryTool: scanning %d files in %s for query=%r",
            len(files),
            self.local_dir,
            query,
        )

        results: List[Dict[str, Any]] = []

        for file_path in files:
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

        results.sort(key=lambda d: d["metadata"].get("score", 0.0), reverse=True)
        results = results[:k]

        logger.info(
            "LocalDirectoryTool: found %d matching file(s) for query=%r",
            len(results),
            query,
        )
        return results

    # ---------- helpers ---------- #

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
        """Simple term frequency scoring: sum of counts of each term."""
        lower = text.lower()
        score = 0
        for t in terms:
            if not t:
                continue
            score += lower.count(t)
        return score

    def _make_snippet(self, text: str, terms: List[str], max_chars: int) -> str:
        """Build a snippet around the first occurrence of any query term."""
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

        half = max_chars // 2
        start = max(0, start_idx - half)
        end = min(len(text), start + max_chars)

        snippet = text[start:end].strip()

        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet