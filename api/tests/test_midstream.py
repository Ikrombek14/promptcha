"""Oqim oʻrtasida provayder uzilsa: llm MidStreamError beradi, pipeline `reset` bilan qayta boshlaydi."""

from types import SimpleNamespace

import pytest
from google.genai import errors as gerrors

from app.ai import llm, pipeline
from app.config import get_settings
from app.schemas import Classification, GenerateRequest, PlanResult, ReviewResult


class FlakyGemini:
    """Birinchi stream: "a" beradi, keyin 503. Ikkinchi stream: toʻliq."""

    def __init__(self):
        self.streams = 0

    async def generate_content(self, **kw):
        raise AssertionError("bu testda parse chaqirilmasligi kerak")

    async def generate_content_stream(self, *, model, contents, config):
        self.streams += 1
        first = self.streams == 1

        async def gen():
            yield SimpleNamespace(text="a")
            if first:
                raise gerrors.ServerError(503, {"error": {"code": 503, "message": "high demand"}})
            yield SimpleNamespace(text="b")

        return gen()


@pytest.fixture
def flaky(monkeypatch):
    g = FlakyGemini()
    monkeypatch.setattr(
        llm, "_gemini_client", lambda: SimpleNamespace(aio=SimpleNamespace(models=g))
    )
    s = get_settings().model_copy(
        update={
            "ai_providers": "gemini",
            "gemini_api_key": "g",
            "gemini_model": "m1",
            "gemini_fallback_models": "",
        }
    )
    monkeypatch.setattr(llm, "get_settings", lambda: s)
    return g


async def test_stream_raises_midstream_error_after_first_chunk(flaky):
    chunks = []
    with pytest.raises(llm.MidStreamError):
        async for c in llm.stream("s", "u"):
            chunks.append(c)
    assert chunks == ["a"]


async def test_pipeline_resets_and_retries_generate(flaky, monkeypatch):
    async def fake_parse(system, user, schema, max_tokens=600, light=False):
        if schema is Classification:  # arxetip uchun har doim (keshdan) chaqiriladi
            return Classification(kind="image", confidence=0.9, tools=["midjourney"])
        if schema is PlanResult:
            return PlanResult()
        if schema is ReviewResult:
            return ReviewResult(score=80, notes=["x — y"])
        raise AssertionError(schema)

    monkeypatch.setattr(llm, "parse", fake_parse)
    body = GenerateRequest(text="logo", ai="midjourney", kind="image", answers={"style": "min"})
    events = [(n, d) async for n, d in pipeline.run(body)]
    names = [n for n, _ in events if n != "stage"]
    assert names == ["delta", "reset", "delta", "delta", "explain", "done"]
    assert events[-1][1]["prompt"] == "ab"
    assert flaky.streams == 2
