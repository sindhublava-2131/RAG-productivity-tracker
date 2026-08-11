"""Google Gemini provider."""

from __future__ import annotations

from core.config import settings
from services.rag.providers._http import post_json
from services.rag.providers.base import LLMError, LLMProvider, ProviderResult


class GeminiProvider(LLMProvider):
    name = "gemini"

    def default_model(self) -> str:
        return settings.GEMINI_MODEL

    async def complete(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise LLMError("GEMINI_API_KEY is not configured")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        # Send the key in a header, not a URL query parameter.
        resp = await post_json(
            url,
            payload={
                "contents": [
                    {"parts": [{"text": f"{system_prompt}\n\nUser Question: {user_prompt}"}]}
                ]
            },
            headers={"x-goog-api-key": api_key},
        )
        if resp.status_code != 200:
            raise LLMError(f"Gemini returned HTTP {resp.status_code}")
        try:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return ProviderResult(text=text, provider=self.name, model=self.model, raw=data)
        except (ValueError, KeyError, IndexError) as exc:
            raise LLMError(f"Malformed Gemini response: {exc}") from exc
