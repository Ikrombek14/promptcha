"""Admin paneli mantiqi: statistika, foydalanuvchilar, Pro berish, toʻlovlar, sozlamalar.

Router (`routers/admin.py`) faqat HTTP; SQL va qoidalar shu yerda. Hammasi async.
Sof funksiyalar (`extend_pro`, `apply_bonus`) bazasiz testlanadi.

Manbalar:
- `usage_log` — muvaffaqiyatli generate'lar (faol foydalanuvchilar, vosita kesimi, top, kunlik)
- `llm_calls`  — har LLM chaqiruvi (tokenlar, provayder/model, bosqich)
"""

import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import LlmCall, Payment, UsageLog, User
from app.services import settings as app_settings
from app.services.auth import is_admin_email

log = logging.getLogger(__name__)

USER_NOT_FOUND = "Foydalanuvchi topilmadi."
NOTHING_TO_CHANGE = "Oʻzgartirish uchun hech narsa berilmadi."
TOP_USERS_LIMIT = 10


# ---------- sof qoidalar ----------


def extend_pro(user: User, days: int, now: datetime | None = None) -> User:
    """Pro'ni `days` kunga uzaytiradi: muddati kelajakda boʻlsa unga qoʻshiladi, aks holda hozirdan."""
    now = now or datetime.now(UTC)
    base = user.pro_until if user.pro_until is not None and user.pro_until > now else now
    user.plan = "pro"
    user.pro_until = base + timedelta(days=days)
    return user


def apply_bonus(user: User, delta: int) -> User:
    """Bonus urinishlarga `delta` qoʻshadi (manfiy boʻlishi mumkin); natija 0 dan kam boʻlmaydi."""
    user.bonus_generations = max(0, (user.bonus_generations or 0) + delta)
    return user


def set_plan(user: User, plan: str) -> User:
    """`free` → muddat oʻchadi; `pro` (kunsiz) → muddatsiz Pro."""
    user.plan = plan
    user.pro_until = None
    return user


# ---------- statistika ----------


def _window(days: int, now: datetime) -> datetime:
    return now - timedelta(days=days)


