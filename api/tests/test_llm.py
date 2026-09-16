"""Provayder qatlami: model zaxiralari va provayderlar zanjiri (429/5xx → keyingisi)."""

from types import SimpleNamespace

import openai
import pytest
from google.genai import errors as gerrors

from app.ai import llm
from app.config import get_settings
from app.schemas import Classification

# --------------------------------------------------------------------------- soxta klientlar


def _gemini_err(code: int = 429):
    return gerrors.ClientError(code, {"error": {"code": code, "message": "quota, retry in 30s"}})


def _openai_err(status: int):
    import httpx2 as httpx  # openai 3.x httpx2 ustida

    resp = httpx.Response(status, request=httpx.Request("POST", "http://x/v1/chat/completions"))
    if status == 429:
        return openai.RateLimitError("rate", response=resp, body=None)
    if status == 400:
        return openai.BadRequestError("bad", response=resp, body=None)
    if status == 401:
        return openai.AuthenticationError("auth", response=resp, body=None)
    return openai.APIStatusError("err", response=resp, body=None)


class FakeGemini:
    def __init__(self):
        self.failing: dict[str, Exception] = {}
        self.calls: list[str] = []

    async def generate_content(self, *, model, contents, config):
        self.calls.append(model)
        if model in self.failing:
            raise self.failing[model]
        return SimpleNamespace(parsed=Classification(kind="image", confidence=0.9), text=None)

    async def generate_content_stream(self, *, model, contents, config):
        self.calls.append(model)
        if model in self.failing:
            raise self.failing[model]

        async def gen():
            for t in ["a", "b"]:
                yield SimpleNamespace(text=t)

        return gen()


class FakeOpenAI:
    """client.chat.completions.create(...) — content yoki stream."""

    def __init__(self, content='{"kind": "text", "confidence": 0.8, "reason": "x"}'):
        self.content = content
        self.failing: dict[str, Exception] = {}
        self.reject_response_format = False
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kw):
        self.calls.append(kw)
        model = kw["model"]
        if model in self.failing:
            raise self.failing[model]
        if self.reject_response_format and "response_format" in kw:
            raise _openai_err(400)
        if kw.get("stream"):

            async def gen():
                for t in ["x", "y"]:
                    yield SimpleNamespace(
                        choices=[SimpleNamespace(delta=SimpleNamespace(content=t))]
                    )
                yield SimpleNamespace(choices=[])

            return gen()
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


@pytest.fixture
def env(monkeypatch):
    """Sozlamalar va soxta klientlar. env.settings(...) bilan qiymatlar oʻzgartiriladi."""
    g = FakeGemini()
    o = FakeOpenAI()
    monkeypatch.setattr(
        llm, "_gemini_client", lambda: SimpleNamespace(aio=SimpleNamespace(models=g))
    )
    llm._openai_client.cache_clear()
    monkeypatch.setattr(llm, "_openai_client", lambda name: o)

    state = {"s": get_settings()}

    def settings(**upd):
        state["s"] = state["s"].model_copy(update=upd)

    monkeypatch.setattr(llm, "get_settings", lambda: state["s"])
    settings(
        ai_providers="gemini,groq",
        gemini_api_key="g",
        gemini_model="m1",
        gemini_fallback_models="m2, m3",
        groq_api_key="k",
        groq_model="q1",
        groq_fallback_models="q2",
        mistral_api_key="",
        openrouter_api_key="",
    )
    return SimpleNamespace(gemini=g, openai=o, settings=settings)


# --------------------------------------------------------------------------- Gemini zaxira modellar


async def test_gemini_parse_falls_back_on_429(env):
    env.gemini.failing = {"m1": _gemini_err(429)}
    r = await llm.parse("s", "u", Classification, 100)
    assert r.kind == "image"
    assert env.gemini.calls == ["m1", "m2"]


async def test_gemini_stream_falls_back_on_503(env):
    env.gemini.failing = {"m1": _gemini_err(503), "m2": _gemini_err(429)}
    chunks = [c async for c in llm.stream("s", "u")]
    assert chunks == ["a", "b"]
    assert env.gemini.calls == ["m1", "m2", "m3"]


async def test_gemini_non_retryable_error_does_not_fall_back(env):
    env.gemini.failing = {"m1": _gemini_err(400)}
    with pytest.raises(llm.ProviderError, match="400"):
        await llm.parse("s", "u", Classification, 100)
    assert env.gemini.calls == ["m1"]


