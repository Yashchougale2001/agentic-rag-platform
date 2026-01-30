import requests
from typing import List, Dict, Optional
from src.utils.config_loader import load_model_config


class OllamaClient:
    """
    Simple client for local Ollama TinyLLaMA.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        cfg = load_model_config()
        self.model_name = cfg.get("llm", {}).get("ollama", {}).get("model_name", "tinyllama")

    def generate(
        self, system_prompt: str, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.1
    ) -> str:
        """
        messages: list of {"role": "user"/"assistant"/"system", "content": "..."}
        """
        # Ollama chat API
        payload = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "options": {"temperature": temperature},
            "stream": False,
        }
        resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]