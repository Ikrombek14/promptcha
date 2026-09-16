"""Pipeline qadamlari: provayder qatlami (app.ai.llm) soxta funksiyalar bilan almashtiriladi.

Oqim: classify (kesh) → plan (brif + savollar, kesh) → generate (stream) → review (ball + izohlar).
"""

import pytest

from app.ai import llm, pipeline
from app.schemas import (
    Brief,
    ClarifyQuestion,
    Classification,
    GenerateRequest,
    PlanResult,
    ReviewCriterion,
    ReviewResult,
)


class FakeLLM:
    def __init__(self, parsed_by_type: dict, chunks: list[str]):
        self.parsed_by_type = parsed_by_type
        self.chunks = chunks
        self.parse_calls: list[dict] = []
        self.stream_calls: list[dict] = []

    async def parse(self, system, user, schema, max_tokens=600, light=False):
        self.parse_calls.append(
            {"system": system, "user": user, "schema": schema, "max_tokens": max_tokens}
        )
        return self.parsed_by_type[schema].model_copy(deep=True)

    async def stream(self, system, user, max_tokens=None):
        self.stream_calls.append({"system": system, "user": user, "max_tokens": max_tokens})
        for c in self.chunks:
            yield c

    def calls_for(self, schema):
        return [c for c in self.parse_calls if c["schema"] is schema]


