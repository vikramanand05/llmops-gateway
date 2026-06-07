from datetime import datetime

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    rpm_limit: int = 60
    tpd_limit: int = 10_000


class APIKeyCreated(BaseModel):
    id: str
    name: str
    api_key: str
    key_prefix: str
    rpm_limit: int
    tpd_limit: int


class APIKeyRead(BaseModel):
    id: str
    name: str
    key_prefix: str
    active: bool
    rpm_limit: int
    tpd_limit: int
    created_at: datetime
    last_used_at: datetime | None = None

    model_config = {"from_attributes": True}


class UsageLogRead(BaseModel):
    id: str
    api_key_id: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    estimated_cost: float
    status: str
    fallback_used: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CostSummary(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost: float
    cost_by_provider: dict[str, float]
    cost_by_api_key: dict[str, float]
    daily_usage_trend: list[dict[str, float | int | str]]