# --------------------------------------------------------------------------- provayderlar zanjiri


async def test_chain_moves_to_groq_when_gemini_exhausted(env):
    env.gemini.failing = {m: _gemini_err(429) for m in ("m1", "m2", "m3")}
    r = await llm.parse("s", "u", Classification, 100)
    assert r.kind == "text"
    assert env.openai.calls[0]["model"] == "q1"
    assert env.openai.calls[0]["response_format"] == {"type": "json_object"}
    assert "<output_format>" in env.openai.calls[0]["messages"][0]["content"]


async def test_chain_stream_moves_to_groq(env):
    env.gemini.failing = {m: _gemini_err(503) for m in ("m1", "m2", "m3")}
    chunks = [c async for c in llm.stream("s", "u")]
    assert chunks == ["x", "y"]
    assert env.openai.calls[0]["stream"] is True


async def test_all_providers_exhausted_gives_last_uzbek_error(env):
    env.gemini.failing = {m: _gemini_err(429) for m in ("m1", "m2", "m3")}
    env.openai.failing = {"q1": _openai_err(429), "q2": _openai_err(503)}
    with pytest.raises(llm.ProviderError, match="xatolik \\(503\\)|band"):
        await llm.parse("s", "u", Classification, 100)


async def test_providers_without_keys_are_skipped(env):
    env.settings(ai_providers="mistral,openrouter,groq", groq_api_key="k", mistral_api_key="")
    assert llm.providers() == ["groq"]
    env.settings(ai_providers="gemini", gemini_api_key="")
    with pytest.raises(llm.ProviderError, match="sozlanmagan"):
        await llm.parse("s", "u", Classification, 100)


async def test_unknown_provider_is_ignored(env):
    env.settings(ai_providers="foo, groq", groq_api_key="k")
    assert llm.providers() == ["groq"]


# --------------------------------------------------------------------------- OpenAI-mos tafsilotlar


async def test_openai_retries_without_response_format_on_400(env):
    env.settings(ai_providers="groq")
    env.openai.reject_response_format = True
    r = await llm.parse("s", "u", Classification, 100)
    assert r.kind == "text"
    assert "response_format" in env.openai.calls[0]
    assert "response_format" not in env.openai.calls[1]


async def test_openai_parses_fenced_json(env):
    env.settings(ai_providers="groq")
    env.openai.content = 'Here:\n```json\n{"kind": "app", "confidence": 0.7}\n```'
    r = await llm.parse("s", "u", Classification, 100)
    assert r.kind == "app"


async def test_openai_bad_json_is_uzbek_error(env):
    env.settings(ai_providers="groq")
    env.openai.content = "not json at all"
    with pytest.raises(llm.ProviderError, match="oʻqib boʻlmadi"):
        await llm.parse("s", "u", Classification, 100)


async def test_openai_auth_error_is_not_retried(env):
    env.settings(ai_providers="groq,gemini")
    env.openai.failing = {"q1": _openai_err(401)}
    with pytest.raises(llm.ProviderError, match="kalit"):
        await llm.parse("s", "u", Classification, 100)
    assert env.gemini.calls == []


def test_light_provider_order_is_separate(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("AI_PROVIDERS", "anthropic,groq")
    monkeypatch.setenv("AI_PROVIDERS_LIGHT", "groq,anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    get_settings.cache_clear()
    try:
        assert llm.providers() == ["anthropic", "groq"]
        assert llm.providers(light=True) == ["groq", "anthropic"]
        monkeypatch.setenv("AI_PROVIDERS_LIGHT", "")
        get_settings.cache_clear()
        assert llm.providers(light=True) == ["anthropic", "groq"]
    finally:
        get_settings.cache_clear()


def test_anthropic_light_model_and_temperature_rule(monkeypatch):
    from app.ai import client
    from app.config import get_settings

    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    monkeypatch.setenv("ANTHROPIC_LIGHT_MODEL", "claude-haiku-4-5-20251001")
    get_settings.cache_clear()
    try:
        heavy = client.request_kwargs(max_tokens=300)
        light = client.request_kwargs(max_tokens=300, light=True)
        assert (
            heavy["model"] == "claude-sonnet-5" and "extra_body" not in heavy
        )  # 5-oila temperature rad etadi
        assert light["model"] == "claude-haiku-4-5-20251001" and light["extra_body"] == {
            "temperature": 0.4
        }
    finally:
        get_settings.cache_clear()
