"""Sessiya (JWT cookie) va foydalanuvchi dependency'lari.

- Cookie `promptcha_session`: httpOnly, SameSite=Lax, Secure (prod), `JWT_EXPIRE_DAYS` kun.
- `get_current_user` — ixtiyoriy (None = kirmagan), `require_user` — 401, `require_admin` — 403.
- Admin = email `ADMIN_EMAILS` roʻyxatida (alohida parol yoʻq).
Google OAuth oqimi `routers/auth.py` da; bu modul faqat token/cookie/dependency.
"""

import logging
import secrets
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from urllib.parse import urlencode

import httpx
from fastapi import Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import Prompt, UsageLog, User
from app.services import settings as app_settings

log = logging.getLogger(__name__)

ALGORITHM = "HS256"
NOT_LOGGED_IN = "Kirish talab qilinadi."
NOT_ADMIN = "Bu boʻlim faqat administrator uchun."


def create_token(user_id: uuid.UUID) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=s.jwt_expire_days)).timestamp()),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> uuid.UUID | None:
    """Yaroqsiz/muddati oʻtgan token → None (xato koʻtarilmaydi)."""
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[ALGORITHM])
        return uuid.UUID(str(payload.get("sub")))
    except (JWTError, ValueError):
        return None


def set_session_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        key=s.session_cookie_name,
        value=token,
        max_age=s.jwt_expire_days * 24 * 3600,
        httponly=True,
        secure=s.is_production,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(key=s.session_cookie_name, path="/")


def is_admin_email(email: str | None) -> bool:
    return bool(email) and email.strip().lower() in get_settings().admin_email_list


async def get_current_user(
    request: Request, session: Annotated[AsyncSession | None, Depends(get_session)]
) -> User | None:
    """Cookie boʻyicha foydalanuvchi; yoʻq/yaroqsiz → None. Baza xatosi ham None (sayt ishlayveradi)."""
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token or session is None:
        return None
    user_id = decode_token(token)
    if user_id is None:
        return None
    try:
        return await session.get(User, user_id)
    except Exception:
        log.exception("foydalanuvchini oʻqib boʻlmadi")
        return None


async def require_user(user: Annotated[User | None, Depends(get_current_user)]) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail=NOT_LOGGED_IN)
    return user


async def require_admin(user: Annotated[User, Depends(require_user)]) -> User:
    if not is_admin_email(user.email):
        raise HTTPException(status_code=403, detail=NOT_ADMIN)
    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]
LoggedInUser = Annotated[User, Depends(require_user)]
AdminUser = Annotated[User, Depends(require_admin)]


# ====================================================================== Google OAuth oqimi
# Router (`routers/auth.py`) faqat HTTP; quyidagilar testlarda monkeypatch qilinadi.

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_SCOPE = "openid email profile"

STATE_COOKIE = "promptcha_oauth"
STATE_MAX_AGE = 600  # 10 daqiqa
STATE_COOKIE_PATH = "/api/auth"
NEXT_MAX_LEN = 500

GOOGLE_NOT_CONFIGURED = "Google kirish sozlanmagan."
STATE_MISMATCH = "Kirish holati mos kelmadi. Qaytadan urinib koʻring."
DB_DOWN = "Xizmat vaqtincha ishlamayapti. Birozdan soʻng urinib koʻring."


class GoogleAuthError(Exception):
    """Google token/userinfo bosqichida xato (tarmoq, rad etilgan kod, notoʻliq javob)."""


def safe_next(raw: str | None) -> str:
    """Faqat sayt ichidagi nisbiy yoʻl (`/uz/app`); `//evil.com`, sxema, boshqaruv belgilari → `/`."""
    if not raw or len(raw) > NEXT_MAX_LEN:
        return "/"
    if not raw.startswith("/") or raw.startswith(("//", "/\\")):
        return "/"
    if "\\" in raw or any(ord(c) < 32 for c in raw):
        return "/"
    return raw


def locale_of_path(path: str) -> str:
    """`/ru/app` → `ru`; boshqasi → `uz`."""
    first = path.strip("/").split("/", 1)[0]
    return first if first in ("uz", "ru", "en") else "uz"


def _state_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().app_secret, salt="promptcha-oauth-state")


def new_state() -> str:
    return secrets.token_urlsafe(24)


def sign_state(state: str, next_path: str) -> str:
    return _state_serializer().dumps({"state": state, "next": next_path})


def load_state(value: str | None) -> dict[str, str] | None:
    """Cookie qiymati → {state, next}; imzo/muddat notoʻgʻri → None."""
    if not value:
        return None
    try:
        data = _state_serializer().loads(value, max_age=STATE_MAX_AGE)
    except BadSignature:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("state"), str):
        return None
    return {"state": data["state"], "next": safe_next(data.get("next"))}


def set_state_cookie(response: Response, value: str) -> None:
    s = get_settings()
    response.set_cookie(
        key=STATE_COOKIE,
        value=value,
        max_age=STATE_MAX_AGE,
        httponly=True,
        secure=s.is_production,
        samesite="lax",
        path=STATE_COOKIE_PATH,
    )


