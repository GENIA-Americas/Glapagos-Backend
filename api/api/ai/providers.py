"""
Glapagos AI Provider Registry
api/api/ai/providers.py

Responsibilities:
  - Define the AIProvider protocol (structural interface).
  - Implement OpenAI and Ollama providers.
  - Expose get_provider() which returns a module-level singleton —
    one client instance per process, not one per request.

Adding a new provider:
  1. Implement the AIProvider protocol.
  2. Register it in _PROVIDER_REGISTRY.
  3. Set AI_PROVIDER=<key> in the environment.
"""
from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

_AI_PROVIDER_KEY = os.environ.get("AI_PROVIDER", "openai").lower()

# Module-level singleton — populated once on first call to get_provider().
_provider_instance: "AIProvider | None" = None


@runtime_checkable
class AIProvider(Protocol):
    """
    Every provider must implement complete().
    system is optional; not all backends support system prompts natively.
    """

    def complete(self, prompt: str, *, system: str = "", **kwargs) -> str: ...


class OpenAIProvider:
    def __init__(self) -> None:
        import openai
        from django.conf import settings

        self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAIProvider initialised")

    def complete(self, prompt: str, *, system: str = "", **kwargs) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion = self._client.chat.completions.create(
            model=kwargs.get("model", "gpt-4o-mini"),
            messages=messages,
        )
        return completion.choices[0].message.content or ""


class OllamaProvider:
    def __init__(self) -> None:
        from api.ai.clients.ollama_client import OllamaClient

        self._client = OllamaClient()
        logger.info("OllamaProvider initialised (model=%s)", self._client.model)

    def complete(self, prompt: str, *, system: str = "", **kwargs) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        return self._client.complete(full_prompt, **kwargs)


_PROVIDER_REGISTRY: dict[str, type] = {
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_provider() -> AIProvider:
    """
    Return the module-level provider singleton.
    Thread-safe for reads; the write-once pattern is safe under Django's
    multi-threaded WSGI servers because the cost of a duplicate init is
    a discarded object, not a corrupted state.
    """
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    provider_class = _PROVIDER_REGISTRY.get(_AI_PROVIDER_KEY)
    if provider_class is None:
        logger.warning(
            "Unknown AI_PROVIDER=%r — falling back to OpenAI", _AI_PROVIDER_KEY
        )
        provider_class = OpenAIProvider

    _provider_instance = provider_class()
    return _provider_instance