async def stats(session: AsyncSession, days: int = 30) -> dict[str, Any]:
    now = datetime.now(UTC)
    since = _window(days, now)
    gen = UsageLog.action == "generate"

    # Faol foydalanuvchilar va generatsiyalar — uchta oyna bitta soʻrovda (FILTER)
    cols = []
    for label, d in (("today", 1), ("d7", 7), ("d30", 30)):
        w = UsageLog.created_at >= _window(d, now)
        cols.append(
            (
                func.count(func.distinct(UsageLog.user_id)).filter(w, gen)
                + func.count(func.distinct(UsageLog.guest_id)).filter(
                    w, gen, UsageLog.user_id.is_(None)
                )
            ).label(f"active_{label}")
        )
        cols.append(func.count().filter(w, gen).label(f"gen_{label}"))
    row = (await session.execute(select(*cols))).one()
    active_users = {k: int(getattr(row, f"active_{k}") or 0) for k in ("today", "d7", "d30")}
    generations = {k: int(getattr(row, f"gen_{k}") or 0) for k in ("today", "d7", "d30")}

    in_llm = LlmCall.created_at >= since
    tok = (
        await session.execute(
            select(
                func.coalesce(func.sum(LlmCall.input_tokens), 0),
                func.coalesce(func.sum(LlmCall.output_tokens), 0),
            ).where(in_llm)
        )
    ).one()
    tokens = {"input": int(tok[0]), "output": int(tok[1])}

    in_usage = UsageLog.created_at >= since
    by_tool_rows = (
        await session.execute(
            select(
                UsageLog.ai,
                func.count().label("generations"),
                func.coalesce(func.sum(UsageLog.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(UsageLog.output_tokens), 0).label("output_tokens"),
            )
            .where(in_usage, gen)
            .group_by(UsageLog.ai)
            .order_by(func.count().desc())
        )
    ).all()
    by_tool = [
        {
            "ai": r.ai or "unknown",
            "generations": int(r.generations),
            "input_tokens": int(r.input_tokens),
            "output_tokens": int(r.output_tokens),
        }
        for r in by_tool_rows
    ]

    by_provider_rows = (
        await session.execute(
            select(
                LlmCall.provider,
                LlmCall.model,
                func.count().label("calls"),
                func.coalesce(func.sum(LlmCall.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(LlmCall.output_tokens), 0).label("output_tokens"),
                func.count().filter(LlmCall.estimated.is_(True)).label("estimated_calls"),
            )
            .where(in_llm)
            .group_by(LlmCall.provider, LlmCall.model)
            .order_by(func.count().desc())
        )
    ).all()
    by_provider = [
        {
            "provider": r.provider,
            "model": r.model,
            "calls": int(r.calls),
            "input_tokens": int(r.input_tokens),
            "output_tokens": int(r.output_tokens),
            "estimated_calls": int(r.estimated_calls),
        }
        for r in by_provider_rows
    ]

    by_stage_rows = (
        await session.execute(
            select(
                LlmCall.stage,
                func.count().label("calls"),
                func.coalesce(func.sum(LlmCall.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(LlmCall.output_tokens), 0).label("output_tokens"),
            )
            .where(in_llm)
            .group_by(LlmCall.stage)
            .order_by(func.count().desc())
        )
    ).all()
    by_stage = [
        {
            "stage": r.stage,
            "calls": int(r.calls),
            "input_tokens": int(r.input_tokens),
            "output_tokens": int(r.output_tokens),
        }
        for r in by_stage_rows
    ]

    in_sum = func.coalesce(func.sum(UsageLog.input_tokens), 0)
    out_sum = func.coalesce(func.sum(UsageLog.output_tokens), 0)
    top_rows = (
        await session.execute(
            select(
                UsageLog.user_id,
                User.email,
                func.count().label("generations"),
                in_sum.label("input_tokens"),
                out_sum.label("output_tokens"),
            )
            .join(User, User.id == UsageLog.user_id)
            .where(in_usage, gen, UsageLog.user_id.is_not(None))
            .group_by(UsageLog.user_id, User.email)
            .order_by((in_sum + out_sum).desc(), func.count().desc())
            .limit(TOP_USERS_LIMIT)
        )
    ).all()
    top_users = [
        {
            "user_id": str(r.user_id),
            "email": r.email,
            "generations": int(r.generations),
            "input_tokens": int(r.input_tokens),
            "output_tokens": int(r.output_tokens),
        }
        for r in top_rows
    ]

    # Kunlik (UTC), boʻsh kunlar 0 bilan, eskidan yangiga
    day_col = func.date_trunc("day", func.timezone("UTC", UsageLog.created_at))
    daily_rows = (
        await session.execute(
            select(
                day_col.label("day"),
                func.count().label("generations"),
                func.coalesce(func.sum(UsageLog.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(UsageLog.output_tokens), 0).label("output_tokens"),
            )
            .where(in_usage, gen)
            .group_by(day_col)
        )
    ).all()
    by_day: dict[date, dict[str, int]] = {}
    for r in daily_rows:
        d = r.day.date() if isinstance(r.day, datetime) else r.day
        by_day[d] = {
            "generations": int(r.generations),
            "input_tokens": int(r.input_tokens),
            "output_tokens": int(r.output_tokens),
        }
    daily = []
    first = now.date() - timedelta(days=days - 1)
    for i in range(days):
        d = first + timedelta(days=i)
        v = by_day.get(d, {"generations": 0, "input_tokens": 0, "output_tokens": 0})
        daily.append({"date": d.isoformat(), **v})

    return {
        "days": days,
        "active_users": active_users,
        "generations": generations,
        "tokens": tokens,
        "by_tool": by_tool,
        "by_provider": by_provider,
        "by_stage": by_stage,
        "top_users": top_users,
        "daily": daily,
    }


# ---------- foydalanuvchilar ----------


def _usage_subquery():
    return (
        select(
            UsageLog.user_id.label("uid"),
            func.count().label("generations_total"),
            func.coalesce(func.sum(UsageLog.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(UsageLog.output_tokens), 0).label("output_tokens"),
        )
        .where(UsageLog.action == "generate", UsageLog.user_id.is_not(None))
        .group_by(UsageLog.user_id)
        .subquery()
    )


def user_item(user: User, generations_total: int, input_tokens: int, output_tokens: int) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "plan": user.plan,
        "pro_until": user.pro_until,
        "bonus_generations": user.bonus_generations or 0,
        "generations_total": int(generations_total or 0),
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "is_admin": is_admin_email(user.email),
    }


async def list_users(session: AsyncSession, q: str = "", page: int = 1, limit: int = 50) -> dict:
    u = _usage_subquery()
    base = select(User).outerjoin(u, u.c.uid == User.id)
    count_q = select(func.count()).select_from(User)
    q = (q or "").strip()
    if q:
        pat = f"%{q}%"
        cond = or_(User.email.ilike(pat), User.name.ilike(pat))
        base = base.where(cond)
        count_q = count_q.where(cond)
    total = int(await session.scalar(count_q) or 0)
    rows = (
        await session.execute(
            base.add_columns(
                func.coalesce(u.c.generations_total, 0),
                func.coalesce(u.c.input_tokens, 0),
                func.coalesce(u.c.output_tokens, 0),
            )
            .order_by(User.last_login_at.desc().nulls_last(), User.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).all()
    items = [user_item(r[0], r[1], r[2], r[3]) for r in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


async def _get_user(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND)
    return user


async def _user_with_stats(session: AsyncSession, user: User) -> dict:
    u = _usage_subquery()
    row = (
        await session.execute(
            select(u.c.generations_total, u.c.input_tokens, u.c.output_tokens).where(
                u.c.uid == user.id
            )
        )
    ).one_or_none()
    if row is None:
        return user_item(user, 0, 0, 0)
    return user_item(user, row[0], row[1], row[2])


async def grant(
    session: AsyncSession,
    user_id: uuid.UUID,
    plan: str | None = None,
    pro_days: int | None = None,
    bonus_generations: int | None = None,
) -> dict:
    """Admin amali: reja/Pro muddati/bonus. Hech narsa berilmasa 422."""
    if plan is None and pro_days is None and bonus_generations is None:
        raise HTTPException(status_code=422, detail=NOTHING_TO_CHANGE)
    user = await _get_user(session, user_id)
    if plan is not None:
        set_plan(user, plan)
    if pro_days:
        extend_pro(user, pro_days)
    if bonus_generations:
        apply_bonus(user, bonus_generations)
    await session.commit()
    return await _user_with_stats(session, user)


# ---------- toʻlovlar ----------


def payment_item(p: Payment, email: str | None) -> dict:
    return {
        "id": p.id,
        "user_id": p.user_id,
        "email": email,
        "amount": p.amount,
        "currency": p.currency,
        "method": p.method,
        "days": p.days,
        "note": p.note,
        "provider_ref": p.provider_ref,
        "created_by": p.created_by,
        "paid_at": p.paid_at,
    }


async def list_payments(session: AsyncSession, page: int = 1, limit: int = 50) -> dict:
    total = int(await session.scalar(select(func.count()).select_from(Payment)) or 0)
    rows = (
        await session.execute(
            select(Payment, User.email)
            .outerjoin(User, User.id == Payment.user_id)
            .order_by(Payment.paid_at.desc(), Payment.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).all()
    items = [payment_item(r[0], r[1]) for r in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


async def create_payment(
    session: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    days: int,
    method: str = "manual",
    note: str | None = None,
    created_by: str | None = None,
) -> dict:
    """Toʻlov yoziladi va shu tranzaksiyada foydalanuvchi Pro'si `days` kunga uzayadi."""
    user = await _get_user(session, user_id)
    extend_pro(user, days)
    p = Payment(
        user_id=user.id,
        amount=amount,
        currency="UZS",
        method=method,
        days=days,
        note=note,
        created_by=created_by,
        paid_at=datetime.now(UTC),
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return payment_item(p, user.email)


# ---------- sozlamalar ----------


def _limit_defaults() -> dict[str, int]:
    s = get_settings()
    return {k: getattr(s, attr) for k, (attr, _, _) in app_settings.LIMIT_KEYS.items()}


async def get_settings_view(session: AsyncSession) -> dict:
    limits = await app_settings.get_limits(session)
    return {**limits, "defaults": _limit_defaults()}


async def update_settings(session: AsyncSession, values: dict[str, int]) -> dict:
    """Berilgan kalitlarni yozadi; chegaradan tashqari → 422 (oʻzbekcha)."""
    changes = {k: v for k, v in values.items() if k in app_settings.LIMIT_KEYS and v is not None}
    if not changes:
        raise HTTPException(status_code=422, detail=NOTHING_TO_CHANGE)
    for key, value in changes.items():
        try:
            await app_settings.set_int(session, key, value)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"Notoʻgʻri qiymat — {e}") from e
    await session.commit()
    app_settings.invalidate()
    return await get_settings_view(session)


__all__ = [
    "apply_bonus",
    "create_payment",
    "extend_pro",
    "get_settings_view",
    "grant",
    "list_payments",
    "list_users",
    "set_plan",
    "stats",
    "update_settings",
]
