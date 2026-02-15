"""Simple in-memory rate limiting middleware helpers."""

from __future__ import annotations

import asyncio
import math
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Pattern

from fastapi import Request

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except Exception:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore[assignment]
    get_remote_address = None  # type: ignore[assignment]


if Limiter is not None and get_remote_address is not None:
    limiter = Limiter(key_func=get_remote_address)
else:  # pragma: no cover - fallback for environments without slowapi

    class _NoOpLimiter:
        def limit(self, *_args, **_kwargs):
            def _decorator(func):
                return func

            return _decorator

    limiter = _NoOpLimiter()


@dataclass(frozen=True)
class RateLimitRule:
    method: str
    pattern: Pattern[str]
    limit: int
    window_seconds: int


class InMemoryRateLimiter:
    """Small, process-local rate limiter keyed by client IP + endpoint group."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._rules: list[RateLimitRule] = [
            RateLimitRule("POST", re.compile(r"^/api/v1/suitors/register$"), 10, 60),
            RateLimitRule("POST", re.compile(r"^/api/v1/sessions/start$"), 5, 60),
            RateLimitRule("POST", re.compile(r"^/api/v1/sessions/[^/]+/end$"), 5, 60),
            RateLimitRule(
                "GET", re.compile(r"^/api/v1/sessions/[^/]+/verdict$"), 30, 60
            ),
            RateLimitRule("GET", re.compile(r"^/api/v1/sessions/[^/]+/slots$"), 10, 60),
            RateLimitRule("POST", re.compile(r"^/api/v1/sessions/[^/]+/book$"), 3, 60),
            RateLimitRule("GET", re.compile(r"^/api/v1/public/[^/]+$"), 60, 60),
            RateLimitRule(
                "PATCH", re.compile(r"^/api/v1/dashboard/heart/status$"), 5, 60
            ),
            RateLimitRule("GET", re.compile(r"^/api/v1/dashboard(?:/.*)?$"), 30, 60),
            RateLimitRule("GET", re.compile(r"^/api/v1/admin/health$"), 60, 60),
            RateLimitRule("GET", re.compile(r"^/health$"), 60, 60),
        ]

    async def check_request(self, request: Request) -> int | None:
        method = request.method.upper()
        path = request.url.path
        ip = self._client_ip(request)

        for rule in self._rules:
            if method != rule.method or not rule.pattern.match(path):
                continue
            key = f"{ip}:{rule.method}:{rule.pattern.pattern}"
            return await self._consume(key, rule.limit, rule.window_seconds)
        return None

    async def _consume(self, key: str, limit: int, window_seconds: int) -> int | None:
        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            window = self._hits[key]
            while window and window[0] <= cutoff:
                window.popleft()

            if len(window) >= limit:
                retry_after = max(1, math.ceil(window_seconds - (now - window[0])))
                return retry_after

            window.append(now)
            return None

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"
