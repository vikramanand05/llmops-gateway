from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class PromptReference(BaseModel):
    prompt_id: str
    version: str
    variables: dict[str, Any] = Field(default_factory=dict)


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    provider: str | None = None
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 512
    stream: bool = False
    route_strategy: Literal["priority", "cost", "latency"] = "priority"
    fallback_chain: list[str] | None = None
    prompt: PromptReference | None = None
    debug_store_payload: bool = False


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    provider: str
    choices: list[ChatChoice]
    usage: ChatUsage
    gateway: dict[str, Any]
