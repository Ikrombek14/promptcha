"""Anthropic klienti. Faqat AI_PROVIDER=anthropic boʻlganda ishlatiladi (app.ai.llm orqali)."""

from functools import lru_cache

import anthropic

from app.config import get_settings

# temperature SDK 1.x imzosidan olib tashlangan; API'da faqat 4.6/4.5 oilasi qabul qiladi.
_TEMPERATURE_MODELS = ("4-6", "4-5")


@lru_cache
def get_client() -> anthropic.AsyncAnthropic:
    s = get_settings()
    return anthropic.AsyncAnthropic(
        api_key=s.anthropic_api_key or None, max_retries=2, timeout=60.0
    )


def request_kwargs(*, max_tokens: int | None = None, quality: bool = False) -> dict:
    """Har bir chaqiruv uchun umumiy parametrlar: model, max_tokens (≤ limit), temperature.

    `quality=True` — «Yaxshilash» uchun kuchliroq model. Sonnet 5 va yangi oilalar `temperature`ni
    rad etadi (400 «deprecated»), shuning uchun u faqat 4.6/4.5 modellariga yuboriladi.
    """
    s = get_settings()
    model = (s.anthropic_quality_model if quality else "") or s.anthropic_model
    kwargs: dict = {
        "model": model,
        "max_tokens": min(max_tokens or s.ai_max_tokens, s.ai_max_tokens),
    }
    if any(tag in model for tag in _TEMPERATURE_MODELS):
        kwargs["extra_body"] = {"temperature": s.ai_temperature}
    return kwargs


def cached_system(system: str) -> list[dict]:
    """System prompt keshlanadigan blok sifatida — playbook/namunalar koʻp soʻrovda bir xil."""
    return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
