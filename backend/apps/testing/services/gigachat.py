from __future__ import annotations
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

@dataclass
class _TokenCache:
    token:      Optional[str] = None
    expires_at: float         = 0.0
    _lock:      Lock          = field(default_factory=Lock, repr=False, compare=False)

    def get(self) -> Optional[str]:
        with self._lock:
            if self.token and time.time() < self.expires_at - 30:
                return self.token
        return None

    def set(self, token: str, ttl_seconds: int = 1800) -> None:
        with self._lock:
            self.token      = token
            self.expires_at = time.time() + ttl_seconds


_token_cache = _TokenCache()

_OAUTH_URL      = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
_CHAT_URL       = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
_VERIFY_SSL     = False          # Sberbank uses a self-signed cert in their sandbox
_TIMEOUT_AUTH   = 10             # seconds
_TIMEOUT_CHAT   = 45             # seconds — AI calls can be slow



def _credentials() -> tuple[str, str]:
    """Pull credentials from Django settings at call time (avoids import-time errors)."""
    try:
        from django.conf import settings
        client_id = getattr(settings, "GIGACHAT_CLIENT_ID", "")
        secret    = getattr(settings, "GIGACHAT_SECRET", "")
        return client_id, secret
    except Exception:
        return "", ""


# ── Public API ───────────────────────────────────────────────────────────────────

def get_access_token() -> Optional[str]:
    """
    Obtain (or return cached) GigaChat OAuth2 access token.
    Returns None if authentication fails.
    """
    cached = _token_cache.get()
    if cached:
        return cached

    client_id, secret = _credentials()
    if not client_id or not secret:
        logger.error("GigaChat credentials not configured (GIGACHAT_CLIENT_ID / GIGACHAT_SECRET).")
        return None

    try:
        resp = requests.post(
            url=_OAUTH_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept":       "application/json",
                "RqUID":        str(uuid.uuid4()),
            },
            auth=HTTPBasicAuth(client_id, secret),
            data={"scope": "GIGACHAT_API_PERS"},
            verify=_VERIFY_SSL,
            timeout=_TIMEOUT_AUTH,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            logger.error("GigaChat OAuth response missing 'access_token'.")
            return None

        _token_cache.set(token, ttl_seconds=1800)
        logger.debug("GigaChat access token refreshed.")
        return token

    except requests.Timeout:
        logger.error("GigaChat OAuth timed out after %ss.", _TIMEOUT_AUTH)
    except requests.HTTPError as exc:
        logger.error("GigaChat OAuth HTTP error: %s — %s", exc.response.status_code, exc.response.text[:200])
    except Exception as exc:
        logger.exception("GigaChat OAuth unexpected error: %s", exc)
    return None


def send_prompt(message: str, token: Optional[str] = None) -> Optional[str]:
    """
    Send a single-turn chat message to GigaChat.
    Acquires a fresh token if none is supplied.
    Returns the assistant reply string, or None on failure.
    """
    if token is None:
        token = get_access_token()
    if not token:
        logger.error("Cannot send GigaChat prompt — no valid token.")
        return None

    payload = json.dumps({
        "model":       "GigaChat",
        "temperature": 0,
        "messages": [{"role": "user", "content": message}],
    })

    try:
        resp = requests.post(
            url=_CHAT_URL,
            headers={
                "Content-Type":  "application/json",
                "Accept":        "application/json",
                "Authorization": f"Bearer {token}",
            },
            data=payload,
            verify=_VERIFY_SSL,
            timeout=_TIMEOUT_CHAT,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return content

    except requests.Timeout:
        logger.error("GigaChat chat completion timed out after %ss.", _TIMEOUT_CHAT)
    except requests.HTTPError as exc:
        status = exc.response.status_code
        if status == 401:
            # Token may have expired mid-flight — invalidate cache
            _token_cache.set("", ttl_seconds=0)
            logger.warning("GigaChat 401 — token invalidated, will retry on next call.")
        else:
            logger.error("GigaChat HTTP error %s: %s", status, exc.response.text[:200])
    except (KeyError, IndexError, ValueError) as exc:
        logger.error("GigaChat unexpected response format: %s", exc)
    except Exception as exc:
        logger.exception("GigaChat send_prompt unexpected error: %s", exc)
    return None