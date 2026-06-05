"""
Canonical Ollama client.
api/api/ai/clients/ollama_client.py

Single source of truth — providers.py and any other module imports from here.
Uses requests with explicit timeouts. Streams disabled for simplicity;
enable streaming only via Celery tasks, not inside the request cycle.
"""
from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)

_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
_OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "120"))


class OllamaClient:
    """
    Thin, stateless wrapper around the Ollama /api/generate endpoint.
    Instantiated once per provider instance (see providers.py singleton).
    """

    def __init__(
        self,
        base_url: str = _OLLAMA_BASE_URL,
        model: str = _OLLAMA_MODEL,
        timeout: int = _OLLAMA_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str, **kwargs) -> str:
        """
        Send a prompt and return the full response string.
        Raises requests.HTTPError on non-2xx responses.
        """
        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
        }
        url = f"{self.base_url}/api/generate"
        logger.debug("Ollama request: model=%s url=%s", payload["model"], url)

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json().get("response", "")
