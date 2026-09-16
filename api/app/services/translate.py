"""Tayyor promptni foydalanuvchi tiliga tarjima qilish (Tahrirchi Tilmoch).

Prompt AI vositasiga **inglizcha** yuboriladi (modellar inglizchaga yaxshi javob beradi) — tarjima
faqat foydalanuvchi nima nusxalayotganini tushunishi uchun. Shuning uchun talab boʻyicha
(foydalanuvchi tugmani bosganda) chaqiriladi va natija keshlanadi: har belgi pullik.

Hujjat: https://developer.tahrirchi.uz/uz/docs
"""

import hashlib
import logging
import time

import httpx
from fastapi import HTTPException

from app.config import get_settings

log = logging.getLogger(__name__)

# Tahrirchi til kodlari (NLLB uslubi)
LANG_CODES = {"uz": "uzn_Latn", "ru": "rus_Cyrl", "en": "eng_Latn"}
MAX_CHARS = 5000  # bitta soʻrov chegarasi (hujjatdan)
CACHE_TTL = 30 * 60
CACHE_MAX = 300

NOT_CONFIGURED = "Tarjima xizmati sozlanmagan."
TOO_LONG = "Matn juda uzun — tarjima qilib boʻlmadi."
FAILED = "Tarjima qilib boʻlmadi. Birozdan soʻng urinib koʻring."

_cache: dict[str, tuple[float, str]] = {}


def _key(text: str, target: str) -> str:
    return hashlib.sha256(f"{target}\n{text}".encode()).hexdigest()


def is_configured() -> bool:
    return bool(get_settings().tahrirchi_api_key)


async def translate(text: str, target_locale: str, source_locale: str = "en") -> str:
    """Matnni tarjima qiladi. Kesh 30 daqiqa. Xato → HTTPException (oʻzbekcha)."""
    s = get_settings()
    if not s.tahrirchi_api_key:
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED)
    text = text.strip()
    if not text:
        return ""
    if len(text) > MAX_CHARS:
        raise HTTPException(status_code=422, detail=TOO_LONG)
    target = LANG_CODES.get(target_locale, LANG_CODES["uz"])
    source = LANG_CODES.get(source_locale, LANG_CODES["en"])
    if target == source:
        return text

    key = _key(text, target)
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL:
        return hit[1]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                s.tahrirchi_url,
                headers={"Authorization": s.tahrirchi_api_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "source_lang": source,
                    "target_lang": target,
                    "model": s.tahrirchi_model,
                },
            )
    except httpx.HTTPError as e:
        log.warning("tahrirchi ulanmadi: %s", str(e)[:200])
        raise HTTPException(status_code=503, detail=FAILED) from e
    if r.status_code != 200:
        log.warning("tahrirchi %s: %s", r.status_code, r.text[:200])
        raise HTTPException(status_code=503, detail=FAILED)
    out = (r.json() or {}).get("translated_text", "").strip()
    if not out:
        raise HTTPException(status_code=503, detail=FAILED)

    if len(_cache) >= CACHE_MAX:
        _cache.pop(next(iter(_cache)))
    _cache[key] = (time.monotonic(), out)
    return out


def reset_cache_for_tests() -> None:
    _cache.clear()
