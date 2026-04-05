"""
django_client.py — Async HTTP client layer for the Django REST backend.

All communication with Django goes through this module.
Uses aiohttp with a shared ClientSession (connection pooling, keep-alive).

Public API:
    DjangoAPIClient.session()          — async context manager for raw access
    DjangoAPIClient.validate_session() — validate a session key
    DjangoAPIClient.start_attempt()    — begin a student attempt
    DjangoAPIClient.submit_answer()    — push one answer
    DjangoAPIClient.finish_attempt()   — finalise and get score
    DjangoAPIClient.get_attempt_result() — full result with answer details
    DjangoAPIClient.close()            — shutdown shared session
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

import aiohttp
from aiohttp import ClientResponseError, ClientConnectorError, ServerTimeoutError

from config import settings

logger = logging.getLogger("django_client")

# ── Shared session (singleton) ────────────────────────────────────────────────

_session: aiohttp.ClientSession | None = None
_session_lock = asyncio.Lock()


async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        async with _session_lock:
            if _session is None or _session.closed:
                timeout = aiohttp.ClientTimeout(
                    connect=settings.HTTP_CONNECT_TIMEOUT,
                    sock_read=settings.HTTP_READ_TIMEOUT,
                    total=settings.HTTP_TOTAL_TIMEOUT,
                )
                connector = aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=20,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )
                _session = aiohttp.ClientSession(
                    base_url=settings.DJANGO_API_BASE,
                    timeout=timeout,
                    connector=connector,
                    headers={
                        "Content-Type": "application/json",
                        "Accept":       "application/json",
                        "User-Agent":   "OkurmenKids-WS-Engine/1.0",
                    },
                )
                logger.info("aiohttp session created → %s", settings.DJANGO_API_BASE)
    return _session


# ── Exceptions ────────────────────────────────────────────────────────────────

class DjangoAPIError(Exception):
    """Raised when the Django backend returns a non-2xx or is unreachable."""
    def __init__(self, message: str, status_code: int | None = None, detail: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.detail      = detail

    def __str__(self):
        base = super().__str__()
        if self.status_code:
            return f"[HTTP {self.status_code}] {base}"
        return base


class SessionExpiredError(DjangoAPIError):
    """Session key is invalid or expired."""


class AttemptError(DjangoAPIError):
    """Attempt-related validation error (e.g. already finished)."""


# ── Low-level HTTP helpers ────────────────────────────────────────────────────

class _RawClient:
    """Thin wrapper exposing get/post with uniform error handling."""

    def __init__(self, session: aiohttp.ClientSession):
        self._s = session

    async def get(self, path: str, **kwargs) -> Any:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, json: dict | None = None, **kwargs) -> Any:
        return await self._request("POST", path, json=json, **kwargs)

    async def get_raw(self, path: str) -> Any:
        """Return raw JSON without error wrapping (for health checks etc.)."""
        session = await _get_session()
        async with session.get(path) as resp:
            return await resp.json()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        session = await _get_session()
        try:
            async with session.request(method, path, **kwargs) as resp:
                body = await resp.json(content_type=None)

                if resp.status == 400:
                    detail = body.get("detail", str(body))
                    # Distinguish session-expired from generic 400
                    lc = detail.lower()
                    if "session" in lc and ("expired" in lc or "invalid" in lc or "deactivated" in lc):
                        raise SessionExpiredError(detail, status_code=400, detail=detail)
                    if "attempt" in lc:
                        raise AttemptError(detail, status_code=400, detail=detail)
                    raise DjangoAPIError(detail, status_code=400, detail=detail)

                if resp.status == 404:
                    detail = body.get("detail", "Not found.")
                    raise DjangoAPIError(detail, status_code=404, detail=detail)

                if resp.status >= 500:
                    raise DjangoAPIError(
                        f"Django server error {resp.status}",
                        status_code=resp.status,
                        detail=str(body),
                    )

                resp.raise_for_status()
                return body

        except (ClientResponseError,) as exc:
            raise DjangoAPIError(str(exc), status_code=exc.status) from exc
        except ClientConnectorError as exc:
            raise DjangoAPIError(f"Cannot connect to Django: {exc}") from exc
        except ServerTimeoutError as exc:
            raise DjangoAPIError(f"Django request timed out: {exc}") from exc


# ── Public API ────────────────────────────────────────────────────────────────

class DjangoAPIClient:
    """
    High-level typed client for the OkurmenKids Django API.
    All methods are coroutines; call from async context.
    """

    @staticmethod
    @asynccontextmanager
    async def session():
        """Yield a low-level _RawClient for ad-hoc requests."""
        s = await _get_session()
        yield _RawClient(s)

    # ── Session ───────────────────────────────────────────────────────────────

    @staticmethod
    async def validate_session(key: str) -> dict:
        """
        POST /api/v1/sessions/validate
        Returns full session metadata if key is valid.
        Raises SessionExpiredError if key is invalid/expired.
        """
        async with DjangoAPIClient.session() as client:
            data = await client.post("/api/v1/sessions/validate", json={"key": key})
        logger.debug("validate_session(%s) → %s", key[:8], data.get("status"))
        return data

    @staticmethod
    async def get_session_data(key: str) -> dict:
        """
        GET /api/v1/sync/session/{key}
        Returns full session + questions payload for FastAPI consumption.
        """
        async with DjangoAPIClient.session() as client:
            data = await client.get(f"/api/v1/sync/session/{key}")
        return data

    # ── Attempt ───────────────────────────────────────────────────────────────

    @staticmethod
    async def start_attempt(key: str, student_name: str) -> dict:
        """
        POST /api/v1/attempt/start
        Returns attempt_id, questions list, session_type, test_title.
        """
        async with DjangoAPIClient.session() as client:
            data = await client.post(
                "/api/v1/attempt/start",
                json={"key": key, "student_name": student_name},
            )
        logger.info(
            "start_attempt: student=%s attempt=%s",
            student_name, data.get("attempt_id", "?")[:8],
        )
        return data

    @staticmethod
    async def submit_answer(
        attempt_id: str,
        question_id: str,
        answer_text: str = "",
        selected_options: list[str] | None = None,
    ) -> dict:
        """
        POST /api/v1/attempt/answer
        Returns { answer_id, is_correct, grading_status, message }.
        """
        payload: dict = {
            "attempt_id":       attempt_id,
            "question_id":      question_id,
            "answer_text":      answer_text,
            "selected_options": selected_options or [],
        }
        async with DjangoAPIClient.session() as client:
            data = await client.post("/api/v1/attempt/answer", json=payload)
        logger.debug(
            "submit_answer: attempt=%s q=%s → correct=%s",
            attempt_id[:8], question_id[:8], data.get("is_correct"),
        )
        return data

    @staticmethod
    async def finish_attempt(attempt_id: str) -> dict:
        """
        POST /api/v1/attempt/finish
        Returns FinishResult with score, answered, correct, duration_seconds.
        """
        async with DjangoAPIClient.session() as client:
            data = await client.post(
                "/api/v1/attempt/finish",
                json={"attempt_id": attempt_id},
            )
        logger.info(
            "finish_attempt: attempt=%s score=%.1f",
            attempt_id[:8], data.get("score", 0),
        )
        return data

    @staticmethod
    async def get_attempt_result(attempt_id: str) -> dict:
        """
        GET /api/v1/attempt/{attempt_id}/result
        Full result with per-question breakdown.
        """
        async with DjangoAPIClient.session() as client:
            data = await client.get(f"/api/v1/attempt/{attempt_id}/result")
        return data

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @staticmethod
    async def close():
        global _session
        if _session and not _session.closed:
            await _session.close()
            _session = None
            logger.info("aiohttp session closed.")