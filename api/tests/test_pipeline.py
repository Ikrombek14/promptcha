"""Pipeline qadamlari: provayder qatlami (app.ai.llm) soxta funksiyalar bilan almashtiriladi."""

import pytest

from app.ai import client as ai_client
from app.ai import llm, pipeline
from app.schemas import (
    ClarifyQuestion,
    ClarifyResult,
    Classification,
    ExplainResult,
    GenerateRequest,
)


class FakeLLM:
    def __init__(self, parsed_by_type: dict, chunks: list[str]):
        self.parsed_by_type = parsed_by_type
        self.chunks = chunks
        self.parse_calls: list[dict] = []
        self.stream_calls: list[dict] = []

    async def parse(self, system, user, schema, max_tokens=600):
        self.parse_calls.append(
            {"system": system, "user": user, "schema": schema, "max_tokens": max_tokens}
        )
        return self.parsed_by_type[schema]

    async def stream(self, system, user, max_tokens=None):
        self.stream_calls.append({"system": system, "user": user, "max_tokens": max_tokens})
        for c in self.chunks:
            yield c


@pytest.fixture
def fake(monkeypatch):
    f = FakeLLM(
        parsed_by_type={
            Classification: Classification(
                kind="image", confidence=0.95, tools=["midjourney", "ideogram"], reason="logo"
            ),
            ClarifyResult: ClarifyResult(questions=[]),
            ExplainResult: ExplainResult(notes=["a — b", "c — d"]),
        },
        chunks=["/imagine prompt: ", "minimal logo ", "--ar 1:1 --v 6.0"],
    )
    monkeypatch.setattr(llm, "parse", f.parse)
    monkeypatch.setattr(llm, "stream", f.stream)
    return f


async def _collect(body, context=None):
    return [(n, d) async for n, d in pipeline.run(body, context)]


async def test_full_flow_ok(fake):
    body = GenerateRequest(
        text="restoran uchun logo", ai="midjourney", answers={"style": "minimal"}
    )
    events = await _collect(body)
    names = [n for n, _ in events]
    assert names[:2] == ["stage", "classify"]
    assert [d["stage"] for n, d in events if n == "stage"] == ["classify", "generate", "explain"]
    assert names.count("delta") == 3
    assert "explain" in names
    assert events[-1][0] == "done"
    assert events[-1][1]["status"] == "ok"
    assert events[-1][1]["prompt"].endswith("--v 6.0")


async def test_low_confidence_asks_kind(fake):
    fake.parsed_by_type[Classification] = Classification(
        kind="design", confidence=0.5, tools=["claude"], reason="?"
    )
    body = GenerateRequest(text="logo kerak", ai="midjourney")
    events = await _collect(body)
    assert events[1] == (
        "classify",
        {"kind": "design", "confidence": 0.5, "ask": True, "ai": "midjourney", "tools": ["claude"]},
    )
    assert events[-1][1]["status"] == "needs_kind"
    assert not any(n == "delta" for n, _ in events)


async def test_auto_ai_is_chosen_by_classify(fake):
    """AI tanlanmagan (None) → classify tavsiya qilgan vosita ishlatiladi, kind berilgan boʻlsa ham."""
    fake.parsed_by_type[Classification] = Classification(
        kind="video", confidence=0.99, tools=["veo", "kling"], reason="clip"
    )
    body = GenerateRequest(text="restoran uchun reels", kind="video", answers={"mood": "iliq"})
    events = await _collect(body)
    assert events[1][1]["ai"] == "veo"
    assert events[-1][1]["ai"] == "veo"
    assert events[-1][1]["status"] == "ok"
    assert fake.stream_calls[0]["system"].startswith(
        "You are a senior prompt engineer for text-to-video"
    )
    assert "Veo" in fake.parse_calls[-1]["system"]  # explain ham shu vosita bilan


async def test_clarify_stops_when_questions(fake):
    fake.parsed_by_type[ClarifyResult] = ClarifyResult(
        questions=[ClarifyQuestion(id="style", question="Uslub?", options=["minimal", "klassik"])]
    )
    body = GenerateRequest(text="logo kerak", ai="midjourney", kind="image")
    events = await _collect(body)
    assert events[0] == ("stage", {"stage": "clarify"})
    assert events[1][0] == "clarify"
    assert events[1][1]["questions"][0]["id"] == "style"
    assert events[-1][1]["status"] == "needs_clarification"


async def test_answers_skip_clarify(fake):
    fake.parsed_by_type[ClarifyResult] = ClarifyResult(
        questions=[ClarifyQuestion(id="style", question="Uslub?", options=["minimal"])]
    )
    body = GenerateRequest(text="logo", ai="midjourney", kind="image", answers={"style": "minimal"})
    events = await _collect(body)
    assert not any(n == "clarify" for n, _ in events)
    assert events[-1][1]["status"] == "ok"


async def test_generate_system_contains_examples_and_context(fake):
    body = GenerateRequest(text="logo", ai="midjourney", kind="image", answers={"style": "minimal"})
    await _collect(body, context={"industry": "restoran"})
    call = fake.stream_calls[0]
    assert "<examples>" in call["system"]
    assert "industry: restoran" in call["system"]
    assert "<clarifications>" in call["user"]
    assert all(c["max_tokens"] <= 1500 for c in fake.parse_calls)


async def test_provider_error_propagates(fake, monkeypatch):
    async def boom(*a, **k):
        raise llm.ProviderError("AI xizmati band.")

    monkeypatch.setattr(llm, "parse", boom)
    body = GenerateRequest(text="logo kerak", ai="midjourney")
    with pytest.raises(pipeline.PipelineError, match="band"):
        await _collect(body)


def test_anthropic_request_kwargs_limits():
    kw = ai_client.request_kwargs(max_tokens=99999)
    assert kw["max_tokens"] <= 1500
    assert kw["model"]
    if "4-6" in kw["model"]:
        assert kw["extra_body"] == {"temperature": 0.4}
