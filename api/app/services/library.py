"""Tarix va kutubxona — `prompts` jadvali bilan ishlash (SQL shu yerda, router faqat HTTP).

- Tarix: kirgan foydalanuvchining hamma yasalgan promptlari (generate avtomatik saqlaydi).
- Kutubxona: foydalanuvchi «saqlash» bosgan promptlar (`is_saved = true`).
Hamma funksiya faqat shu foydalanuvchining qatorlari bilan ishlaydi — begona qator 404.
"""

import uuid

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
