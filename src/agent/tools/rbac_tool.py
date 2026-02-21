# src/agent/tools/rbac_tool.py

from __future__ import annotations

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class RBACFilterTool:
    """
    Filter retrieved docs based on user role and metadata.

    Expected metadata fields (you can adjust):
      - visibility: "public" | "hr" | "admin" | "private"
      - owner_user_id: str (for private docs)
    """

    def __init__(self):
        pass

    def filter_docs(
        self,
        docs: List[Dict[str, Any]],
        *,
        user_id: str,
        role: str,
    ) -> List[Dict[str, Any]]:
        allowed: List[Dict[str, Any]] = []
        for d in docs:
            meta = d.get("metadata", {}) or {}
            visibility = (meta.get("visibility") or "public").lower()
            owner_id = meta.get("owner_user_id")

            if self._is_allowed(visibility, owner_id, user_id, role):
                allowed.append(d)

        if len(allowed) < len(docs):
            logger.info(
                "RBAC filtered %d/%d docs for user %s (%s)",
                len(docs) - len(allowed),
                len(docs),
                user_id,
                role,
            )
        return allowed

    def _is_allowed(
        self,
        visibility: str,
        owner_id: str | None,
        user_id: str,
        role: str,
    ) -> bool:
        role = role.lower()

        # Admin: everything
        if role == "admin":
            return True

        # HR: all public + hr docs (and maybe private if policy says so)
        if role == "hr":
            if visibility in ("public", "hr"):
                return True
            # Optionally, HR can see all private (depends on your policy)
            if visibility == "private":
                return True
            return False

        # Employee: only public docs + their own private docs
        if role == "employee":
            if visibility == "public":
                return True
            if visibility == "private" and owner_id == user_id:
                return True
            return False

        # Unknown role: safest is public only
        return visibility == "public"