import time
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import settings
from app.schemas.chat import ChatMessage


class ProviderError(Exception):
    pass


class ProviderRateLimit(ProviderError):
    pass


class ProviderTimeout(ProviderError):
    pass


@dataclass
class ProviderResult:
    provider: str
    model: str
    content: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int


class ProviderClient(Protocol):
    provider: str

    async def complete(self, model: str, messages: list[ChatMessage], max_tokens: int) -> ProviderResult:
        ...


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) + len(text) // 24)


def estimate_message_tokens(messages: list[ChatMessage]) -> int:
    return sum(estimate_tokens(message.content) + 4 for message in messages)


class MockProviderClient:
    provider = "mock"

    async def complete(self, model: str, messages: list[ChatMessage], max_tokens: int) -> ProviderResult:
        started = time.perf_counter()
        joined = " ".join(message.content for message in messages)
        lowered = joined.lower()
        if "force_timeout" in lowered:
            raise ProviderTimeout("Mock timeout triggered")
        if "force_rate_limit" in lowered:
            raise ProviderRateLimit("Mock rate limit triggered")
        if "force_fail" in lowered:
            raise ProviderError("Mock provider failure triggered")

        last_user = next((m.content for m in reversed(messages) if m.role == "user"), joined)
        content = (
            "This is a mock LLM response from LLMOps Gateway. "
            f"Provider routing worked for model {model}. "
            f"User asked: {last_user[:180]}"
        )
        prompt_tokens = estimate_message_tokens(messages)
        completion_tokens = min(max_tokens, estimate_tokens(content))
        return ProviderResult(
            provider=self.provider,
            model=model,
            content=content,
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


class OpenAICompatibleClient:
    provider = "openai"

    async def complete(self, model: str, messages: list[ChatMessage], max_tokens: int) -> ProviderResult:
        if not settings.openai_api_key:
            return await MockProviderClient().complete(model, messages, max_tokens)
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": model,
                    "messages": [message.model_dump() for message in messages],
                    "max_tokens": max_tokens,
                },
            )
        if response.status_code == 429:
            raise ProviderRateLimit(response.text)
        if response.status_code >= 500:
            raise ProviderError(response.text)
        response.raise_for_status()
        data = response.json()
        return ProviderResult(
            provider=self.provider,
            model=model,
            content=data["choices"][0]["message"]["content"],
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=data.get("usage", {}).get("prompt_tokens", estimate_message_tokens(messages)),
            completion_tokens=data.get("usage", {}).get("completion_tokens", 0),
        )


class AnthropicCompatibleClient(MockProviderClient):
    provider = "anthropic"


class GeminiCompatibleClient(MockProviderClient):
    provider = "gemini"


class OllamaCompatibleClient(MockProviderClient):
    provider = "ollama"


PROVIDER_CLIENTS: dict[str, ProviderClient] = {
    "mock": MockProviderClient(),
    "openai": OpenAICompatibleClient(),
    "anthropic": AnthropicCompatibleClient(),
    "gemini": GeminiCompatibleClient(),
    "ollama": OllamaCompatibleClient(),
}
