from dataclasses import dataclass

from app.core.config import settings
from app.services.cost import get_model_config
from app.services.metrics import FALLBACK_COUNT, PROVIDER_HEALTH
from app.services.provider_clients import (
    PROVIDER_CLIENTS,
    ProviderError,
    ProviderRateLimit,
    ProviderResult,
    ProviderTimeout,
)
from app.schemas.chat import ChatMessage

DEFAULT_FALLBACK_CHAIN = ["gpt-4o-mini", "gemini-1.5-flash", "claude-3-haiku", "llama3-local"]


@dataclass
class RouteResult:
    result: ProviderResult
    fallback_used: bool
    attempted_models: list[str]


class ModelRouter:
    def resolve_chain(
        self,
        requested_model: str | None,
        provider: str | None,
        strategy: str,
        fallback_chain: list[str] | None,
    ) -> list[str]:
        if fallback_chain:
            chain = fallback_chain
        elif requested_model:
            chain = [requested_model] + [model for model in DEFAULT_FALLBACK_CHAIN if model != requested_model]
        else:
            chain = DEFAULT_FALLBACK_CHAIN.copy()

        if provider and provider != settings.default_provider:
            chain = [model for model in chain if self.provider_for_model(model) in {provider, "mock"}]
        if strategy == "cost":
            return sorted(chain, key=lambda model: self._cost_score(model))
        if strategy == "latency":
            return sorted(chain, key=lambda model: self._latency_score(model))
        return sorted(chain, key=lambda model: self._priority_score(model))

    async def complete(
        self,
        requested_model: str | None,
        provider: str | None,
        strategy: str,
        fallback_chain: list[str] | None,
        messages: list[ChatMessage],
        max_tokens: int,
    ) -> RouteResult:
        attempted: list[str] = []
        chain = self.resolve_chain(requested_model, provider, strategy, fallback_chain)
        last_error: Exception | None = None

        for index, model in enumerate(chain):
            attempted.append(model)
            resolved_provider = provider or self.provider_for_model(model)
            client = PROVIDER_CLIENTS.get(resolved_provider) or PROVIDER_CLIENTS[settings.default_provider]
            try:
                result = await client.complete(model=model, messages=messages, max_tokens=max_tokens)
                PROVIDER_HEALTH.labels(provider=result.provider).set(1)
                if index > 0:
                    FALLBACK_COUNT.labels(from_model=chain[0], to_model=model).inc()
                return RouteResult(result=result, fallback_used=index > 0, attempted_models=attempted)
            except (ProviderTimeout, ProviderRateLimit, ProviderError) as exc:
                PROVIDER_HEALTH.labels(provider=resolved_provider).set(0)
                last_error = exc
                continue

        raise ProviderError(f"All providers failed after attempts {attempted}: {last_error}")

    @staticmethod
    def provider_for_model(model: str) -> str:
        return (get_model_config(model) or {}).get("provider", settings.default_provider)

    @staticmethod
    def _priority_score(model: str) -> int:
        return int((get_model_config(model) or {}).get("priority", 999))

    @staticmethod
    def _latency_score(model: str) -> float:
        return float((get_model_config(model) or {}).get("expected_latency_ms", 999999))

    @staticmethod
    def _cost_score(model: str) -> float:
        config = get_model_config(model) or {}
        return float(config.get("prompt_per_1k", 999)) + float(config.get("completion_per_1k", 999))


model_router = ModelRouter()
