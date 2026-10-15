"""Tarix va kutubxona — `prompts` jadvali bilan ishlash (SQL shu yerda, router faqat HTTP).

- Tarix: kirgan foydalanuvchining hamma yasalgan promptlari (generate avtomatik saqlaydi).
- Kutubxona: foydalanuvchi «saqlash» bosgan promptlar (`is_saved = true`).
Hamma funksiya faqat shu foydalanuvchining qatorlari bilan ishlaydi — begona qator 404.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Prompt

NOT_FOUND = "Bu prompt topilmadi."

PAGE_LIMIT_MAX = 100


def item(row: Prompt) -> dict:
    """Roʻyxat elementi (`schemas.HistoryItem` shakli)."""
    return {
        "id": row.id,
        "input_text": row.input_text,
        "kind": row.kind,
        "ai": row.ai,
        "result": row.result,
        "explanations": row.explanations,
        "score": row.score,
        "is_saved": bool(row.is_saved),
        "feedback": row.feedback,
        "created_at": row.created_at,
    }


async def list_prompts(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    limit: int = 20,
    saved_only: bool = False,
) -> dict:
    """Yangidan eskiga, sahifalab. `saved_only` — kutubxona."""
    where = [Prompt.user_id == user_id]
    if saved_only:
        where.append(Prompt.is_saved.is_(True))
    total = int(await session.scalar(select(func.count()).select_from(Prompt).where(*where)) or 0)
    rows = (
        (
            await session.execute(
                select(Prompt)
                .where(*where)
                .order_by(Prompt.created_at.desc(), Prompt.id.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return {"items": [item(r) for r in rows], "total": total, "page": page, "limit": limit}


async def _own(session: AsyncSession, user_id: uuid.UUID, prompt_id: uuid.UUID) -> Prompt:
    row = await session.scalar(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.user_id == user_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return row


async def set_saved(
    session: AsyncSession, user_id: uuid.UUID, prompt_id: uuid.UUID, saved: bool
) -> dict:
    """Kutubxonaga qoʻshish yoki olib tashlash. Yangilangan elementni qaytaradi."""
    row = await _own(session, user_id, prompt_id)
    row.is_saved = saved
    await session.commit()
    return item(row)


async def delete_prompt(session: AsyncSession, user_id: uuid.UUID, prompt_id: uuid.UUID) -> None:
    """Oʻz promptini oʻchirish (begona yoki yoʻq boʻlsa 404)."""
    await _own(session, user_id, prompt_id)
    await session.execute(delete(Prompt).where(Prompt.id == prompt_id, Prompt.user_id == user_id))
    await session.commit()


# --------------------------------------------------------------- «Prompt ishladimi?» (A.4)

#: Shu vaqtdan eski prompt haqida soʻraladi (odam natijani sinab koʻrgan boʻlishi kerak)
FEEDBACK_AFTER_HOURS = 6

ANSWERS: tuple[str, ...] = ("worked", "not_worked")


async def pending_feedback(session: AsyncSession, user_id: uuid.UUID) -> dict | None:
    """Javob berilmagan eng yangi prompt (soʻralishi kerak boʻlgani). Yoʻq boʻlsa `None`."""
    cutoff = datetime.now(UTC) - timedelta(hours=FEEDBACK_AFTER_HOURS)
    row = await session.scalar(
        select(Prompt)
        .where(
            Prompt.user_id == user_id,
            Prompt.feedback.is_(None),
            Prompt.created_at <= cutoff,
        )
        .order_by(Prompt.created_at.desc())
        .limit(1)
    )
    if row is None:
        return None
    return {
        "id": row.id,
        "kind": row.kind,
        "ai": row.ai,
        "input_text": row.input_text[:160],
        "score": row.score,
        "created_at": row.created_at,
    }


async def set_feedback(
    session: AsyncSession,
    user_id: uuid.UUID,
    prompt_id: uuid.UUID,
    answer: str,
    note: str | None = None,
) -> dict:
    """«Ishladi / ishlamadi» javobini yozadi. Begona yoki yoʻq prompt → 404."""
    if answer not in ANSWERS:
        raise HTTPException(status_code=422, detail=NOT_FOUND)
    row = await session.scalar(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.user_id == user_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    row.feedback = answer
    row.feedback_note = (note or "").strip()[:500] or None
    await session.commit()
    return item(row)
