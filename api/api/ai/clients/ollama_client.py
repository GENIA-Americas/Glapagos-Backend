"""
Glápagos AI Client — Ollama Integration
apps/ai/clients/ollama_client.py

Adds local LLM inference via Ollama so users can run models
without an external API key. Follows the same interface pattern
as the existing OpenAI hook, pluggable via env var.

Usage:
    AI_PROVIDER=ollama
    OLLAMA_BASE_URL=http://localhost:11434  (default)
    OLLAMA_MODEL=llama3                     (default)

Drop-in compatible with the Glápagos AI provider interface.
"""

from __future__ import annotations

import os
import logging
from typing import Any, Generator

import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (resolved from environment at import time)
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT: int = int(os.environ.get("OLLAMA_TIMEOUT", "120"))


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class OllamaClientError(Exception):
    """Base exception for OllamaClient errors."""


class OllamaConnectionError(OllamaClientError):
    """Raised when the Ollama server cannot be reached."""


class OllamaModelError(OllamaClientError):
    """Raised when the requested model is unavailable."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class OllamaClient:
    """
    Thin wrapper around the Ollama REST API for local LLM inference.

    Implements the Glápagos AI provider interface:
        - complete(prompt, **kwargs) -> str
        - stream(prompt, **kwargs)   -> Generator[str, None, None]
        - health_check()             -> dict
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    # ------------------------------------------------------------------
    # Public interface (matches Glápagos AI provider contract)
    # ------------------------------------------------------------------

    def complete(self, prompt: str, **kwargs: Any) -> str:
        """
        Send a prompt and return the full response as a string.

        Args:
            prompt: The input text.
            **kwargs: Forwarded to the Ollama /api/generate payload
                      (e.g. temperature, top_p, system, context).

        Returns:
            The model's response as a plain string.

        Raises:
            OllamaConnectionError: If the Ollama server is unreachable.
            OllamaClientError: For any other API-level error.
        """
        payload = self._build_payload(prompt, stream=False, **kwargs)
        try:
            response = self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except ConnectionError as exc:
            raise OllamaConnectionError(
                f"Cannot reach Ollama at {self.base_url}. "
                "Is the server running? (ollama serve)"
            ) from exc
        except Timeout as exc:
            raise OllamaClientError(
                f"Ollama request timed out after {self.timeout}s."
            ) from exc
        except RequestException as exc:
            raise OllamaClientError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        return data.get("response", "")

    def stream(self, prompt: str, **kwargs: Any) -> Generator[str, None, None]:
        """
        Stream the model's response token by token.

        Yields:
            Individual response tokens as strings.

        Raises:
            OllamaConnectionError: If the Ollama server is unreachable.
            OllamaClientError: For any other API-level error.
        """
        import json as _json

        payload = self._build_payload(prompt, stream=True, **kwargs)
        try:
            with self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = _json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
        except ConnectionError as exc:
            raise OllamaConnectionError(
                f"Cannot reach Ollama at {self.base_url}."
            ) from exc
        except RequestException as exc:
            raise OllamaClientError(f"Ollama stream failed: {exc}") from exc

    def health_check(self) -> dict:
        """
        Check whether the Ollama server is reachable and the configured
        model is available.

        Returns:
            {
                "status": "ok" | "error",
                "base_url": str,
                "model": str,
                "model_available": bool,
                "error": str | None,
            }
        """
        result: dict[str, Any] = {
            "status": "error",
            "base_url": self.base_url,
            "model": self.model,
            "model_available": False,
            "error": None,
        }
        try:
            resp = self._session.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            model_available = any(
                self.model in name for name in models
            )
            result.update(
                status="ok",
                model_available=model_available,
                error=None if model_available
                      else f"Model '{self.model}' not pulled. Run: ollama pull {self.model}",
            )
        except ConnectionError:
            result["error"] = (
                f"Ollama server unreachable at {self.base_url}. "
                "Start it with: ollama serve"
            )
        except Exception as exc:  # noqa: BLE001
            result["error"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_payload(self, prompt: str, stream: bool, **kwargs: Any) -> dict:
        payload: dict[str, Any] = {
            "model": kwargs.pop("model", self.model),
            "prompt": prompt,
            "stream": stream,
        }
        # Optional Ollama parameters passed through transparently
        for key in ("system", "template", "context", "options"):
            if key in kwargs:
                payload[key] = kwargs.pop(key)
        # Remaining kwargs go into the options sub-dict (temperature, top_p, …)
        if kwargs:
            payload.setdefault("options", {}).update(kwargs)
        return payload

    def __repr__(self) -> str:
        return f"OllamaClient(base_url={self.base_url!r}, model={self.model!r})"


# ---------------------------------------------------------------------------
# Provider factory — used by the Glápagos AI provider registry
# ---------------------------------------------------------------------------

def get_client(**kwargs: Any) -> OllamaClient:
    """
    Factory function called by the Glápagos AI provider registry
    when AI_PROVIDER=ollama.

    Environment variables are the primary configuration mechanism;
    kwargs allow programmatic overrides in tests.
    """
    return OllamaClient(**kwargs)
