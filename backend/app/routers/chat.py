import json
import time
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.api_key import APIKey
from app.schemas.chat import ChatChoice, ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatUsage
from app.services.cost import calculate_cost
from app.services.metrics import LLM_COST_TOTAL
from app.services.prompt_renderer import PromptNotFound, apply_prompt_reference
from app.services.provider_clients import ProviderError, estimate_message_tokens
from app.services.rate_limiter import RateLimitExceeded, rate_limiter
from app.services.router import model_router
from app.services.usage import create_usage_log

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ChatCompletionResponse | JSONResponse:
    api_key: APIKey = request.state.api_key
    started = time.perf_counter()
    messages = payload.messages

    try:
        messages = apply_prompt_reference(db, messages, payload.prompt)
    except PromptNotFound as exc:
        create_usage_log(
            db,
            api_key_id=api_key.id,
            provider=payload.provider or "unknown",
            model=payload.model or settings.default_model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency_ms=(time.perf_counter() - started) * 1000,
            estimated_cost=0.0,
            status="failed",
            fallback_used=False,
            error_message=str(exc),
            store_payload=False,
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    estimated_input_tokens = estimate_message_tokens(messages)
    try:
        rate_limiter.check(api_key.key_hash, api_key.rpm_limit, api_key.tpd_limit, estimated_input_tokens)
    except RateLimitExceeded as exc:
        create_usage_log(
            db,
            api_key_id=api_key.id,
            provider=payload.provider or "gateway",
            model=payload.model or settings.default_model,
            prompt_tokens=estimated_input_tokens,
            completion_tokens=0,
            total_tokens=estimated_input_tokens,
            latency_ms=(time.perf_counter() - started) * 1000,
            estimated_cost=0.0,
            status="failed",
            fallback_used=False,
            error_message=str(exc),
            store_payload=False,
        )
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(exc.retry_after)},
            content={"detail": str(exc)},
        )

    status = "success"
    error_message = None
    route = None
    response = None
    try:
        route = await model_router.complete(
            requested_model=payload.model or settings.default_model,
            provider=payload.provider,
            strategy=payload.route_strategy,
            fallback_chain=payload.fallback_chain,
            messages=messages,
            max_tokens=payload.max_tokens,
        )
        result = route.result
        cost = calculate_cost(result.model, result.prompt_tokens, result.completion_tokens)
        LLM_COST_TOTAL.labels(provider=result.provider, model=result.model).inc(cost)
        if route.fallback_used:
            status = "fallback_used"
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(datetime.now(UTC).timestamp()),
            model=result.model,
            provider=result.provider,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=result.content),
                )
            ],
            usage=ChatUsage(
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.prompt_tokens + result.completion_tokens,
            ),
            gateway={
                "latency_ms": round(result.latency_ms, 2),
                "estimated_cost": cost,
                "fallback_used": route.fallback_used,
                "attempted_models": route.attempted_models,
            },
        )
        return response
    except ProviderError as exc:
        status = "failed"
        error_message = str(exc)
        raise HTTPException(status_code=502, detail=error_message) from exc
    finally:
        latency_ms = (time.perf_counter() - started) * 1000
        provider = response.provider if response else payload.provider or "unknown"
        model = response.model if response else payload.model or settings.default_model
        prompt_tokens = response.usage.prompt_tokens if response else estimated_input_tokens
        completion_tokens = response.usage.completion_tokens if response else 0
        total_tokens = response.usage.total_tokens if response else prompt_tokens
        cost = response.gateway["estimated_cost"] if response else 0.0
        store_payload = payload.debug_store_payload or settings.store_prompts_default
        create_usage_log(
            db,
            api_key_id=api_key.id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            estimated_cost=cost,
            status=status,
            fallback_used=bool(route.fallback_used) if route else False,
            error_message=error_message,
            store_payload=store_payload,
            prompt_payload=json.dumps([m.model_dump() for m in messages]) if store_payload else None,
            response_payload=response.model_dump_json() if response and store_payload else None,
        )
