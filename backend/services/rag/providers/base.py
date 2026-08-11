"""LLM provider base interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResult:
    text: str
    provider: str
    model: str
    raw: dict | None = None


class LLMError(RuntimeError):
    """Raised when a provider call fails (timeout, network, malformed response)."""


class LLMProvider(ABC):
    name: str = "base"
    model: str

    def __init__(self, model: str | None = None) -> None:
        self.model = model or self.default_model()

    @abstractmethod
    def default_model(self) -> str:  # pragma: no cover - abstract
        ...

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        """Generate a completion from the given prompts. Must raise LLMError on failure."""
        raise NotImplementedError


class FakeLLMProvider(LLMProvider):
    """Deterministic provider for tests — never touches the network."""

    name = "fake"
    max_retries = 0

    def __init__(self, model: str | None = None, canned: str | None = None) -> None:
        super().__init__(model=model)
        self.canned = canned
        self.call_count = 0

    def default_model(self) -> str:
        return "fake-model"

    async def complete(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        self.call_count += 1
        if self.canned is None:
            return ProviderResult(
                text=f"[fake-answer] processed: {user_prompt[:80]}",
                provider=self.name,
                model=self.model,
            )
        return ProviderResult(text=self.canned, provider=self.name, model=self.model)


class FailingLLMProvider(FakeLLMProvider):
    """Provider that always raises LLMError — simulates provider failure."""

    def __init__(self, model: str | None = None) -> None:
        super().__init__(model=model)
        self.name = "failing"

    async def complete(self, system_prompt: str, user_prompt: str) -> ProviderResult:
        raise LLMError("simulated provider failure")
