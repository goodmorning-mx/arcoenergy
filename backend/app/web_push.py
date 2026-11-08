"""Minimal Web Push helpers using a persistent secret managed by Factory."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from urllib.parse import urlparse

import requests
from py_vapid import Vapid
from pywebpush import WebPushException, webpush

logger = logging.getLogger(__name__)

_P256_ORDER = int("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16)
_ALLOWED_PUSH_HOSTS = (
    "fcm.googleapis.com",
    "push.services.mozilla.com",
    "push.apple.com",
    "notify.windows.com",
)


class _NoRedirectSession(requests.Session):
    def request(self, method, url, **kwargs):
        kwargs["allow_redirects"] = False
        return super().request(method, url, **kwargs)


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _private_scalar(secret: str) -> bytes:
    seed = secret.encode("utf-8")
    counter = 0
    while True:
        digest = hashlib.sha256(b"arcoenergy-webpush-v1\0" + seed + counter.to_bytes(4, "big")).digest()
        scalar = int.from_bytes(digest, "big")
        if 0 < scalar < _P256_ORDER:
            return digest
        counter += 1


def vapid_public_key(secret: str) -> str:
    if not secret:
        raise ValueError("Web Push is not configured")
    vapid = Vapid.from_string(_b64url(_private_scalar(secret)))
    from cryptography.hazmat.primitives import serialization

    point = vapid.public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    return _b64url(point)


def validate_push_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    trusted = any(hostname == domain or hostname.endswith("." + domain) for domain in _ALLOWED_PUSH_HOSTS)
    if (
        parsed.scheme != "https"
        or not trusted
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path
        or len(endpoint) > 4096
    ):
        raise ValueError("Endpoint de notificación no admitido.")
    return endpoint


def send_push(subscription: dict[str, str], payload: dict[str, str], secret: str, subject: str) -> int | None:
    """Send a small user-visible message; return the push service response code."""
    try:
        endpoint = validate_push_endpoint(subscription["endpoint"])
        vapid_private_key = _b64url(_private_scalar(secret))
        with _NoRedirectSession() as requests_session:
            response = webpush(
                subscription_info={
                    "endpoint": endpoint,
                    "keys": {"p256dh": subscription["p256dh"], "auth": subscription["auth"]},
                },
                data=json.dumps(payload, separators=(",", ":")),
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": subject},
                ttl=86400,
                timeout=8,
                requests_session=requests_session,
            )
        return response.status_code
    except WebPushException as exc:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
        logger.info("Web Push delivery failed with status %s", status)
        return status
    except Exception:
        logger.warning("Web Push delivery failed without exposing subscription details")
        return None
