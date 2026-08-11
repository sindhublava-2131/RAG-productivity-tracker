"""Provider registry / factory."""

from __future__ import annotations

import logging

from core.config import settings
from services.rag.providers.base import LLMProvider
from services.rag.providers.gemini import GeminiProvider
from services.rag.providers.grok import GrokProvider
from services.rag.providers.ollama import OllamaProvider
from services.rag.providers.openai import OpenAIProvider

logger = logging.getLogger("cozy.rag.providers")

_PROVIDER_CLASSES: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "grok": GrokProvider,
}


def get_provider(provider_name: str | None, model_name: str | None = None) -> LLMProvider:
    name = (provider_name or settings.RAG_PROVIDER or "ollama").lower()
    cls = _PROVIDER_CLASSES.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider '{name}'. Valid: {sorted(_PROVIDER_CLASSES)}"
        )
    model = model_name or (settings.RAG_MODEL or None)
    return cls(model=model)
