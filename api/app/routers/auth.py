"""/api/auth — Google OAuth, sessiya, chiqish, guest promptlarni koʻchirish.

Router faqat HTTP: state cookie, redirect, javob shakli. Google/baza mantiqi `services/auth.py` da
(`exchange_code`, `fetch_userinfo`, `upsert_user`, `remaining_today`, `save_prompts`) — testlarda
oʻsha modul orqali monkeypatch qilinadi, shuning uchun bu yerda `auth_service.<nom>` deb chaqiriladi.

Oqim: GET /google → Google → GET /google/callback → cookie → FRONTEND_URL + next.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.schemas import AiTool, Kind, Locale
from app.services import auth as auth_service
from app.services.auth import CurrentUser, LoggedInUser

log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

SessionDep = Annotated[AsyncSession | None, Depends(get_session)]

MIGRATE_MAX = 50
NOT_FOUND = "Topilmadi."
BAD_EMAIL = "Email notoʻgʻri."


# ---------------------------------------------------------------------- sxemalar


class GuestPromptIn(BaseModel):
    input_text: str = Field(min_length=1, max_length=4000)
    kind: Kind
    ai: AiTool
    clarifications: dict[str, str] = Field(default_factory=dict)
    result: str = Field(min_length=1, max_length=20000)
    explanations: list[str] = Field(default_factory=list, max_length=8)
    locale: Locale = "uz"
    output_language: Locale = "en"


class MigrateRequest(BaseModel):
    prompts: list[GuestPromptIn] = Field(default_factory=list, max_length=MIGRATE_MAX)


# ---------------------------------------------------------------------- yordamchilar


def _login_error_redirect(next_path: str, reason: str = "google") -> RedirectResponse:
    """Google/tarmoq xatosi — foydalanuvchi boʻsh 500 emas, login sahifasida xabar koʻradi."""
    s = get_settings()
    locale = auth_service.locale_of_path(next_path)
    resp = RedirectResponse(f"{s.frontend_url}/{locale}/login?error={reason}", status_code=302)
    auth_service.clear_state_cookie(resp)
    return resp


def _login_redirect(user_id, next_path: str) -> RedirectResponse:
    resp = RedirectResponse(get_settings().frontend_url + next_path, status_code=302)
    auth_service.set_session_cookie(resp, auth_service.create_token(user_id))
    auth_service.clear_state_cookie(resp)
    return resp


# ---------------------------------------------------------------------- endpointlar


@router.get("/google")
async def google_start(next: str = Query(default="/")):
    """Google'ga yoʻnaltiradi; `state` + `next` imzolangan qisqa muddatli cookie'da."""
    s = get_settings()
    if not s.google_client_id:
        raise HTTPException(status_code=503, detail=auth_service.GOOGLE_NOT_CONFIGURED)
    state = auth_service.new_state()
    next_path = auth_service.safe_next(next)
    resp = RedirectResponse(auth_service.google_authorize_url(state), status_code=302)
    auth_service.set_state_cookie(resp, auth_service.sign_state(state, next_path))
    return resp


@router.get("/google/callback")
async def google_callback(
    request: Request,
    session: SessionDep,
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
):
    saved = auth_service.load_state(request.cookies.get(auth_service.STATE_COOKIE))
    if saved is None or not state or saved["state"] != state:
        raise HTTPException(status_code=400, detail=auth_service.STATE_MISMATCH)
    next_path = saved["next"]
    if error or not code:
        log.warning("google callback rad etildi: %s", error or "code yoʻq")
        return _login_error_redirect(next_path)
    try:
        token = await auth_service.exchange_code(code)
        info = await auth_service.fetch_userinfo(token)
        user = await auth_service.upsert_user(
            session, str(info["sub"]), str(info["email"]), info.get("name"), info.get("picture")
        )
    except auth_service.GoogleAuthError as e:
        log.warning("google kirish xatosi: %s", e)
        return _login_error_redirect(next_path)
    except Exception:
        log.exception("google callback: foydalanuvchini saqlab boʻlmadi")
        return _login_error_redirect(next_path)
    log.info("kirdi: %s", user.email)
    return _login_redirect(user.id, next_path)


@router.get("/me")
async def me(user: LoggedInUser, session: SessionDep):
    remaining = await auth_service.remaining_today(session, user)
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "plan": user.plan,
        "pro_until": user.pro_until.isoformat() if user.pro_until else None,
        "is_admin": auth_service.is_admin_email(user.email),
        "bonus_generations": user.bonus_generations or 0,
        "remaining_today": remaining,
    }


@router.post("/logout")
async def logout(user: CurrentUser):
    resp = JSONResponse({"status": "ok"})
    auth_service.clear_session_cookie(resp)
    if user is not None:
        log.info("chiqdi: %s", user.email)
    return resp


@router.post("/migrate")
async def migrate(body: MigrateRequest, user: LoggedInUser, session: SessionDep):
    """Guest (localStorage) promptlarini kirgan foydalanuvchi tarixiga koʻchiradi."""
    items = [p.model_dump() for p in body.prompts]
    saved = await auth_service.save_prompts(session, user.id, items)
    return {"saved": saved}


@router.get("/dev-login")
async def dev_login(session: SessionDep, email: str = Query(default=""), next: str = "/"):
    """Faqat dev + AUTH_DEV_LOGIN=true: Google'siz kirish (google_sub = `dev-<email>`)."""
    s = get_settings()
    if not (s.is_dev and s.auth_dev_login):
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    email = email.strip().lower()
    if "@" not in email or len(email) > 320:
        raise HTTPException(status_code=422, detail=BAD_EMAIL)
    if session is None:
        raise HTTPException(status_code=503, detail=auth_service.DB_DOWN)
    user = await auth_service.upsert_user(
        session, f"dev-{email}", email, email.split("@", 1)[0], None
    )
    log.info("dev-login: %s", email)
    return _login_redirect(user.id, auth_service.safe_next(next))
