"""
Canonical Ollama client for apps.ai.clients.
api/apps/ai/clients/ollama_client.py
"""
from __future__ import annotations

import json
import logging
import os
from typing import Generator

import requests

logger = logging.getLogger(__name__)

_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "120"))


class OllamaClientError(Exception):
    """Base exception for all Ollama client errors."""


class OllamaConnectionError(OllamaClientError):
    """Raised when the Ollama server is unreachable."""


class OllamaClient:
    def __init__(
        self,
        base_url: str = _BASE_URL,
        model: str = _MODEL,
        timeout: int = _TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session = requests.Session()

    def complete(self, prompt: str, **kwargs) -> str:
        options = {k: v for k, v in kwargs.items() if k not in ("model",)}
        payload: dict = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
        }
        if options:
            payload["options"] = options
        try:
            response = self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.ConnectionError as exc:
            raise OllamaConnectionError(
                "Cannot reach Ollama server. Is ollama serve running?"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise OllamaClientError(
                f"Ollama request timed out after {self.timeout}s."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise OllamaClientError(f"Ollama HTTP error: {exc}") from exc

    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": True,
        }
        try:
            response = self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    yield chunk.get("response", "")
        except requests.exceptions.ConnectionError as exc:
            raise OllamaConnectionError(
                "Cannot reach Ollama server. Is ollama serve running?"
            ) from exc

    def health_check(self) -> dict:
        try:
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            response.raise_for_status()
            models = [m["name"] for m in response.json().get("models", [])]
            model_available = any(
                m == self.model or m.startswith(f"{self.model}:")
                for m in models
            )
            return {
                "status": "ok",
                "model_available": model_available,
                "error": (
                    None
                    if model_available
                    else f"Model not pulled. Run: ollama pull {self.model}"
                ),
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "model_available": False,
                "error": "Ollama server unreachable.",
            }
