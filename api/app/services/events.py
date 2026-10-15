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

#: Brauzer yuborishi mumkin boʻlgan hodisalar — faqat uning oʻzida sodir boʻladiganlar
CLIENT_EVENT_NAMES: frozenset[str] = frozenset(
    {
        "idea_submitted",
        "tool_selected",
        "questions_answered",
        "prompt_copied",
        "prompt_shared",
        "prompt_feedback",
        "voice_started",
        "voice_transcribed",
        "voice_failed",
    }
)

#: Faqat server yozadi — bu nomlarni brauzerdan qabul qilmaymiz, aks holda
#: istalgan odam soxta «prompt_generated» yuborib voronka raqamlarini buzadi.
SERVER_EVENT_NAMES: frozenset[str] = frozenset(
    {"type_detected", "prompt_generated", "limit_reached"}
)

EVENT_NAMES: frozenset[str] = CLIENT_EVENT_NAMES | SERVER_EVENT_NAMES

MAX_PAYLOAD_CHARS = 1500
MAX_VALUE_CHARS = 300
MAX_KEYS = 16


def _trim(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Payload'ni meʼyorga soladi.

    Har bir qiymat ham, **umumiy hajm ham** cheklanadi: kalit qoʻshilgandan keyin
    jami uzunlik `MAX_PAYLOAD_CHARS` dan oshsa, qolgani tashlab ketiladi. Shunday
    qilib bitta soʻrov bilan jadvalni shishirib boʻlmaydi.
    """
    if not payload:
        return None
    out: dict[str, Any] = {}
    size = 0
    for key, value in list(payload.items())[:MAX_KEYS]:
        k = str(key)[:40]
        if isinstance(value, str):
            v: Any = value[:MAX_VALUE_CHARS]
        elif isinstance(value, (int, float, bool)) or value is None:
            v = value
        else:
            v = str(value)[:MAX_VALUE_CHARS]
        size += len(k) + len(str(v)) + 4
        if size > MAX_PAYLOAD_CHARS:
            break
        out[k] = v
    return out or None


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
