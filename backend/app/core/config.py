from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "llmops-gateway"
    environment: str = "development"
    database_url: str = "sqlite:///./llmops_gateway.db"
    redis_url: str = "redis://redis:6379/0"
    rate_limit_backend: str = "memory"
    admin_token: str = "change-me-admin-token"
    default_provider: str = "mock"
    default_model: str = "gpt-4o-mini"
    request_timeout_seconds: float = 20.0
    store_prompts_default: bool = False
    auto_create_tables: bool = True
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    ollama_base_url: str = "http://ollama:11434"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
