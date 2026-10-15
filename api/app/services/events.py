"""Mahsulot hodisalarini yozish (`events` jadvali).

Qoida: hodisa yozuvi asosiy oqimni **hech qachon** sekinlashtirmaydi va yiqitmaydi —
yozish alohida vazifada ketadi, har qanday xato log'ga tushadi va yutiladi.

Voronka: `idea_submitted` → `type_detected` → `prompt_generated` → `prompt_copied`
→ `prompt_feedback`. Toʻliq roʻyxat: `docs/promptcha-redesign/TASKS.md` (A.1).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from app.db import SessionLocal
from app.models import Event

log = logging.getLogger(__name__)

#: Faqat shu nomlar qabul qilinadi — tasodifiy/begona hodisa jadvalni ifloslantirmasin
EVENT_NAMES: frozenset[str] = frozenset(
    {
        "idea_submitted",
        "type_detected",
        "tool_selected",
        "questions_answered",
        "prompt_generated",
        "prompt_copied",
        "prompt_shared",
        "limit_reached",
        "prompt_feedback",
        "voice_started",
        "voice_transcribed",
        "voice_failed",
    }
)

MAX_PAYLOAD_CHARS = 4000


def _trim(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Payload'ni meʼyorga soladi: uzun matnlar kesiladi, ichma-ich obyektlar matnga aylanadi."""
    if not payload:
        return None
    out: dict[str, Any] = {}
    for key, value in list(payload.items())[:20]:
        k = str(key)[:40]
        if isinstance(value, str):
            out[k] = value[:1000]
        elif isinstance(value, (int, float, bool)) or value is None:
            out[k] = value
        else:
            out[k] = str(value)[:1000]
    text = str(out)
    if len(text) > MAX_PAYLOAD_CHARS:  # pragma: no cover — juda kam uchraydi
        out = {"_trimmed": text[:MAX_PAYLOAD_CHARS]}
    return out


async def _write(
    name: str,
    payload: dict[str, Any] | None,
    user_id: uuid.UUID | None,
    guest_id: str | None,
    session_id: str | None,
) -> None:
    try:
        async with SessionLocal() as session:
            session.add(
                Event(
                    name=name,
                    payload=_trim(payload),
                    user_id=user_id,
                    guest_id=(guest_id or None) and str(guest_id)[:64],
                    session_id=(session_id or None) and str(session_id)[:64],
                )
            )
            await session.commit()
    except Exception:
        log.warning("hodisa yozilmadi: %s", name, exc_info=True)


def record(
    name: str,
    payload: dict[str, Any] | None = None,
    *,
    user_id: uuid.UUID | None = None,
    guest_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Hodisani fon rejimida yozadi. Hech narsa qaytarmaydi va hech qachon xato bermaydi."""
    if name not in EVENT_NAMES:
        log.warning("notanish hodisa nomi: %s", name)
        return
    try:
        task = asyncio.create_task(_write(name, payload, user_id, guest_id, session_id))
        # Vazifa yigʻilib qolmasin (GC uni oʻchirib yubormasligi uchun havola saqlanadi)
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    except RuntimeError:  # pragma: no cover — hodisa tsiklsiz kontekst (testlar)
        log.debug("hodisa uchun event loop yoʻq: %s", name)


_tasks: set[asyncio.Task] = set()
