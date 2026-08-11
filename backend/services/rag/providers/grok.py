"""xAI Grok provider (OpenAI-compatible API)."""

from __future__ import annotations

from core.config import settings
from services.rag.providers._http import post_json
from services.rag.providers.base import LLMError, LLMProvider, ProviderResult


class GrokProvider(LLMProvider):
    name = "grok"

    def default_model(self) -> str:
        return settings.GROK_MODEL

    async def complete(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        api_key = settings.GROK_API_KEY
        if not api_key:
            raise LLMError("GROK_API_KEY is not configured")
        resp = await post_json(
            "https://api.x.ai/v1/chat/completions",
            payload={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if resp.status_code != 200:
            raise LLMError(f"Grok returned HTTP {resp.status_code}")
        try:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return ProviderResult(text=text, provider=self.name, model=self.model, raw=data)
        except (ValueError, KeyError, IndexError) as exc:
            raise LLMError(f"Malformed Grok response: {exc}") from exc
