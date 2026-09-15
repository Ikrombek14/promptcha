"""Provayder qatlami: pipeline faqat shu ikkita funksiyani biladi.

parse(system, user, Schema)  → Schema  (structured output)
stream(system, user)         → matn boʻlaklari

AI_PROVIDERS — vergul bilan zanjir (masalan "gemini,groq,mistral,openrouter"). Kaliti yoʻq
provayder tashlab ketiladi. Kvota (429) yoki band (5xx) boʻlsa keyingi provayderga oʻtiladi.
Har provayder ichida ham model zaxiralari bor (*_FALLBACK_MODELS). Xatolar ProviderError.
"""

import json
import logging
import re
import time
from collections.abc import AsyncIterator
from functools import lru_cache

from pydantic import BaseModel, ValidationError

from app.ai import metering
from app.config import Settings, get_settings

log = logging.getLogger(__name__)


def _ms(t0: float) -> int:
    return int((time.monotonic() - t0) * 1000)


def _record(
    provider: str,
    model: str,
    t0: float,
    *,
    input_tokens: int | None,
    output_tokens: int | None,
    input_text: str,
    output_text: str = "",
    ok: bool = True,
) -> None:
    """Har bir provayder chaqiruvi shu orqali oʻlchanadi (meter yoʻq boʻlsa jim)."""
    metering.record(
        provider,
        model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_text=input_text,
        output_text=output_text,
        ok=ok,
        duration_ms=_ms(t0),
    )


class ProviderError(Exception):
    """Foydalanuvchiga koʻrsatiladigan xato (oʻzbekcha)."""


class _Retryable(Exception):
    """Ichki: bu provayder hozir band/kvota tugagan — keyingisiga oʻtish mumkin."""

    def __init__(self, error: ProviderError):
        super().__init__(str(error))
        self.error = error


class MidStreamError(ProviderError):
    """Matn chiqa boshlagandan keyin provayder uzildi (503 va h.k.).

    Boshqa modelga jimgina oʻtib boʻlmaydi — mijoz allaqachon boʻlaklarni olgan.
    Pipeline buni ushlab `reset` hodisasi beradi va generate'ni qaytadan boshlaydi.
    """


def _models(primary: str, fallbacks: str) -> list[str]:
    out = [primary.strip()] if primary.strip() else []
    for m in fallbacks.split(","):
        m = m.strip()
        if m and m not in out:
            out.append(m)
    return out


def _wait_text(e: Exception) -> str:
    m = re.search(r"retry(?: in| after)?:? (\d+)", str(e), re.IGNORECASE)
    return f"{int(m.group(1)) + 1} soniyadan" if m else "bir daqiqadan"


def _busy(e: Exception) -> ProviderError:
    return ProviderError(f"AI xizmati band. {_wait_text(e).capitalize()} soʻng urinib koʻring.")


# --------------------------------------------------------------------------- Gemini


@lru_cache
def _gemini_client():
    from google import genai
    from google.genai import types

    # SDK ichidagi qayta urinishlar qisqa: 503 boʻlsa tez orada oʻz zaxira modelimizga oʻtamiz
    return genai.Client(
        api_key=get_settings().gemini_api_key or None,
        http_options=types.HttpOptions(
            timeout=30_000,
            retry_options=types.HttpRetryOptions(attempts=2, initial_delay=0.5, max_delay=2.0),
        ),
    )


def _gemini_config(system: str, max_tokens: int, schema: type[BaseModel] | None):
    from google.genai import types

    s = get_settings()
    kw: dict = {
        "system_instruction": system,
        "temperature": s.ai_temperature,
        "max_output_tokens": min(max_tokens, s.ai_max_tokens),
    }
    # Gemini 3.x: fikrlash tokenlari max_output_tokens ichida sanaladi — past daraja tutiladi.
    # (thinking_budget=0 3.x'da 400 qaytaradi; thinking_level: minimal | low | medium | high)
    if s.gemini_thinking_level:
        kw["thinking_config"] = types.ThinkingConfig(thinking_level=s.gemini_thinking_level)
    if schema is not None:
        kw["response_mime_type"] = "application/json"
        kw["response_schema"] = schema
    return types.GenerateContentConfig(**kw)


def _gemini_error(e: Exception) -> ProviderError:
    from google.genai import errors

    log.warning("gemini xatosi: %s: %s", type(e).__name__, str(e)[:500])
    if isinstance(e, errors.APIError):
        code = getattr(e, "code", None)
        if code in (401, 403):
            return ProviderError("AI xizmati sozlanmagan (API kalit notoʻgʻri).")
        if code == 429:
            return _busy(e)
        return ProviderError(f"AI xizmatida xatolik ({code}). Qayta urinib koʻring.")
    return ProviderError("AI xizmatiga ulanib boʻlmadi. Internetni tekshiring.")


