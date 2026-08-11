"""Ollama LLM provider."""

from __future__ import annotations

from core.config import settings
from services.rag.providers._http import post_json
from services.rag.providers.base import LLMError, LLMProvider, ProviderResult


class OllamaProvider(LLMProvider):
    name = "ollama"

    def default_model(self) -> str:
        return settings.OLLAMA_MODEL

    async def complete(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        url = f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate"
        resp = await post_json(
            url,
            payload={
                "model": self.model,
                "prompt": f"{system_prompt}\n\nUser Question: {user_prompt}",
                "stream": False,
            },
        )
        if resp.status_code != 200:
            raise LLMError(f"Ollama returned HTTP {resp.status_code}")
        try:
            data = resp.json()
            text = data.get("response")
            if not text:
                raise LLMError("Ollama response missing 'response' field")
            return ProviderResult(text=text, provider=self.name, model=self.model, raw=data)
        except ValueError as exc:
            raise LLMError(f"Malformed Ollama response: {exc}") from exc
