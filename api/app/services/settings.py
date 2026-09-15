"""Admin oʻzgartiradigan sozlamalar (`app_settings` jadvali) — limitlar.

Kalit yoʻq boʻlsa `.env` (Settings) qiymati. 60 s xotira keshi; admin yozganda darhol yangilanadi.
Baza ishlamasa .env qiymati qaytadi (sayt toʻxtamaydi).
"""

import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.models import AppSetting

log = logging.getLogger(__name__)

CACHE_TTL = 60.0

# kalit → (.env atributi, min, max)
LIMIT_KEYS: dict[str, tuple[str, int, int]] = {
    "guest_total_generations": ("guest_total_generations", 0, 1000),
    "guest_daily_ip_generations": ("guest_daily_ip_generations", 0, 10000),
    "free_daily_generations": ("free_daily_generations", 0, 1000),
}

_cache: dict[str, str] = {}
_cache_at: float = 0.0


def invalidate() -> None:
    global _cache_at
    _cache_at = 0.0


def _defaults() -> dict[str, int]:
    s = get_settings()
    return {k: getattr(s, attr) for k, (attr, _, _) in LIMIT_KEYS.items()}


async def _load(session: AsyncSession | None) -> dict[str, str]:
    global _cache, _cache_at
    if time.monotonic() - _cache_at < CACHE_TTL:
        return _cache
    try:
        if session is not None:
            rows = (await session.execute(select(AppSetting))).scalars().all()
        else:
            async with SessionLocal() as own:
                rows = (await own.execute(select(AppSetting))).scalars().all()
        _cache = {r.key: r.value for r in rows}
        _cache_at = time.monotonic()
    except Exception:
        log.exception("app_settings oʻqib boʻlmadi — .env qiymatlari")
        _cache_at = time.monotonic()  # bazani har soʻrovda urmaslik uchun
    return _cache


async def get_int(key: str, session: AsyncSession | None = None) -> int:
    """Limit qiymati: app_settings → .env."""
    defaults = _defaults()
    if key not in defaults:
        raise KeyError(key)
    values = await _load(session)
    raw = values.get(key)
    if raw is None:
        return defaults[key]
    try:
        return int(raw)
    except ValueError:
        return defaults[key]


async def get_limits(session: AsyncSession | None = None) -> dict[str, int]:
    return {k: await get_int(k, session) for k in LIMIT_KEYS}


async def set_int(session: AsyncSession, key: str, value: int) -> None:
    """Admin yozadi; chegaradan tashqari qiymat ValueError. Commit chaqiruvchi zimmasida."""
    if key not in LIMIT_KEYS:
        raise KeyError(key)
    _, lo, hi = LIMIT_KEYS[key]
    if not lo <= value <= hi:
        raise ValueError(f"{key}: {lo}–{hi} oraligʻida boʻlishi kerak")
    row = await session.get(AppSetting, key)
    if row is None:
        session.add(AppSetting(key=key, value=str(value)))
    else:
        row.value = str(value)
    invalidate()
