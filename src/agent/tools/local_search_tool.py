
# src/agent/tools/local_search_tool.py
import os
import glob
import re
from typing import List, Dict, Any


class LocalSearchTool:
    """
    Simple keyword-based search over a local directory of text files.
    Used as a fallback when vector search finds nothing.
    """

    def __init__(self, local_dir: str):
        self.local_dir = local_dir
        os.makedirs(local_dir, exist_ok=True)

    def run(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        if not os.path.exists(self.local_dir):
            return []

        # Better tokenization: remove punctuation, keep word chars only
        tokens = re.findall(r"\w+", query.lower())
        keywords = [t for t in tokens if len(t) > 2]

        candidates: List[Dict[str, Any]] = []

        for filepath in glob.glob(f"{self.local_dir}/**/*.*", recursive=True):
            if os.path.isdir(filepath):
                continue

            # Optional: limit to text-like files (uncomment if needed)
            # if not filepath.lower().endswith((".txt", ".md", ".csv")):
            #     continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            content_lower = content.lower()
            match_score = sum(1 for kw in keywords if kw in content_lower)
            if match_score == 0:
                continue

            chunks = self._split_into_chunks(content, os.path.basename(filepath))
            for chunk in chunks:
                candidates.append(
    {
        "text": chunk["text"],   # <<--- key must be "text"
        "metadata": {
            "source": filepath,
            "chunk_id": chunk["id"],
            "match_score": match_score,
        },
    }
)

        candidates.sort(key=lambda x: x["metadata"]["match_score"], reverse=True)
        return candidates[:top_k]

    def _split_into_chunks(self, text: str, source: str, max_chars: int = 1500):
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) + 2 > max_chars:
                if current:
                    chunks.append({"id": f"{source}_{len(chunks)}", "text": current})
                current = para
            else:
                current += ("\n\n" if current else "") + para
        if current:
            chunks.append({"id": f"{source}_{len(chunks)}", "text": current})
        return chunks

