from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@lru_cache
def load_pricing() -> dict[str, Any]:
    pricing_path = Path(__file__).resolve().parents[1] / "core" / "pricing.yaml"
    with pricing_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def get_model_config(model: str) -> dict[str, Any] | None:
    return load_pricing().get("models", {}).get(model)


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    config = get_model_config(model)
    if not config:
        return 0.0
    prompt_cost = (prompt_tokens / 1000) * float(config["prompt_per_1k"])
    completion_cost = (completion_tokens / 1000) * float(config["completion_per_1k"])
    return round(prompt_cost + completion_cost, 8)