def _gemini_retryable(e: Exception) -> bool:
    from google.genai import errors

    return isinstance(e, errors.APIError) and getattr(e, "code", None) in (429, 503)


def _gemini_usage(resp) -> tuple[int | None, int | None]:
    """(prompt_token_count, candidates_token_count + thoughts) — usage_metadata boʻlmasa (None, None)."""
    u = getattr(resp, "usage_metadata", None)
    if u is None:
        return None, None
    out = getattr(u, "candidates_token_count", None)
    thoughts = getattr(u, "thoughts_token_count", None)
    if out is not None and thoughts:
        out += thoughts  # fikrlash tokenlari ham chiqish sifatida hisoblanadi
    return getattr(u, "prompt_token_count", None), out


async def _gemini_parse[T: BaseModel](
    system: str, user: str, schema: type[T], max_tokens: int
) -> T:
    s = get_settings()
    config = _gemini_config(system, max_tokens, schema)
    prompt_text = system + user
    last: Exception | None = None
    for model in _models(s.gemini_model, s.gemini_fallback_models):
        t0 = time.monotonic()
        try:
            resp = await _gemini_client().aio.models.generate_content(
                model=model, contents=user, config=config
            )
        except Exception as e:
            _record(
                "gemini",
                model,
                t0,
                input_tokens=None,
                output_tokens=0,
                input_text=prompt_text,
                ok=False,
            )
            if _gemini_retryable(e):
                log.warning("gemini %s band (%s) — keyingi model", model, getattr(e, "code", "?"))
                last = e
                continue
            raise _gemini_error(e) from e
        text = resp.text or ""
        inp, out = _gemini_usage(resp)
        _record(
            "gemini",
            model,
            t0,
            input_tokens=inp,
            output_tokens=out,
            input_text=prompt_text,
            output_text=text,
        )
        parsed = resp.parsed
        if isinstance(parsed, schema):
            return parsed
        if text:
            return _parse_json(schema, text)
        raise ProviderError("AI javobi boʻsh keldi. Qayta urinib koʻring.")
    assert last is not None
    raise _Retryable(_gemini_error(last)) from last


async def _gemini_stream(system: str, user: str, max_tokens: int) -> AsyncIterator[str]:
    s = get_settings()
    config = _gemini_config(system, max_tokens, None)
    prompt_text = system + user
    last: Exception | None = None
    for model in _models(s.gemini_model, s.gemini_fallback_models):
        yielded = False
        parts: list[str] = []
        usage: tuple[int | None, int | None] = (None, None)
        t0 = time.monotonic()
        try:
            st = await _gemini_client().aio.models.generate_content_stream(
                model=model, contents=user, config=config
            )
            async for chunk in st:
                # usage_metadata odatda oxirgi boʻlakda toʻliq keladi
                u = _gemini_usage(chunk)
                if u[0] is not None or u[1] is not None:
                    usage = u
                if chunk.text:
                    yielded = True
                    parts.append(chunk.text)
                    yield chunk.text
            _record(
                "gemini",
                model,
                t0,
                input_tokens=usage[0],
                output_tokens=usage[1],
                input_text=prompt_text,
                output_text="".join(parts),
            )
            return
        except Exception as e:
            _record(
                "gemini",
                model,
                t0,
                input_tokens=None,
                output_tokens=None,
                input_text=prompt_text,
                output_text="".join(parts),
                ok=False,
            )
            if _gemini_retryable(e):
                if yielded:
                    # Matn chiqa boshlagan — pipeline `reset` berib qaytadan boshlaydi
                    raise MidStreamError(str(_gemini_error(e))) from e
                log.warning("gemini %s band (%s) — keyingi model", model, getattr(e, "code", "?"))
                last = e
                continue
            raise _gemini_error(e) from e
    assert last is not None
    raise _Retryable(_gemini_error(last)) from last


# --------------------------------------------------------------------------- OpenAI-mos
# Groq, Mistral, OpenRouter va istalgan boshqa /v1/chat/completions server (custom).

_OPENAI_COMPAT: dict[str, str] = {
    "groq": "https://api.groq.com/openai/v1",
    "mistral": "https://api.mistral.ai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "sambanova": "https://api.sambanova.ai/v1",
    "huggingface": "https://router.huggingface.co/v1",
    "hyperbolic": "https://api.hyperbolic.xyz/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "cohere": "https://api.cohere.ai/compatibility/v1",
    "custom": "",  # CUSTOM_BASE_URL dan olinadi (masalan lokal Ollama)
}


