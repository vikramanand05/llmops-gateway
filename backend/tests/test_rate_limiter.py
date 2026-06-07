import pytest

from app.services.rate_limiter import InMemoryRateLimiter, RateLimitExceeded


def test_request_rate_limit():
    limiter = InMemoryRateLimiter()
    limiter.check("key", rpm_limit=1, tpd_limit=100, tokens=1)
    with pytest.raises(RateLimitExceeded):
        limiter.check("key", rpm_limit=1, tpd_limit=100, tokens=1)


def test_daily_token_limit():
    limiter = InMemoryRateLimiter()
    with pytest.raises(RateLimitExceeded):
        limiter.check("key", rpm_limit=10, tpd_limit=5, tokens=6)
