import redis
from fastapi import HTTPException, Request

from app.core.config import settings

_redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

WINDOW_SECONDS = 60


def rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:{client_ip}:{request.url.path}"

    current = _redis_client.incr(key)
    if current == 1:
        _redis_client.expire(key, WINDOW_SECONDS)

    if current > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
