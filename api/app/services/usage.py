"""Server tomondagi limitlar va hisob — `usage_log`, `llm_calls`, `prompts` jadvallari.

Limitlar (`services/settings.py` — admin oʻzgartira oladi, yoʻq boʻlsa `.env`):
- Pro (`user.is_pro`): cheksiz.
- Kirgan bepul: kuniga (24 soat) `free_daily_generations`; tugasa `bonus_generations` sarflanadi.
- Guest (kirmagan): jami `guest_total_generations` (`guest_id` boʻyicha) va IP kuniga
  `guest_daily_ip_generations` — guest_id almashtirib aylanib oʻtishni toʻxtatadi.
Hisob faqat muvaffaqiyatli ish (`done: ok`) tugagach yoziladi. Baza ishlamasa 503 (fail-closed).

Yozuvchi funksiyalar (`record_usage`, `record_llm_calls`, `consume_bonus_if_needed`, `save_prompt`)
oʻz sessiyasi bilan ishlaydi va xatoda faqat log yozadi — ishni (job) buzmaydi.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import LlmCall, Prompt, UsageLog, User
from app.schemas import GenerateRequest
from app.services import settings as app_settings

if TYPE_CHECKING:
    from app.ai.metering import Meter
    from app.services.jobs import Job

log = logging.getLogger(__name__)

GUEST_EXHAUSTED = "Bepul urinishlar tugadi. Davom etish uchun Google orqali kiring."
IP_EXHAUSTED = "Bugungi bepul limit tugadi. Ertaga qayta urinib koʻring yoki kiring."
USER_EXHAUSTED = "Bugungi bepul limit tugadi. Ertaga qayting yoki Pro'ga oʻting."
DB_DOWN = "Xizmat vaqtincha ishlamayapti. Birozdan soʻng urinib koʻring."


def _since() -> datetime:
    return datetime.now(UTC) - timedelta(days=1)


async def _user_daily_count(session: AsyncSession, user_id: uuid.UUID) -> int:
    n = await session.scalar(
        select(func.count())
        .select_from(UsageLog)
        .where(UsageLog.user_id == user_id, UsageLog.created_at >= _since())
    )
    return n or 0


async def check_quota(
    session: AsyncSession, user: User | None, guest_id: str | None, ip: str
) -> None:
    """Chegara oshgan boʻlsa 429; baza ishlamasa 503 (fail-closed).

    - Pro → oʻtadi.
    - Kirgan bepul: bugungi soni < free_daily_generations yoki bonus_generations > 0.
    - Guest: jami guest_total_generations va IP kuniga guest_daily_ip_generations.
    """
    try:
        if user is not None:
            if user.is_pro:
                return
            limit = await app_settings.get_int("free_daily_generations", session)
            used = await _user_daily_count(session, user.id)
            if used < limit or (user.bonus_generations or 0) > 0:
                return
            raise HTTPException(status_code=429, detail=USER_EXHAUSTED)

        guest_limit = await app_settings.get_int("guest_total_generations", session)
        ip_limit = await app_settings.get_int("guest_daily_ip_generations", session)
        if guest_id:
            total = await session.scalar(
                select(func.count()).select_from(UsageLog).where(UsageLog.guest_id == guest_id)
            )
            if (total or 0) >= guest_limit:
                raise HTTPException(status_code=429, detail=GUEST_EXHAUSTED)
        daily_ip = await session.scalar(
            select(func.count())
            .select_from(UsageLog)
            .where(UsageLog.ip == ip, UsageLog.created_at >= _since())
        )
        if (daily_ip or 0) >= ip_limit:
            raise HTTPException(status_code=429, detail=IP_EXHAUSTED)
    except HTTPException:
        raise
    except Exception:
        log.exception("usage_log oʻqib boʻlmadi")
        raise HTTPException(status_code=503, detail=DB_DOWN) from None


_check_quota_impl = check_quota


async def check_guest_quota(session: AsyncSession, guest_id: str | None, ip: str) -> None:
    """Eski nom: guest limiti = `check_quota(session, None, guest_id, ip)`."""
    await _check_quota_impl(session, None, guest_id, ip)


async def record_usage(
    *,
    user_id: uuid.UUID | None,
    guest_id: str | None,
    ip: str,
    ai: str | None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> None:
    """Muvaffaqiyatli generate'dan keyin `usage_log` qatori. Xato boʻlsa ishni buzmaydi — faqat log."""
    try:
        async with SessionLocal() as session:
            session.add(
                UsageLog(
                    user_id=user_id,
                    guest_id=guest_id,
                    ip=ip,
                    action="generate",
                    ai=ai,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            )
            await session.commit()
    except Exception:
        log.exception("usage_log yozib boʻlmadi")


async def record_llm_calls(meter: "Meter", job: "Job") -> None:
    """Job ichidagi har LLM chaqiruvi → `llm_calls` (ok ham, xato ham). Boʻsh boʻlsa hech narsa."""
    if not meter.calls:
        return
    try:
        async with SessionLocal() as session:
            session.add_all(
                LlmCall(
                    user_id=job.user_id,
                    guest_id=job.body.guest_id,
                    job_id=job.id,
                    stage=c.stage,
                    provider=c.provider,
                    model=c.model[:80],
                    input_tokens=c.input_tokens,
                    output_tokens=c.output_tokens,
                    estimated=c.estimated,
                    ok=c.ok,
                    duration_ms=c.duration_ms,
                )
                for c in meter.calls
            )
            await session.commit()
    except Exception:
        log.exception("llm_calls yozib boʻlmadi (job %s)", job.id)


async def consume_bonus_if_needed(user_id: uuid.UUID) -> None:
    """Bugungi hisob (hozirgi yozuv bilan) kunlik limitdan oshgan boʻlsa bonus 1 ga kamayadi."""
    try:
        async with SessionLocal() as session:
            user = await session.get(User, user_id)
            if user is None or user.is_pro or (user.bonus_generations or 0) <= 0:
                return
            limit = await app_settings.get_int("free_daily_generations", session)
            used = await _user_daily_count(session, user_id)
            if used > limit:
                user.bonus_generations = max(0, user.bonus_generations - 1)
                await session.commit()
    except Exception:
        log.exception("bonus sarflab boʻlmadi (user %s)", user_id)


async def save_prompt(
    user_id: uuid.UUID,
    body: GenerateRequest,
    done: dict,
    notes: list[str] | None,
) -> Prompt | None:
    """Kirgan foydalanuvchi uchun tarix: `prompts` qatori (avto-saqlash)."""
    try:
        async with SessionLocal() as session:
            row = Prompt(
                user_id=user_id,
                input_text=body.text,
                kind=str(done.get("kind") or body.kind or "text"),
                ai=str(done.get("ai") or body.ai or "chatgpt"),
                clarifications=dict(body.answers) or None,
                result=str(done.get("prompt") or ""),
                explanations=list(notes) if notes else None,
                locale=body.locale,
                output_language=body.output_language,
            )
            session.add(row)
            await session.commit()
            return row
    except Exception:
        log.exception("prompt saqlab boʻlmadi (user %s)", user_id)
        return None
