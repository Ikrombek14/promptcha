"""Sessiya (JWT cookie) va foydalanuvchi dependency'lari.

- Cookie `promptcha_session`: httpOnly, SameSite=Lax, Secure (prod), `JWT_EXPIRE_DAYS` kun.
- `get_current_user` — ixtiyoriy (None = kirmagan), `require_user` — 401, `require_admin` — 403.
- Admin = email `ADMIN_EMAILS` roʻyxatida (alohida parol yoʻq).
Google OAuth oqimi `routers/auth.py` da; bu modul faqat token/cookie/dependency.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import User

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
