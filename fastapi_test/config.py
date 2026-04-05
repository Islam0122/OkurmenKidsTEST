"""
config.py — centralised settings loaded from environment variables.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    # ── FastAPI server ────────────────────────────────────────────────────────
    PORT:  int  = int(os.getenv("PORT",  "8001"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── Django backend ────────────────────────────────────────────────────────
    DJANGO_API_BASE: str = os.getenv(
        "DJANGO_API_BASE",
        "https://okurmenkidstest.up.railway.app",
    ).rstrip("/")

    # ── HTTP client timeouts (seconds) ────────────────────────────────────────
    HTTP_CONNECT_TIMEOUT:  float = float(os.getenv("HTTP_CONNECT_TIMEOUT",  "10"))
    HTTP_READ_TIMEOUT:     float = float(os.getenv("HTTP_READ_TIMEOUT",     "30"))
    HTTP_TOTAL_TIMEOUT:    float = float(os.getenv("HTTP_TOTAL_TIMEOUT",    "60"))

    # ── WebSocket ─────────────────────────────────────────────────────────────
    # How long (seconds) to wait for the first "start" message after connect
    WS_HANDSHAKE_TIMEOUT: float = float(os.getenv("WS_HANDSHAKE_TIMEOUT", "30"))
    # Ping interval to keep connections alive
    WS_PING_INTERVAL:     float = float(os.getenv("WS_PING_INTERVAL", "25"))

    # ── Exam limits ───────────────────────────────────────────────────────────
    # Max idle (no message) seconds before server closes the WS
    WS_IDLE_TIMEOUT: float = float(os.getenv("WS_IDLE_TIMEOUT", "300"))


settings = Settings()