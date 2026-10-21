import hashlib
from functools import lru_cache

import redis
from fastapi import Depends, HTTPException, Request, status

from api.config import get_settings
from api.security import Principal, current_principal, current_principal_or_key


@lru_cache
def get_redis() -> redis.Redis:
    return redis.Redis.from_url(
        get_settings().redis_url, socket_timeout=1, socket_connect_timeout=1
    )


def _guarded(action):
    try:
        return action(get_redis())
    except redis.RedisError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Service unavailable") from exc


def _too_many(retry_after: int) -> HTTPException:
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Too many requests",
        headers={"Retry-After": str(max(retry_after, 1))},
    )


def hit(key: str, limit: int, window_seconds: int) -> None:
    def count(client: redis.Redis) -> tuple[int, int]:
        total = client.incr(key)
        if total == 1:
            client.expire(key, window_seconds)
        return total, client.ttl(key)

    total, ttl = _guarded(count)
    if total > limit:
        raise _too_many(ttl)


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()[:32]


def login_ip_limit(request: Request) -> None:
    hit(f"rl:login:ip:{request.client.host}", get_settings().login_ip_per_minute, 60)


def _account_key(email: str) -> str:
    return f"rl:login:account:{fingerprint(email)}"


def ensure_account_not_locked(email: str) -> None:
    failures, ttl = _guarded(
        lambda client: (int(client.get(_account_key(email)) or 0), client.ttl(_account_key(email)))
    )
    if failures >= get_settings().login_account_per_five_minutes:
        raise _too_many(ttl)


def record_login_failure(email: str) -> None:
    key = _account_key(email)

    def bump(client: redis.Redis) -> None:
        if client.incr(key) == 1:
            client.expire(key, 300)

    _guarded(bump)


def clear_login_failures(email: str) -> None:
    _guarded(lambda client: client.delete(_account_key(email)))


def _subject(principal: Principal) -> str:
    return f"key:{principal.api_key_id}" if principal.api_key_id else f"user:{principal.user_id}"


def check_limit(principal: Principal = Depends(current_principal_or_key)) -> Principal:
    hit(f"rl:check:{_subject(principal)}", get_settings().check_per_minute, 60)
    return principal


def batch_limit(principal: Principal = Depends(current_principal_or_key)) -> Principal:
    hit(f"rl:batch:{_subject(principal)}", get_settings().batch_per_hour, 3600)
    return principal


def password_limit(principal: Principal = Depends(current_principal)) -> Principal:
    hit(f"rl:password:{principal.user_id}", get_settings().password_changes_per_hour, 3600)
    return principal