def clear_state_cookie(response: Response) -> None:
    response.delete_cookie(key=STATE_COOKIE, path=STATE_COOKIE_PATH)


def google_authorize_url(state: str) -> str:
    s = get_settings()
    query = {
        "client_id": s.google_client_id,
        "redirect_uri": s.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "state": state,
        "prompt": "select_account",
        "access_type": "online",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(query)}"


async def exchange_code(code: str) -> str:
    """Authorization code → access_token. Xato → GoogleAuthError."""
    s = get_settings()
    data = {
        "code": code,
        "client_id": s.google_client_id,
        "client_secret": s.google_client_secret,
        "redirect_uri": s.google_redirect_uri,
        "grant_type": "authorization_code",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(GOOGLE_TOKEN_URL, data=data)
    except httpx.HTTPError as e:
        raise GoogleAuthError(f"token soʻrovi: {e}") from e
    if r.status_code != 200:
        raise GoogleAuthError(f"token javobi {r.status_code}: {r.text[:200]}")
    token = r.json().get("access_token")
    if not token:
        raise GoogleAuthError("javobda access_token yoʻq")
    return token


async def fetch_userinfo(access_token: str) -> dict[str, Any]:
    """OpenID userinfo: {sub, email, name, picture, ...}. Xato → GoogleAuthError."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
    except httpx.HTTPError as e:
        raise GoogleAuthError(f"userinfo soʻrovi: {e}") from e
    if r.status_code != 200:
        raise GoogleAuthError(f"userinfo javobi {r.status_code}")
    info = r.json()
    if not info.get("sub") or not info.get("email"):
        raise GoogleAuthError("userinfo'da sub/email yoʻq")
    return info


async def upsert_user(
    session: AsyncSession | None,
    sub: str,
    email: str,
    name: str | None,
    avatar_url: str | None,
) -> User:
    """google_sub boʻyicha topadi (yoʻq boʻlsa email boʻyicha — dev-login/qayta ulanish), yangilaydi
    yoki yaratadi; `last_login_at = now`. Commit shu yerda."""
    if session is None:
        raise RuntimeError("baza sessiyasi yoʻq")
    email = email.strip().lower()
    user = await session.scalar(select(User).where(User.google_sub == sub))
    if user is None:
        user = await session.scalar(select(User).where(User.email == email))
    now = datetime.now(UTC)
    if user is None:
        user = User(google_sub=sub, email=email, name=name, avatar_url=avatar_url)
        session.add(user)
    else:
        user.google_sub = sub
        user.email = email
        if name:
            user.name = name
        if avatar_url:
            user.avatar_url = avatar_url
    user.last_login_at = now
    await session.commit()
    await session.refresh(user)
    return user


# ====================================================================== hisob va koʻchirish


async def remaining_today(session: AsyncSession | None, user: User) -> int | None:
    """Bugun (oxirgi 24 soat) qolgan bepul urinishlar; Pro → None (cheksiz).

    = max(0, free_daily_generations − bugungi usage_log soni) + bonus_generations.
    Sessiya None (baza yoʻq) → usage soni 0 deb olinadi (limit .env/app_settings'dan).
    """
    if user.is_pro:
        return None
    limit = await app_settings.get_int("free_daily_generations", session)
    used = 0
    if session is not None:
        since = datetime.now(UTC) - timedelta(days=1)
        try:
            used = (
                await session.scalar(
                    select(func.count())
                    .select_from(UsageLog)
                    .where(UsageLog.user_id == user.id, UsageLog.created_at >= since)
                )
                or 0
            )
        except Exception:
            log.exception("usage_log oʻqib boʻlmadi (remaining_today)")
    return max(0, limit - used) + (user.bonus_generations or 0)


async def save_prompts(
    session: AsyncSession | None, user_id: uuid.UUID, items: Sequence[Mapping[str, Any]]
) -> int:
    """Guest promptlarni `prompts` ga yozadi. Dublikat (shu user'da bir xil input_text+result) va
    tana ichidagi takrorlar oʻtkazib yuboriladi. Qaytaradi: saqlanganlar soni."""
    if session is None:
        raise HTTPException(status_code=503, detail=DB_DOWN)
    if not items:
        return 0
    texts = {p["input_text"] for p in items}
    rows = await session.execute(
        select(Prompt.input_text, Prompt.result).where(
            Prompt.user_id == user_id, Prompt.input_text.in_(texts)
        )
    )
    seen: set[tuple[str, str]] = {(t, r) for t, r in rows.all()}
    saved = 0
    for p in items:
        key = (p["input_text"], p["result"])
        if key in seen:
            continue
        seen.add(key)
        session.add(
            Prompt(
                user_id=user_id,
                input_text=p["input_text"],
                kind=p["kind"],
                ai=p["ai"],
                clarifications=dict(p.get("clarifications") or {}),
                result=p["result"],
                explanations=list(p.get("explanations") or []),
                locale=p.get("locale") or "uz",
                output_language=p.get("output_language") or "en",
            )
        )
        saved += 1
    await session.commit()
    return saved