def _openai_settings(name: str, s: Settings) -> tuple[str, str, list[str]]:
    """(base_url, api_key, models)"""
    base = s.custom_base_url if name == "custom" else _OPENAI_COMPAT[name]
    key = getattr(s, f"{name}_api_key")
    models = _models(getattr(s, f"{name}_model"), getattr(s, f"{name}_fallback_models"))
    return base, key, models


@lru_cache
def _openai_client(name: str):
    import openai

    base, key, _ = _openai_settings(name, get_settings())
    headers = (
        {"HTTP-Referer": "https://promptcha.uz", "X-Title": "Promptcha"}
        if name == "openrouter"
        else None
    )
    return openai.AsyncOpenAI(
        base_url=base, api_key=key, max_retries=1, timeout=60.0, default_headers=headers
    )


def _openai_retryable(e: Exception) -> bool:
    import openai

    if isinstance(e, openai.RateLimitError | openai.APIConnectionError):
        return True
    return isinstance(e, openai.APIStatusError) and e.status_code in (500, 502, 503, 529)


def _openai_error(name: str, e: Exception) -> ProviderError:
    import openai

    log.warning("%s xatosi: %s: %s", name, type(e).__name__, str(e)[:500])
    if isinstance(e, openai.AuthenticationError):
        return ProviderError("AI xizmati sozlanmagan (API kalit notoʻgʻri).")
    if isinstance(e, openai.RateLimitError):
        return _busy(e)
    if isinstance(e, openai.APIConnectionError):
        return ProviderError("AI xizmatiga ulanib boʻlmadi. Internetni tekshiring.")
    if isinstance(e, openai.APIStatusError):
        return ProviderError(f"AI xizmatida xatolik ({e.status_code}). Qayta urinib koʻring.")
    return ProviderError("AI xizmatida kutilmagan xatolik. Qayta urinib koʻring.")


def _json_system(system: str, schema: type[BaseModel]) -> str:
    return (
        f"{system}\n\n<output_format>\nRespond with ONE JSON object that matches this JSON "
        "Schema exactly. No prose, no markdown fences, no comments.\n"
        f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}\n</output_format>"
    )


_DOUBLE_ESCAPED_UNICODE = re.compile(r"\\\\u([0-9a-fA-F]{4})")


def _parse_json[T: BaseModel](schema: type[T], text: str) -> T:
    """Model javobidan JSON obyektni ajratib, sxemaga tekshiradi."""
    raw = text.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
    if not raw.startswith("{"):
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            raw = raw[start : end + 1]
    # Model ʻ kabi harflarni ikki backslash bilan yozsa dekoder matn deb oʻtkazadi — bittaga tushiramiz
    raw = _DOUBLE_ESCAPED_UNICODE.sub(r"\\u\1", raw)
    try:
        return schema.model_validate_json(raw)
    except ValidationError as e:
        log.warning("json sxemaga mos emas: %s | %s", str(e)[:200], raw[:200])
        raise ProviderError("AI javobini oʻqib boʻlmadi. Qayta urinib koʻring.") from e


async def _openai_parse[T: BaseModel](
    name: str, system: str, user: str, schema: type[T], max_tokens: int
) -> T:
    import openai

    s = get_settings()
    _, _, models = _openai_settings(name, s)
    client = _openai_client(name)
    messages = [
        {"role": "system", "content": _json_system(system, schema)},
        {"role": "user", "content": user},
    ]
    # Fikrlovchi modellar (gpt-oss, qwen3) fikrlash tokenlarini ham max_tokens'dan oladi —
    # qisqa JSON uchun ham toʻliq limit beriladi, aks holda javob boʻsh qoladi.
    common = {
        "messages": messages,
        "temperature": s.ai_temperature,
        "max_tokens": s.ai_max_tokens,
    }
    prompt_text = messages[0]["content"] + user
    # Groq gpt-oss: fikrlashni qisqartirish (boshqa provayderlar 400 bersa, usiz qayta)
    extra = {"reasoning_effort": "low"} if name == "groq" else {}
    last: Exception | None = None
    for model in models:
        t0 = time.monotonic()
        try:
            try:
                resp = await client.chat.completions.create(
                    model=model, response_format={"type": "json_object"}, **common, **extra
                )
            except openai.BadRequestError:
                # Baʼzi modellar response_format / reasoning_effort'ni qabul qilmaydi — usiz qayta
                resp = await client.chat.completions.create(model=model, **common)
        except Exception as e:
            _record(
                name,
                model,
                t0,
                input_tokens=None,
                output_tokens=None,
                input_text=prompt_text,
                ok=False,
            )
            if _openai_retryable(e):
                log.warning("%s %s band — keyingi model", name, model)
                last = e
                continue
            raise _openai_error(name, e) from e
        text = resp.choices[0].message.content or ""
        inp, out = _openai_usage(resp)
        _record(
            name,
            model,
            t0,
            input_tokens=inp,
            output_tokens=out,
            input_text=prompt_text,
            output_text=text,
        )
        if not text.strip():
            raise ProviderError("AI javobi boʻsh keldi. Qayta urinib koʻring.")
        return _parse_json(schema, text)
    assert last is not None
    raise _Retryable(_openai_error(name, last)) from last


