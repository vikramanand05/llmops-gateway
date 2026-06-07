from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.api_key import APIKey
from app.models.usage import UsageLog


def create_usage_log(db: Session, **kwargs) -> UsageLog:
    log = UsageLog(**kwargs)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def summarize_costs(db: Session) -> dict:
    logs = db.query(UsageLog).all()
    cost_by_provider: dict[str, float] = defaultdict(float)
    cost_by_api_key: dict[str, float] = defaultdict(float)
    daily: dict[str, dict[str, float | int | str]] = {}

    for log in logs:
        cost_by_provider[log.provider] += log.estimated_cost
        key_name = db.query(APIKey).filter(APIKey.id == log.api_key_id).first()
        cost_by_api_key[key_name.name if key_name else log.api_key_id] += log.estimated_cost
        day = log.created_at.date().isoformat()
        daily.setdefault(day, {"date": day, "requests": 0, "tokens": 0, "cost": 0.0})
        daily[day]["requests"] += 1
        daily[day]["tokens"] += log.total_tokens
        daily[day]["cost"] += log.estimated_cost

    total_requests, total_tokens, total_cost = db.query(
        func.count(UsageLog.id), func.coalesce(func.sum(UsageLog.total_tokens), 0), func.coalesce(func.sum(UsageLog.estimated_cost), 0.0)
    ).one()

    return {
        "total_requests": int(total_requests),
        "total_tokens": int(total_tokens),
        "total_cost": round(float(total_cost), 8),
        "cost_by_provider": {key: round(value, 8) for key, value in cost_by_provider.items()},
        "cost_by_api_key": {key: round(value, 8) for key, value in cost_by_api_key.items()},
        "daily_usage_trend": list(sorted(daily.values(), key=lambda row: str(row["date"]))),
        "generated_at": datetime.now(UTC).isoformat(),
    }
