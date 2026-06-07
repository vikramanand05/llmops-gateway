import pytest

from app.schemas.chat import ChatMessage
from app.services.provider_clients import ProviderError, ProviderResult
from app.services.router import ModelRouter


def test_route_by_cost_prefers_local_llama():
    router = ModelRouter()
    chain = router.resolve_chain(None, None, "cost", None)
    assert chain[0] == "llama3-local"


@pytest.mark.asyncio
async def test_fallback_logic_when_primary_model_fails(monkeypatch):
    class FlakyClient:
        provider = "mock"

        async def complete(self, model, messages, max_tokens):
            if model == "gpt-4o-mini":
                raise ProviderError("primary failed")
            return ProviderResult(
                provider="mock",
                model=model,
                content="fallback response",
                latency_ms=5,
                prompt_tokens=10,
                completion_tokens=3,
            )

    monkeypatch.setattr("app.services.router.PROVIDER_CLIENTS", {"mock": FlakyClient()})
    router = ModelRouter()
    result = await router.complete(
        requested_model="gpt-4o-mini",
        provider="mock",
        strategy="priority",
        fallback_chain=["gpt-4o-mini", "gemini-1.5-flash"],
        messages=[ChatMessage(role="user", content="hello")],
        max_tokens=64,
    )
    assert result.result.model == "gemini-1.5-flash"
    assert result.fallback_used is True