@pytest.fixture
def fake(monkeypatch):
    f = FakeLLM(
        parsed_by_type={
            Classification: Classification(
                kind="image",
                confidence=0.95,
                tools=["midjourney", "ideogram"],
                archetype="logo",
                reason="logo",
            ),
            PlanResult: PlanResult(
                brief=Brief(goal="logo", facts={"brand_name": "Navroʻz"}, missing=["style"]),
                questions=[],
            ),
            ReviewResult: ReviewResult(
                score=82,
                criteria=[ReviewCriterion(name="task_clear", ok=True)],
                notes=["a — b", "c — d"],
            ),
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
    explain = next(d for n, d in events if n == "explain")
    assert explain["score"] == 82
    assert explain["notes"] == ["a — b", "c — d"]
    assert explain["criteria"][0]["name"] == "task_clear"
    assert events[-1][0] == "done"
    assert events[-1][1]["status"] == "ok"
    assert events[-1][1]["prompt"].endswith("--v 6.0")


async def test_classify_event_has_archetype(fake):
    body = GenerateRequest(text="restoran uchun logo", answers={"style": "minimal"})
    events = await _collect(body)
    assert events[1][1]["archetype"] == "logo"


async def test_unknown_archetype_falls_back_to_general(fake):
    fake.parsed_by_type[Classification].archetype = "nonexistent"
    c = await pipeline.classify("restoran uchun logo")
    assert c.archetype == "general"


async def test_low_confidence_asks_kind(fake):
    fake.parsed_by_type[Classification] = Classification(
        kind="design", confidence=0.5, tools=["claude"], reason="?"
    )
    body = GenerateRequest(text="logo kerak", ai="midjourney")
    events = await _collect(body)
    assert events[1][0] == "classify"
    assert events[1][1]["ask"] is True
    assert events[1][1]["kind"] == "design"
    assert events[-1][1]["status"] == "needs_kind"
    assert not any(n == "delta" for n, _ in events)
    assert not fake.calls_for(PlanResult)  # savolgacha bormaydi


async def test_auto_ai_is_chosen_by_classify(fake):
    """AI tanlanmagan (None) → classify tavsiya qilgan vosita ishlatiladi, kind berilgan boʻlsa ham."""
    fake.parsed_by_type[Classification] = Classification(
        kind="video", confidence=0.99, tools=["veo", "kling"], archetype="ad", reason="clip"
    )
    body = GenerateRequest(text="restoran uchun reels", kind="video", answers={"mood": "iliq"})
    events = await _collect(body)
    assert events[1][1]["ai"] == "veo"
    assert events[-1][1]["ai"] == "veo"
    assert events[-1][1]["status"] == "ok"
    assert fake.stream_calls[0]["system"].startswith(
        "You are a senior prompt engineer for text-to-video"
    )
    assert "Veo" in fake.calls_for(ReviewResult)[0]["system"]


async def test_plan_questions_stop_the_flow(fake):
    fake.parsed_by_type[PlanResult] = PlanResult(
        brief=Brief(missing=["style"]),
        questions=[ClarifyQuestion(id="style", question="Uslub?", options=["minimal", "klassik"])],
    )
    body = GenerateRequest(text="logo kerak", ai="midjourney", kind="image")
    events = await _collect(body)
    assert events[0] == ("stage", {"stage": "clarify"})
    assert events[1][0] == "clarify"
    assert events[1][1]["questions"][0]["id"] == "style"
    assert events[-1][1]["status"] == "needs_clarification"
    assert not fake.stream_calls


async def test_plan_never_asks_a_fact_the_user_gave(fake):
    fake.parsed_by_type[PlanResult] = PlanResult(
        brief=Brief(facts={"brand_name": "Navroʻz"}, missing=["brand_name", "style"]),
        questions=[
            ClarifyQuestion(id="brand_name", question="Nomi?", options=["a"]),
            ClarifyQuestion(id="style", question="Uslub?", options=["minimal"]),
        ],
    )
    p = await pipeline.plan("Navroʻz uchun logo", "image", "midjourney", "uz", archetype="logo")
    assert [q.id for q in p.questions] == ["style"]
    assert p.brief.missing == ["style"]


async def test_answers_are_merged_into_brief_and_skip_questions(fake):
    fake.parsed_by_type[PlanResult] = PlanResult(
        brief=Brief(facts={"brand_name": "Navroʻz"}, missing=["style"]),
        questions=[ClarifyQuestion(id="style", question="Uslub?", options=["minimal"])],
    )
    body = GenerateRequest(
        text="logo", ai="midjourney", kind="image", answers={"style": "minimal, zamonaviy"}
    )
    events = await _collect(body)
    assert not any(n == "clarify" for n, _ in events)
    assert events[-1][1]["status"] == "ok"
    system = fake.stream_calls[0]["system"]
    assert "<brief>" in system
    assert '"style":"minimal, zamonaviy"' in system  # javob brifga kirdi
    assert '"missing"' not in system  # yetishmayotgan qolmadi


def test_apply_answers_keeps_not_specified_as_missing():
    brief = Brief(missing=["style", "colors"])
    qs = [ClarifyQuestion(id="style", question="?"), ClarifyQuestion(id="colors", question="?")]
    out = pipeline.apply_answers(brief, qs, {"style": "(not specified)", "colors": "koʻk"})
    assert out.facts == {"colors": "koʻk"}
    assert out.missing == ["style"]


async def test_plan_is_cached_per_text_and_tool(fake):
    await pipeline.plan("logo kerak", "image", "midjourney", "uz", archetype="logo")
    await pipeline.plan("Logo  kerak", "image", "midjourney", "uz", archetype="logo")
    assert len(fake.calls_for(PlanResult)) == 1
    await pipeline.plan("logo kerak", "image", "ideogram", "uz", archetype="logo")
    assert len(fake.calls_for(PlanResult)) == 2


async def test_generate_system_has_playbook_rubric_examples_context(fake):
    body = GenerateRequest(text="logo", ai="midjourney", kind="image", answers={"style": "minimal"})
    await _collect(body, context={"industry": "restoran"})
    call = fake.stream_calls[0]
    assert "<rubric>" in call["system"]
    assert "<playbook" in call["system"]
    assert "<examples>" in call["system"]
    assert "industry: restoran" in call["system"]
    assert "<clarifications>" in call["user"]
    assert all(c["max_tokens"] <= 1500 for c in fake.parse_calls)


async def test_plan_system_lists_required_facts_and_locale(fake):
    await pipeline.plan("post kerak", "text", "chatgpt", "ru", archetype="post")
    system = fake.calls_for(PlanResult)[0]["system"]
    assert "<required_facts>" in system
    assert "Russian" in system


async def test_provider_error_propagates(fake, monkeypatch):
    async def boom(*a, **k):
        raise llm.ProviderError("AI xizmati band.")

    monkeypatch.setattr(llm, "parse", boom)
    body = GenerateRequest(text="logo kerak", ai="midjourney")
    with pytest.raises(pipeline.PipelineError, match="band"):
        await _collect(body)


async def test_improve_skips_questions_and_passes_feedback(fake):
    fake.parsed_by_type[PlanResult] = PlanResult(
        brief=Brief(missing=["style"]),
        questions=[ClarifyQuestion(id="style", question="Uslub?", options=["minimal"])],
    )
    body = GenerateRequest(
        text="logo kerak",
        ai="midjourney",
        kind="image",
        improve={"previous_prompt": "/imagine old", "feedback": ["aspect ratio yoʻq"]},
    )
    events = await _collect(body)
    assert not any(n == "clarify" for n, _ in events)
    assert events[-1][1]["status"] == "ok"
    user = fake.stream_calls[0]["user"]
    assert "<previous_prompt>" in user and "/imagine old" in user
    assert "aspect ratio yoʻq" in user
    assert next(d for n, d in events if n == "explain")["score"] == 82


async def test_plan_drops_question_when_an_option_is_already_in_the_text(fake):
    fake.parsed_by_type[PlanResult] = PlanResult(
        brief=Brief(missing=["brand_name", "colors"]),
        questions=[
            ClarifyQuestion(id="brand_name", question="Nomi?", options=["Urfon", "Urfon Center"]),
            ClarifyQuestion(id="colors", question="Rang?", options=["koʻk", "qizil"]),
        ],
    )
    p = await pipeline.plan(
        "Urfon oʻquv markazi uchun logo", "image", "midjourney", "uz", archetype="logo"
    )
    assert [q.id for q in p.questions] == ["colors"]
    assert p.brief.facts["brand_name"] == "Urfon"
    assert p.brief.missing == ["colors"]