def _openai_usage(resp) -> tuple[int | None, int | None]:
    """(prompt_tokens, completion_tokens) — usage boʻlmasa (None, None)."""
    u = getattr(resp, "usage", None)
    if u is None:
        return None, None
    return getattr(u, "prompt_tokens", None), getattr(u, "completion_tokens", None)


async def _openai_stream(name: str, system: str, user: str, max_tokens: int) -> AsyncIterator[str]:
    import openai

    s = get_settings()
    _, _, models = _openai_settings(name, s)
    client = _openai_client(name)
    prompt_text = system + user
    common = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": s.ai_temperature,
        "max_tokens": min(max_tokens, s.ai_max_tokens),
        "stream": True,
    }
    # Qoʻshimchalar: oxirgi boʻlakda usage (token hisobi) + Groq'da qisqa fikrlash.
    # Provayder 400 bersa — usiz qayta.
    extra: dict = {"stream_options": {"include_usage": True}}
    if name == "groq":
        extra["reasoning_effort"] = "low"
    last: Exception | None = None
    for model in models:
        yielded = False
        parts: list[str] = []
        usage: tuple[int | None, int | None] = (None, None)
        t0 = time.monotonic()
        try:
            try:
                st = await client.chat.completions.create(model=model, **common, **extra)
            except openai.BadRequestError:
                st = await client.chat.completions.create(model=model, **common)
            async for chunk in st:
                u = _openai_usage(chunk)
                if u[0] is not None or u[1] is not None:
                    usage = u
                if not chunk.choices:
                    continue
                text = chunk.choices[0].delta.content
                if text:
                    yielded = True
                    parts.append(text)
                    yield text
            _record(
                name,
                model,
                t0,
                input_tokens=usage[0],
                output_tokens=usage[1],
                input_text=prompt_text,
                output_text="".join(parts),
            )
            return
        except Exception as e:
            _record(
                name,
                model,
                t0,
                input_tokens=None,
                output_tokens=None,
                input_text=prompt_text,
                output_text="".join(parts),
                ok=False,
            )
            if _openai_retryable(e):
                if yielded:
                    raise MidStreamError(str(_openai_error(name, e))) from e
                log.warning("%s %s band — keyingi model", name, model)
                last = e
                continue
            raise _openai_error(name, e) from e
    assert last is not None
    raise _Retryable(_openai_error(name, last)) from last


# --------------------------------------------------------------------------- Anthropic


def _anthropic_error(e: Exception) -> ProviderError:
    import anthropic

    log.warning("anthropic xatosi: %s: %s", type(e).__name__, str(e)[:500])
    if isinstance(e, anthropic.AuthenticationError):
        return ProviderError("AI xizmati sozlanmagan (API kalit notoʻgʻri).")
    if isinstance(e, anthropic.RateLimitError):
        return _busy(e)
    if isinstance(e, anthropic.APIConnectionError):
        return ProviderError("AI xizmatiga ulanib boʻlmadi. Internetni tekshiring.")
    if isinstance(e, anthropic.APIStatusError):
        return ProviderError(f"AI xizmatida xatolik ({e.status_code}). Qayta urinib koʻring.")
    return ProviderError("AI xizmatida kutilmagan xatolik. Qayta urinib koʻring.")


def _anthropic_retryable(e: Exception) -> bool:
    import anthropic

    if isinstance(e, anthropic.RateLimitError | anthropic.APIConnectionError):
        return True
    return isinstance(e, anthropic.APIStatusError) and e.status_code in (500, 502, 503, 529)


