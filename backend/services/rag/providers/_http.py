"""Shared async HTTP plumbing for provider implementations."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from core.config import settings
from services.rag.providers.base import LLMError

logger = logging.getLogger("cozy.rag.providers")


async def post_json(
    url: str,
    *,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_retries: int | None = None,
) -> httpx.Response:
    """POST JSON with bounded timeout/retries, raising LLMError on failure."""
    timeout = timeout if timeout is not None else settings.LLM_TIMEOUT_SECONDS
    max_retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
    attempts = max_retries + 1
    last_exc: Exception | None = None

    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload, headers=headers or {})
            return resp
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
            last_exc = exc
            logger.warning("Provider request attempt %s/%s failed: %s", attempt + 1, attempts, exc)
            if attempt < attempts - 1:
                await asyncio.sleep(0.3 * (attempt + 1))

    raise LLMError(f"Provider request failed after {attempts} attempt(s): {last_exc}")
