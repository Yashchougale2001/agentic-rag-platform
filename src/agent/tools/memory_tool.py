# src/agent/tools/memory_tool.py

from __future__ import annotations

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileMemoryStore:
    """
    Simple file-based memory store.

    - Conversations: data/memory/conversations/<user_id>.jsonl
    - Profiles:      data/memory/profiles.json
    """

    def __init__(self, base_dir: str = "data/memory"):
        self.base_dir = Path(base_dir)
        self.conv_dir = self.base_dir / "conversations"
        self.profile_path = self.base_dir / "profiles.json"
        self.conv_dir.mkdir(parents=True, exist_ok=True)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        if not self.profile_path.exists():
            self.profile_path.write_text("{}", encoding="utf-8")

    # -------- Conversation memory -------- #

    def load_conversation(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        path = self.conv_dir / f"{user_id}.jsonl"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        recent = lines[-limit:]
        return [json.loads(l) for l in recent if l.strip()]

    def append_turn(self, user_id: str, question: str, answer: str) -> None:
        path = self.conv_dir / f"{user_id}.jsonl"
        rec = {
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "answer": answer,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # -------- User profile memory -------- #

    def load_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            raw = json.loads(self.profile_path.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        return raw.get(user_id, {})

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> None:
        try:
            raw = json.loads(self.profile_path.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        profile = raw.get(user_id, {})
        profile.update(updates)
        raw[user_id] = profile
        self.profile_path.write_text(
            json.dumps(raw, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class MemoryTool:
    """
    Wrapper around FileMemoryStore to use inside LangGraph.
    """

    def __init__(self, store: Optional[FileMemoryStore] = None):
        self.store = store or FileMemoryStore()

    def load(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        conv = self.store.load_conversation(user_id, limit=limit)
        profile = self.store.load_profile(user_id)
        return {"conversation_history": conv, "user_profile": profile}

    def save_turn(self, user_id: str, question: str, answer: str):
        self.store.append_turn(user_id, question, answer)

    def update_profile(self, user_id: str, updates: Dict[str, Any]):
        self.store.update_profile(user_id, updates)