async def _anthropic_parse[T: BaseModel](
    system: str, user: str, schema: type[T], max_tokens: int
) -> T:
    from app.ai.client import get_client, request_kwargs

    kw = request_kwargs(max_tokens=max_tokens)
    model = kw["model"]
    prompt_text = system + user
    t0 = time.monotonic()
    try:
        resp = await get_client().messages.parse(
            **kw,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=schema,
        )
    except Exception as e:
        _record(
            "anthropic",
            model,
            t0,
            input_tokens=None,
            output_tokens=None,
            input_text=prompt_text,
            ok=False,
        )
        err = _anthropic_error(e)
        raise (_Retryable(err) if _anthropic_retryable(e) else err) from e
    inp, out = _anthropic_usage(resp)
    _record(
        "anthropic",
        model,
        t0,
        input_tokens=inp,
        output_tokens=out,
        input_text=prompt_text,
        output_text=_anthropic_text(resp),
    )
    return resp.parsed_output


def _anthropic_usage(msg) -> tuple[int | None, int | None]:
    u = getattr(msg, "usage", None)
    if u is None:
        return None, None
    return getattr(u, "input_tokens", None), getattr(u, "output_tokens", None)


def _anthropic_text(msg) -> str:
    return "".join(getattr(b, "text", "") or "" for b in (getattr(msg, "content", None) or []))


async def _anthropic_stream(system: str, user: str, max_tokens: int) -> AsyncIterator[str]:
    from app.ai.client import get_client, request_kwargs

    kw = request_kwargs(max_tokens=max_tokens)
    model = kw["model"]
    prompt_text = system + user
    yielded = False
    parts: list[str] = []
    t0 = time.monotonic()
    try:
        async with get_client().messages.stream(
            **kw,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as st:
            async for chunk in st.text_stream:
                yielded = True
                parts.append(chunk)
                yield chunk
            final = await st.get_final_message()
    except Exception as e:
        _record(
            "anthropic",
            model,
            t0,
            input_tokens=None,
            output_tokens=None,
            input_text=prompt_text,
            output_text="".join(parts),
            ok=False,
        )
        err = _anthropic_error(e)
        if _anthropic_retryable(e):
            raise (MidStreamError(str(err)) if yielded else _Retryable(err)) from e
        raise err from e
    inp, out = _anthropic_usage(final)
    _record(
        "anthropic",
        model,
        t0,
        input_tokens=inp,
        output_tokens=out,
        input_text=prompt_text,
        output_text="".join(parts),
    )


# --------------------------------------------------------------------------- zanjir


def _has_key(name: str, s: Settings) -> bool:
    if name == "gemini":
        return bool(s.gemini_api_key)
    if name == "anthropic":
        return bool(s.anthropic_api_key)
    if name == "custom":
        return bool(s.custom_base_url and s.custom_model)
    return bool(getattr(s, f"{name}_api_key", ""))


def providers() -> list[str]:
    """AI_PROVIDERS tartibida, faqat sozlangan (kaliti bor) va tanish provayderlar."""
    s = get_settings()
    known = {"gemini", "anthropic", *_OPENAI_COMPAT}
    out: list[str] = []
    for name in s.ai_providers.split(","):
        name = name.strip().lower()
        if not name or name in out:
            continue
        if name not in known:
            log.warning("notanish AI provayder: %s", name)
            continue
        if not _has_key(name, s):
            continue
        out.append(name)
    return out


async def parse[T: BaseModel](system: str, user: str, schema: type[T], max_tokens: int = 600) -> T:
    last: _Retryable | None = None
    for name in providers():
        try:
            if name == "gemini":
                return await _gemini_parse(system, user, schema, max_tokens)
            if name == "anthropic":
                return await _anthropic_parse(system, user, schema, max_tokens)
            return await _openai_parse(name, system, user, schema, max_tokens)
        except _Retryable as r:
            log.warning("%s band — keyingi provayder", name)
            last = r
    if last is not None:
        raise last.error
    raise ProviderError("AI provayder sozlanmagan (API kalit yoʻq).")


async def stream(system: str, user: str, max_tokens: int | None = None) -> AsyncIterator[str]:
    mt = max_tokens or get_settings().ai_max_tokens
    last: _Retryable | None = None
    for name in providers():
        if name == "gemini":
            gen = _gemini_stream(system, user, mt)
        elif name == "anthropic":
            gen = _anthropic_stream(system, user, mt)
        else:
            gen = _openai_stream(name, system, user, mt)
        try:
            async for chunk in gen:
                yield chunk
            return
        except _Retryable as r:
            log.warning("%s band — keyingi provayder", name)
            last = r
    if last is not None:
        raise last.error
    raise ProviderError("AI provayder sozlanmagan (API kalit yoʻq).")
