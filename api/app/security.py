"""Kirish nazorati va xavfsizlik sarlavhalari (sof ASGI middleware — SSE oqimiga xalaqit bermaydi).

Himoya qatlamlari:
  1. API faqat 127.0.0.1 da tinglaydi; tashqaridan faqat Nginx orqali (`/api/`).
  2. Nginx har soʻrovga `X-Internal-Key` qoʻshadi — kalit mos kelmasa 403 (prod'da majburiy).
  3. Brauzer soʻrovlari: `Origin`/`Referer` faqat ruxsat etilgan sayt (CSRF va begona saytlar).
  4. `X-Requested-With: promptcha` sarlavhasi — oddiy form/curl soʻrovlari rad etiladi.
  5. Tana hajmi ≤ 64 KB.
  6. Javob sarlavhalari: no-store, nosniff, frame yoʻq, referrer yoʻq.
"""

import json
import logging
from urllib.parse import urlsplit

from app.config import Settings

log = logging.getLogger(__name__)

REQUESTED_WITH = "promptcha"
MAX_BODY_BYTES = 64 * 1024
PUBLIC_PATHS = {"/api/health"}
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

SECURITY_HEADERS = [
    (b"cache-control", b"no-store"),
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
]


def _origin_of(url: str) -> str:
    p = urlsplit(url)
    return f"{p.scheme}://{p.netloc}".lower() if p.scheme and p.netloc else ""


class SecurityMiddleware:
    def __init__(self, app, settings: Settings):
        self.app = app
        self.s = settings
        self.allowed_origins = {
            _origin_of(o) for o in [*settings.cors_origin_list, settings.frontend_url] if o
        }
        self.internal_key = settings.internal_api_key.encode() if settings.internal_api_key else b""

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api"):
            await self.app(scope, receive, send)
            return

        reason = self._reject_reason(scope)
        if reason:
            await self._deny(send, reason)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {k.lower() for k, _ in headers}
                for k, v in SECURITY_HEADERS:
                    if k not in present:
                        headers.append((k, v))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, self._limit_body(receive), send_with_headers)

    # ------------------------------------------------------------------ tekshiruvlar

    def _reject_reason(self, scope) -> str | None:
        path: str = scope["path"]
        method: str = scope["method"].upper()
        headers = {k.decode().lower(): v for k, v in scope.get("headers", [])}
        if path in PUBLIC_PATHS:
            return None
        if self.s.is_dev and path.startswith(("/api/docs", "/api/openapi.json")):
            return None

        # 2. Nginx maxfiy kaliti (prod'da majburiy; dev'da boʻsh boʻlsa tekshirilmaydi)
        if self.internal_key and headers.get("x-internal-key", b"") != self.internal_key:
            return "internal key"

        # 4. Maxsus sarlavha — brauzerdagi bizning kodimizdan kelganini bildiradi
        if headers.get("x-requested-with", b"").decode(errors="ignore") != REQUESTED_WITH:
            return "requested-with"

        # 3. Origin/Referer — faqat oʻz saytimiz (unsafe metodlarda majburiy, GET'da bor boʻlsa tekshiriladi)
        origin = headers.get("origin", b"").decode(errors="ignore")
        referer = headers.get("referer", b"").decode(errors="ignore")
        source = _origin_of(origin) if origin else _origin_of(referer)
        if source:
            if source not in self.allowed_origins:
                return "origin"
        elif method in UNSAFE_METHODS:
            return "origin missing"

        # 5. Tana hajmi (Content-Length boʻyicha; chunked boʻlsa _limit_body ushlaydi)
        cl = headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > MAX_BODY_BYTES:
            return "body too large"
        return None

    def _limit_body(self, receive):
        received = 0

        async def limited():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > MAX_BODY_BYTES:
                    raise ValueError("body too large")
            return message

        return limited

    async def _deny(self, send, reason: str):
        log.warning("api rad etildi: %s", reason)
        status = 413 if reason == "body too large" else 403
        body = json.dumps(
            {"detail": "Soʻrov rad etildi. Iltimos, sayt orqali foydalaning."},
            ensure_ascii=False,
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(body)).encode()),
                    *SECURITY_HEADERS,
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def client_ip(scope_or_request) -> str:
    """Haqiqiy IP: Nginx orqasida boʻlsak X-Forwarded-For (faqat TRUST_PROXY=true), aks holda socket."""
    from app.config import get_settings

    request = scope_or_request
    headers = request.headers
    if get_settings().trust_proxy:
        xff = headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        real = headers.get("x-real-ip")
        if real:
            return real.strip()
    return request.client.host if request.client else "unknown"
