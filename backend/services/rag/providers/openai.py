"""OpenAI-compatible chat completion provider."""

from __future__ import annotations

from core.config import settings
from services.rag.providers._http import post_json
from services.rag.providers.base import LLMError, LLMProvider, ProviderResult


class OpenAIProvider(LLMProvider):
    name = "openai"

    def default_model(self) -> str:
        return settings.OPENAI_MODEL

    def _base_url(self) -> str:
        return "https://api.openai.com/v1/chat/completions"

    async def complete(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise LLMError("OPENAI_API_KEY is not configured")
        resp = await post_json(
            self._base_url(),
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
            raise LLMError(f"OpenAI returned HTTP {resp.status_code}")
        try:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return ProviderResult(text=text, provider=self.name, model=self.model, raw=data)
        except (ValueError, KeyError, IndexError) as exc:
            raise LLMError(f"Malformed OpenAI response: {exc}") from exc
