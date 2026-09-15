"""/api/admin — statistika, foydalanuvchilar, toʻlovlar, sozlamalar (faqat ADMIN_EMAILS).

Router faqat HTTP: kirish tekshiruvi (`AdminUser`), tana/param validatsiyasi, javob shakli.
SQL va qoidalar `services/admin.py` da. Har oʻzgartiruvchi amal log'ga yoziladi (kim, nima).

  GET  /api/admin/stats?days=30
  GET  /api/admin/users?q=&page=&limit=
  POST /api/admin/users/{user_id}/grant     {plan?, pro_days?, bonus_generations?}
  GET  /api/admin/payments?page=&limit=
  POST /api/admin/payments                  {user_id, amount, method?, days, note?}
  GET  /api/admin/settings
  PUT  /api/admin/settings                  {guest_total_generations?, ...}
"""

import logging
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.services import admin as service
from app.services.auth import AdminUser

log = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

Session = Annotated[AsyncSession, Depends(get_session)]


# ---------- javob shakllari ----------


class Counters(BaseModel):
    today: int
    d7: int
    d30: int


class Tokens(BaseModel):
    input: int
    output: int


class ByTool(BaseModel):
    ai: str
    generations: int
    input_tokens: int
    output_tokens: int


class ByProvider(BaseModel):
    provider: str
    model: str
    calls: int
    input_tokens: int
    output_tokens: int
    estimated_calls: int


class ByStage(BaseModel):
    stage: str
    calls: int
    input_tokens: int
    output_tokens: int


class TopUser(BaseModel):
    user_id: str
    email: str
    generations: int
    input_tokens: int
    output_tokens: int


class Daily(BaseModel):
    date: str
    generations: int
    input_tokens: int
    output_tokens: int


class StatsOut(BaseModel):
    days: int
    active_users: Counters
    generations: Counters
    tokens: Tokens
    by_tool: list[ByTool]
    by_provider: list[ByProvider]
    by_stage: list[ByStage]
    top_users: list[TopUser]
    daily: list[Daily]


class UserItem(BaseModel):
    id: UUID
    email: str
    name: str | None = None
    avatar_url: str | None = None
    plan: str
    pro_until: datetime | None = None
    bonus_generations: int
    generations_total: int
    input_tokens: int
    output_tokens: int
    created_at: datetime | None = None
    last_login_at: datetime | None = None
    is_admin: bool


class UsersOut(BaseModel):
    items: list[UserItem]
    total: int
    page: int
    limit: int


class PaymentItem(BaseModel):
    id: UUID
    user_id: UUID
    email: str | None = None
    amount: int
    currency: str
    method: str
    days: int
    note: str | None = None
    provider_ref: str | None = None
    created_by: str | None = None
    paid_at: datetime | None = None


class PaymentsOut(BaseModel):
    items: list[PaymentItem]
    total: int
    page: int
    limit: int


class SettingsOut(BaseModel):
    guest_total_generations: int
    guest_daily_ip_generations: int
    free_daily_generations: int
    defaults: dict[str, int]


# ---------- kirish tanalari ----------


class GrantBody(BaseModel):
    plan: Literal["free", "pro"] | None = None
    pro_days: int | None = Field(default=None, ge=1, le=3650)
    bonus_generations: int | None = Field(default=None, ge=-1000, le=1000)


class PaymentBody(BaseModel):
    user_id: UUID
    amount: int = Field(ge=0)
    method: Literal["manual", "payme", "click"] = "manual"
    days: int = Field(ge=1, le=3650)
    note: str | None = Field(default=None, max_length=500)


class SettingsBody(BaseModel):
    guest_total_generations: int | None = None
    guest_daily_ip_generations: int | None = None
    free_daily_generations: int | None = None


# ---------- yoʻllar ----------


@router.get("/stats", response_model=StatsOut)
async def stats(
    admin: AdminUser,
    session: Session,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    return await service.stats(session, days)


@router.get("/users", response_model=UsersOut)
async def users(
    admin: AdminUser,
    session: Session,
    q: Annotated[str, Query(max_length=200)] = "",
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    return await service.list_users(session, q=q, page=page, limit=limit)


@router.post("/users/{user_id}/grant", response_model=UserItem)
async def grant(admin: AdminUser, session: Session, user_id: UUID, body: GrantBody):
    log.info(
        "admin %s: grant user=%s plan=%s pro_days=%s bonus=%s",
        admin.email,
        user_id,
        body.plan,
        body.pro_days,
        body.bonus_generations,
    )
    return await service.grant(
        session,
        user_id,
        plan=body.plan,
        pro_days=body.pro_days,
        bonus_generations=body.bonus_generations,
    )


@router.get("/payments", response_model=PaymentsOut)
async def payments(
    admin: AdminUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    return await service.list_payments(session, page=page, limit=limit)


@router.post("/payments", response_model=PaymentItem)
async def create_payment(admin: AdminUser, session: Session, body: PaymentBody):
    log.info(
        "admin %s: payment user=%s amount=%s method=%s days=%s",
        admin.email,
        body.user_id,
        body.amount,
        body.method,
        body.days,
    )
    return await service.create_payment(
        session,
        body.user_id,
        amount=body.amount,
        days=body.days,
        method=body.method,
        note=body.note,
        created_by=admin.email,
    )


@router.get("/settings", response_model=SettingsOut)
async def get_settings_(admin: AdminUser, session: Session):
    return await service.get_settings_view(session)


@router.put("/settings", response_model=SettingsOut)
async def update_settings(admin: AdminUser, session: Session, body: SettingsBody):
    values = body.model_dump(exclude_none=True)
    log.info("admin %s: settings %s", admin.email, values)
    return await service.update_settings(session, values)
