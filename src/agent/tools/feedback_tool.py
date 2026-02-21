# src/agent/tools/feedback_tool.py

from __future__ import annotations

from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeedbackTool:
    """
    Append feedback entries to a JSONL file (for offline evaluation).
    """

    def __init__(self, path: str = "logs/feedback.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def submit(
        self,
        *,
        user_id: str,
        role: str,
        question: str,
        answer: str,
        rating: int,  # e.g. -1, 0, 1 or 1–5
        comment: Optional[str] = None,
        context_sources: Optional[List[str]] = None,
    ) -> None:
        record: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "role": role,
            "question": question,
            "answer": answer,
            "rating": rating,
            "comment": comment,
            "sources": context_sources or [],
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info("Feedback recorded for user %s with rating %s", user_id, rating)