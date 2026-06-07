from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.security import hash_api_key
from app.db.session import SessionLocal
from app.models.api_key import APIKey

PROTECTED_PREFIXES = ("/v1/",)


async def api_key_middleware(request: Request, call_next):
    if not request.url.path.startswith(PROTECTED_PREFIXES):
        return await call_next(request)

    raw_key = _extract_api_key(request)
    if not raw_key:
        return JSONResponse(status_code=401, content={"detail": "Missing API key"})

    db = SessionLocal()
    try:
        api_key = (
            db.query(APIKey)
            .filter(APIKey.key_hash == hash_api_key(raw_key), APIKey.active.is_(True))
            .first()
        )
        if not api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
        api_key.last_used_at = datetime.now(UTC)
        db.add(api_key)
        db.commit()
        request.state.api_key = api_key
    finally:
        db.close()

    return await call_next(request)


def _extract_api_key(request: Request) -> str | None:
    bearer = request.headers.get("authorization")
    if bearer and bearer.lower().startswith("bearer "):
        return bearer.split(" ", 1)[1].strip()
    return request.headers.get("x-api-key")
