# src/processing/query_rewriter.py
from typing import List, Dict, Optional

from src.llm.generator import LLMGenerator


class QueryRewriter:
    """
    Uses the LLM to rewrite user questions into explicit, standalone
    search queries, optionally using conversation history.
    """

    def __init__(self, llm: Optional[LLMGenerator] = None, max_history: int = 6):
        self.llm = llm or LLMGenerator()
        self.max_history = max_history

    def rewrite(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        history: list of {"role": "user"/"assistant", "content": "..."}.
        Returns a rewritten query string. If rewriting fails, returns the original question.
        """
        history = history or []
        recent = history[-self.max_history :]

        if recent:
            history_str = "\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
                for m in recent
            )
        else:
            history_str = "No previous conversation."

        system_prompt = (
            "You are a query rewriting assistant for a retrieval-augmented generation (RAG) system. "
            "Your job is to rewrite user questions into explicit, standalone search queries that are "
            "optimal for retrieving relevant technical documentation.\n"
            "- Do NOT answer the question.\n"
            "- Do NOT add information that was not implied by the user.\n"
            "- Use any relevant context from the conversation history.\n"
            "- Output ONLY the rewritten query, with no explanation or commentary."
        )

        user_content = (
            f"Conversation history:\n{history_str}\n\n"
            f"User's latest question:\n{question}\n\n"
            "Rewrite the user's latest question as a single, clear, standalone search query:"
        )

        try:
            rewritten = self.llm.generate_text(
                system_prompt=system_prompt,
                user_content=user_content,
                max_tokens=64,
                temperature=0.1,
            )
            return rewritten.strip()
        except Exception:
            # On any error, fall back to the original question
            return question