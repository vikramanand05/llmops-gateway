from datetime import UTC, datetime, timedelta

import redis

from app.core.config import settings


class RateLimitExceeded(Exception):
    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self.request_windows: dict[str, list[datetime]] = {}
        self.token_days: dict[str, tuple[str, int]] = {}

    def check(self, key_hash: str, rpm_limit: int, tpd_limit: int, tokens: int) -> None:
        now = datetime.now(UTC)
        minute_ago = now - timedelta(minutes=1)
        window = [ts for ts in self.request_windows.get(key_hash, []) if ts > minute_ago]
        if len(window) >= rpm_limit:
            raise RateLimitExceeded("Requests per minute exceeded", retry_after=60)
        window.append(now)
        self.request_windows[key_hash] = window

        today = now.date().isoformat()
        day, total = self.token_days.get(key_hash, (today, 0))
        if day != today:
            total = 0
        if total + tokens > tpd_limit:
            raise RateLimitExceeded("Daily token limit exceeded", retry_after=3600)
        self.token_days[key_hash] = (today, total + tokens)


class RedisRateLimiter:
    def __init__(self, url: str) -> None:
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def check(self, key_hash: str, rpm_limit: int, tpd_limit: int, tokens: int) -> None:
        minute_key = f"rl:req:{key_hash}"
        count = self.client.incr(minute_key)
        if count == 1:
            self.client.expire(minute_key, 60)
        if count > rpm_limit:
            raise RateLimitExceeded("Requests per minute exceeded", retry_after=60)

        day_key = f"rl:tok:{key_hash}:{datetime.now(UTC).date().isoformat()}"
        total = self.client.incrby(day_key, tokens)
        if total == tokens:
            self.client.expire(day_key, 60 * 60 * 24)
        if total > tpd_limit:
            raise RateLimitExceeded("Daily token limit exceeded", retry_after=3600)


rate_limiter = (
    RedisRateLimiter(settings.redis_url)
    if settings.rate_limit_backend == "redis"
    else InMemoryRateLimiter()
)
