import os
import logging
from typing import List, Dict

from src.utils.config_loader import load_settings, load_model_config
from src.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class LLMGenerator:
    def __init__(self):
        self.settings = load_settings()
        self.model_cfg = load_model_config()
        self.providers = self.settings.get("llm", {}).get("provider_priority", ["groq", "ollama"])
        self.max_tokens = self.settings.get("llm", {}).get("max_tokens", 512)
        self.temperature = self.settings.get("llm", {}).get("temperature", 0.1)

        self._groq_client = None
        self._ollama_client = None

    def _get_groq_client(self):
        if self._groq_client is not None:
            return self._groq_client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        try:
            from groq import Groq

            self._groq_client = Groq(api_key=api_key)
            return self._groq_client
        except Exception as e:
            logger.warning("Failed to init Groq client: %s", e)
            return None

    def _get_ollama_client(self):
        if self._ollama_client is None:
            self._ollama_client = OllamaClient()
        return self._ollama_client

    def _call_groq(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> str:
        client = self._get_groq_client()
        if not client:
            raise RuntimeError("Groq client not available")

        model_name = self.model_cfg.get("llm", {}).get("groq", {}).get(
            "model_name", "llama-3.3-70b-versatile"
        )

        logger.info("Using Groq LLM with model %s", model_name)
        self.last_provider_used = ("groq", model_name)

        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return resp.choices[0].message.content

    # def _call_ollama(
    #     self, system_prompt: str, messages: List[Dict[str, str]]
    # ) -> str:
    #     client = self._get_ollama_client()
    #     model_name = client.model_name

    #     logger.info("Using Ollama LLM (TinyLLaMA) with model %s", model_name)
    #     self.last_provider_used = ("ollama", model_name)
    #     return client.generate(
    #         system_prompt=system_prompt,
    #         messages=messages,
    #         max_tokens=self.max_tokens,
    #         temperature=self.temperature,
    #     )

    def generate_text(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 128,
        temperature: float = 0.1,
    ) -> str:
        """
        Generic helper for short, non-RAG generations (e.g., query rewriting).
        Uses the same provider priority and fallback logic as generate_answer.
        """
        messages = [{"role": "user", "content": user_content}]
        last_error = None

        for provider in self.providers:
            try:
                if provider == "groq":
                    if not self._get_groq_client():
                        continue
                    old_max, old_temp = self.max_tokens, self.temperature
                    self.max_tokens, self.temperature = max_tokens, temperature
                    try:
                        return self._call_groq(system_prompt, messages)
                    finally:
                        self.max_tokens, self.temperature = old_max, old_temp

                # elif provider == "ollama":
                #     # Ollama is local; assume always available once client is created
                #     old_max, old_temp = self.max_tokens, self.temperature
                #     self.max_tokens, self.temperature = max_tokens, temperature
                #     try:
                #         return self._call_ollama(system_prompt, messages)
                #     finally:
                #         self.max_tokens, self.temperature = old_max, old_temp

            except Exception as e:
                logger.warning("LLM provider %s failed in generate_text: %s", provider, e)
                last_error = e

        raise RuntimeError(f"No LLM provider available for generate_text. Last error: {last_error}")

    def generate_answer(
        self,
        question: str,
        context_docs: List[Dict],
        hr_domain: str = "it_assets",
    ) -> str:
        """
        RAG-style prompt. Only use context_docs as knowledge.
        """
        system_prompt = (
            "You are an IT assets assistant. "
            "Answer using ONLY the provided context. "
            "If the context does not contain the answer, say you don't know and "
            "suggest that the user ingest more IT assets documents. "
            "Be concise and cite sources as [source: <filename or url>]. "
            "Do not use outside knowledge."
            "Do not repeat the word ‘Question’ or ‘Context’ in your answer."
            "Do not restate the question; answer directly in prose or bullet points."
        )

        # Build context string
        context_strs = []
        for i, d in enumerate(context_docs):
            src = d["metadata"].get("source", "unknown")
            context_strs.append(
                f"Document {i+1} (source: {src}):\n{d['text']}\n"
            )
        context_block = "\n\n".join(context_strs) if context_strs else "No context."

        user_content = (
            f"Question:\n{question}\n\n"
            f"Context:\n{context_block}\n\n"
            "Now answer the question using only this context."
        )

        messages = [{"role": "user", "content": user_content}]

        # Try providers in priority order, fall back if needed
        last_error = None
        for provider in self.providers:
            try:
                if provider == "groq":
                    if not self._get_groq_client():
                        continue
                    return self._call_groq(system_prompt, messages)
                # elif provider == "ollama":
                #     return self._call_ollama(system_prompt, messages)
            except Exception as e:
                logger.warning("LLM provider %s failed: %s", provider, e)
                last_error = e

        raise RuntimeError(f"No LLM provider available. Last error: {last_error}")