"""Token hisobi: Meter yigʻish, provayder qatlamining record qilishi, meter yoʻqda jimlik."""

from types import SimpleNamespace

import openai
import pytest

from app.ai import llm, metering
from app.config import get_settings
from app.schemas import Classification

# --------------------------------------------------------------------------- Meter


def test_new_set_stage_record_sums():
    m = metering.new()
    metering.set_stage("classify")
    metering.record("groq", "m", input_tokens=100, output_tokens=20, duration_ms=50)
    metering.set_stage("generate")
    metering.record("groq", "m", input_tokens=300, output_tokens=200, duration_ms=900)
    assert [c.stage for c in m.calls] == ["classify", "generate"]
    assert m.input_tokens == 400
    assert m.output_tokens == 220
    assert all(not c.estimated and c.ok for c in m.calls)
    assert metering.current() is m


def test_record_estimates_when_tokens_missing():
    m = metering.new()
    c = metering.record(
        "gemini",
        "g",
        input_tokens=None,
        output_tokens=None,
        input_text="a" * 40,
        output_text="b" * 8,
    )
    assert c is not None and c.estimated
    assert c.input_tokens == 10
    assert c.output_tokens == 2
    assert m.input_tokens == 10


def test_record_partial_tokens_is_estimated():
    metering.new()
    c = metering.record("groq", "m", input_tokens=50, output_tokens=None, output_text="x" * 16)
    assert c.estimated and c.input_tokens == 50 and c.output_tokens == 4


def test_record_without_meter_is_silent():
    metering.clear()
    assert metering.current() is None
    assert metering.record("groq", "m", input_tokens=1, output_tokens=1) is None
    metering.set_stage("generate")  # xato bermaydi


def test_estimate_tokens():
    assert metering.estimate_tokens("") == 0
    assert metering.estimate_tokens("ab") == 1
    assert metering.estimate_tokens("a" * 400) == 100


# --------------------------------------------------------------------------- OpenAI-mos oqim


def _openai_err(status: int):
    import httpx2 as httpx

    resp = httpx.Response(status, request=httpx.Request("POST", "http://x/v1/chat/completions"))
    if status == 400:
        return openai.BadRequestError("bad", response=resp, body=None)
    if status == 429:
        return openai.RateLimitError("rate", response=resp, body=None)
    return openai.APIStatusError("err", response=resp, body=None)


def _delta(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


class FakeStreamClient:
    """Oxirgi boʻlakda usage keladi (stream_options include_usage). reject_stream_options → 400."""

    def __init__(self, *, usage=True, reject_stream_options=False, fail_model=None):
        self.usage = usage
        self.reject_stream_options = reject_stream_options
        self.fail_model = fail_model
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kw):
        self.calls.append(kw)
        if kw["model"] == self.fail_model:
            raise _openai_err(429)
        if self.reject_stream_options and "stream_options" in kw:
            raise _openai_err(400)
        if kw.get("stream"):

            async def gen():
                yield _delta("hello ")
                yield _delta("world")
                if self.usage:
                    yield SimpleNamespace(
                        choices=[],
                        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=7),
                    )

            return gen()
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))],
            usage=SimpleNamespace(prompt_tokens=33, completion_tokens=11) if self.usage else None,
        )

    content = '{"kind": "image", "confidence": 0.9}'


@pytest.fixture
def groq(monkeypatch):
    llm._openai_client.cache_clear()
    s = get_settings().model_copy(
        update={
            "ai_providers": "groq",
            "groq_api_key": "k",
            "groq_model": "q1",
            "groq_fallback_models": "q2",
        }
    )
    monkeypatch.setattr(llm, "get_settings", lambda: s)

    def use(client):
        monkeypatch.setattr(llm, "_openai_client", lambda name: client)
        return client

    return use


async def test_openai_stream_records_usage_from_last_chunk(groq):
    fake = groq(FakeStreamClient())
    m = metering.new()
    metering.set_stage("generate")
    chunks = [c async for c in llm.stream("sys", "usr")]
    assert chunks == ["hello ", "world"]
    assert fake.calls[0]["stream_options"] == {"include_usage": True}
    assert fake.calls[0]["reasoning_effort"] == "low"
    assert len(m.calls) == 1
    c = m.calls[0]
    assert (c.provider, c.model, c.stage) == ("groq", "q1", "generate")
    assert (c.input_tokens, c.output_tokens, c.estimated, c.ok) == (120, 7, False, True)
    assert c.duration_ms >= 0


async def test_openai_stream_estimates_when_no_usage(groq):
    groq(FakeStreamClient(usage=False))
    m = metering.new()
    chunks = [c async for c in llm.stream("sys", "usr")]
    assert "".join(chunks) == "hello world"
    c = m.calls[0]
    assert c.estimated
    assert c.output_tokens == metering.estimate_tokens("hello world")
    assert c.input_tokens == metering.estimate_tokens("sysusr")


async def test_openai_stream_retries_without_extras_on_400(groq):
    fake = groq(FakeStreamClient(reject_stream_options=True))
    m = metering.new()
    chunks = [c async for c in llm.stream("sys", "usr")]
    assert chunks == ["hello ", "world"]
    assert "stream_options" in fake.calls[0]
    assert "stream_options" not in fake.calls[1]
    assert "reasoning_effort" not in fake.calls[1]
    assert len(m.calls) == 1 and m.calls[0].ok


async def test_openai_stream_failed_model_recorded_as_not_ok(groq):
    groq(FakeStreamClient(fail_model="q1"))
    m = metering.new()
    chunks = [c async for c in llm.stream("sys", "usr")]
    assert chunks == ["hello ", "world"]
    assert [(c.model, c.ok) for c in m.calls] == [("q1", False), ("q2", True)]
    assert m.calls[0].estimated and m.calls[0].output_tokens == 0


async def test_openai_parse_records_usage(groq):
    groq(FakeStreamClient())
    m = metering.new()
    metering.set_stage("classify")
    r = await llm.parse("sys", "usr", Classification, 100)
    assert r.kind == "image"
    c = m.calls[0]
    assert (c.stage, c.input_tokens, c.output_tokens, c.estimated) == ("classify", 33, 11, False)


async def test_stream_without_meter_still_works(groq):
    metering.clear()
    groq(FakeStreamClient())
    chunks = [c async for c in llm.stream("sys", "usr")]
    assert chunks == ["hello ", "world"]


# --------------------------------------------------------------------------- Gemini


async def test_gemini_parse_records_usage_metadata(monkeypatch):
    class G:
        async def generate_content(self, *, model, contents, config):
            return SimpleNamespace(
                parsed=Classification(kind="image", confidence=0.9),
                text='{"kind":"image","confidence":0.9}',
                usage_metadata=SimpleNamespace(
                    prompt_token_count=200, candidates_token_count=30, thoughts_token_count=12
                ),
            )

    monkeypatch.setattr(
        llm, "_gemini_client", lambda: SimpleNamespace(aio=SimpleNamespace(models=G()))
    )
    s = get_settings().model_copy(
        update={
            "ai_providers": "gemini",
            "gemini_api_key": "g",
            "gemini_model": "gm",
            "gemini_fallback_models": "",
        }
    )
    monkeypatch.setattr(llm, "get_settings", lambda: s)
    m = metering.new()
    await llm.parse("s", "u", Classification, 100)
    c = m.calls[0]
    assert (c.provider, c.model, c.input_tokens, c.output_tokens, c.estimated) == (
        "gemini",
        "gm",
        200,
        42,
        False,
    )
