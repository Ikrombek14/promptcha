"""Server tomondagi limitlar — `usage_log` jadvali boʻyicha (brauzerni tozalash yordam bermaydi).

- Guest (kirmagan): jami `GUEST_TOTAL_GENERATIONS` (3) muvaffaqiyatli generate, `guest_id` boʻyicha.
- IP: kuniga `GUEST_DAILY_IP_GENERATIONS` — guest_id almashtirib aylanib oʻtishni toʻxtatadi.
- Kirgan foydalanuvchi: kuniga `FREE_DAILY_GENERATIONS` (auth kelganda ulanadi).
Hisob faqat muvaffaqiyatli ish (`done: ok`) tugagach yoziladi.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.models import UsageLog

log = logging.getLogger(__name__)

GUEST_EXHAUSTED = "Bepul urinishlar tugadi. Davom etish uchun Google orqali kiring."
IP_EXHAUSTED = "Bugungi bepul limit tugadi. Ertaga qayta urinib koʻring yoki kiring."
DB_DOWN = "Xizmat vaqtincha ishlamayapti. Birozdan soʻng urinib koʻring."


async def check_guest_quota(session: AsyncSession, guest_id: str | None, ip: str) -> None:
    """Chegara oshgan boʻlsa 429; baza ishlamasa 503 (fail-closed)."""
    s = get_settings()
    since = datetime.now(UTC) - timedelta(days=1)
    try:
        if guest_id:
            total = await session.scalar(
                select(func.count()).select_from(UsageLog).where(UsageLog.guest_id == guest_id)
            )
            if (total or 0) >= s.guest_total_generations:
                raise HTTPException(status_code=429, detail=GUEST_EXHAUSTED)
        daily_ip = await session.scalar(
            select(func.count())
            .select_from(UsageLog)
            .where(UsageLog.ip == ip, UsageLog.created_at >= since)
        )
        if (daily_ip or 0) >= s.guest_daily_ip_generations:
            raise HTTPException(status_code=429, detail=IP_EXHAUSTED)
    except HTTPException:
        raise
    except Exception:
        log.exception("usage_log oʻqib boʻlmadi")
        raise HTTPException(status_code=503, detail=DB_DOWN) from None


async def record_usage(guest_id: str | None, ip: str, ai: str | None) -> None:
    """Muvaffaqiyatli generate'dan keyin. Xato boʻlsa ishni buzmaydi — faqat log."""
    try:
        async with SessionLocal() as session:
            session.add(UsageLog(guest_id=guest_id, ip=ip, action="generate", ai=ai))
            await session.commit()
    except Exception:
        log.exception("usage_log yozib boʻlmadi")
