"""Review bergan rangli boʻlaklar (`segments`) va «anatomiya» kartalari (`parts`).

Asosiy qoida: `segments[].text` birlashtirilganda asl prompt harfma-harf chiqishi shart.
Model oradagi tinish/boʻshliqni tashlab ketsa — server qavsharlaydi (`plain` boʻlak qoʻshadi);
boʻlak promptda umuman boʻlmasa — `segments=[]` (frontend oddiy matn koʻrsatadi).
"""

import pytest

from app.ai import llm, pipeline
from app.ai.prompts import SEGMENT_TYPES, segment_types
from app.schemas import (
    Brief,
    Classification,
    GenerateRequest,
    PlanResult,
    PromptPart,
    ReviewCriterion,
    ReviewResult,
    Segment,
)

PROMPT = "/imagine prompt: minimal logo --ar 1:1 --v 6.0"
CHUNKS = ["/imagine prompt: ", "minimal logo ", "--ar 1:1 --v 6.0"]


class FakeLLM:
    def __init__(self, review: ReviewResult):
        self.review = review
        self.systems: dict = {}

    async def parse(self, system, user, schema, max_tokens=600, tier="quality"):
        self.systems[schema] = system
        if schema is Classification:
            return Classification(
                kind="image", confidence=0.95, tools=["midjourney"], archetype="logo"
            )
        if schema is PlanResult:
            return PlanResult(brief=Brief(goal="logo"), questions=[])
        return self.review.model_copy(deep=True)

    async def stream(self, system, user, max_tokens=None, *, quality=False):
        for c in CHUNKS:
            yield c


def _review(segments=(), parts=(), notes=("a — b",)) -> ReviewResult:
    return ReviewResult(
        score=80,
        criteria=[ReviewCriterion(name="task_clear", ok=True)],
        notes=list(notes),
        segments=list(segments),
        parts=list(parts),
    )


@pytest.fixture
def run_with(monkeypatch):
    """Berilgan ReviewResult bilan toʻliq oqimni yuritadi va `explain` hodisasini qaytaradi."""

    async def _run(review: ReviewResult, kind: str = "image", locale: str = "uz"):
        fake = FakeLLM(review)
        monkeypatch.setattr(llm, "parse", fake.parse)
        monkeypatch.setattr(llm, "stream", fake.stream)
        body = GenerateRequest(
            text="logo kerak", ai="midjourney", kind=kind, locale=locale, answers={"style": "a"}
        )
        events = [(n, d) async for n, d in pipeline.run(body)]
        explain = next(d for n, d in events if n == "explain")
        return explain, fake

    return _run


# --------------------------------------------------------------------------- segments


async def test_segments_are_stitched_back_to_the_exact_prompt(run_with):
    explain, _ = await run_with(
        _review(
            segments=[
                Segment(type="object", text="minimal logo"),
                Segment(type="params", text="--ar 1:1 --v 6.0"),
            ]
        )
    )
    segments = explain["segments"]
    assert "".join(s["text"] for s in segments) == PROMPT
    assert [s["type"] for s in segments] == ["plain", "object", "plain", "params"]
    assert segments[0]["text"] == "/imagine prompt: "


async def test_unknown_segment_type_falls_back_to_plain(run_with):
    explain, _ = await run_with(
        _review(
            segments=[
                Segment(type="object", text="minimal"),
                Segment(type="vibe", text="logo"),  # bunday toifa yoʻq
            ]
        )
    )
    types = [s["type"] for s in explain["segments"]]
    assert "object" in types
    assert "vibe" not in types
    assert "".join(s["text"] for s in explain["segments"]) == PROMPT


async def test_segments_dropped_when_text_is_not_in_the_prompt(run_with, caplog):
    with caplog.at_level("INFO", logger="app.ai.pipeline"):
        explain, _ = await run_with(
            _review(segments=[Segment(type="object", text="a cat on the moon")])
        )
    assert explain["segments"] == []
    assert "segments tashlandi" in caplog.text


async def test_out_of_order_segment_is_skipped_but_the_rest_stay(run_with):
    """Tartibdan chiqqan boʻlak tashlanadi, qolganlari rangli boʻlib qoladi."""
    explain, _ = await run_with(
        _review(
            segments=[
                Segment(type="params", text="--ar 1:1 --v 6.0"),
                Segment(type="object", text="minimal logo"),
            ]
        )
    )
    types = [s["type"] for s in explain["segments"]]
    assert "params" in types
    assert "object" not in types
    assert "".join(s["text"] for s in explain["segments"]) == PROMPT


async def test_segment_matches_despite_different_whitespace(run_with):
    """Model qator uzilishini boshqacha koʻchirsa ham boʻlak topiladi."""
    spaced = PROMPT.split()[0] + "   " + PROMPT.split()[1]
    explain, _ = await run_with(_review(segments=[Segment(type="object", text=spaced)]))
    assert [s["type"] for s in explain["segments"]][0] == "object"
    assert "".join(s["text"] for s in explain["segments"]) == PROMPT


async def test_no_segments_when_model_returns_none(run_with):
    explain, _ = await run_with(_review())
    assert explain["segments"] == []
    assert explain["parts"] == []


async def test_all_plain_segments_are_dropped(run_with):
    explain, _ = await run_with(_review(segments=[Segment(type="plain", text="minimal logo")]))
    assert explain["segments"] == []


# --------------------------------------------------------------------------- parts


async def test_parts_are_cut_to_four_and_excerpt_is_shortened(run_with):
    long = "x" * 120
    explain, _ = await run_with(
        _review(
            parts=[
                PromptPart(type="object", excerpt=long, why="Qahramon boshida turadi"),
                PromptPart(type="composition", excerpt="wide angle", why="Kenglik hissi"),
                PromptPart(type="light", excerpt="soft light", why="Kayfiyat"),
                PromptPart(type="params", excerpt="--ar 1:1", why="Nisbat"),
                PromptPart(type="object", excerpt="beshinchi", why="Ortiqcha"),
            ]
        )
    )
    parts = explain["parts"]
    assert len(parts) == 4
    assert len(parts[0]["excerpt"]) == 60
    assert parts[0]["excerpt"].endswith("…")
    assert [p["type"] for p in parts] == ["object", "composition", "light", "params"]


async def test_part_without_why_or_excerpt_is_dropped(run_with):
    explain, _ = await run_with(
        _review(
            parts=[
                PromptPart(type="object", excerpt="minimal logo", why=""),
                PromptPart(type="params", excerpt="", why="Nisbat"),
                PromptPart(type="light", excerpt="soft", why="Kayfiyat"),
            ]
        )
    )
    assert [p["type"] for p in explain["parts"]] == ["light"]


async def test_unknown_part_type_falls_back_to_plain(run_with):
    explain, _ = await run_with(
        _review(parts=[PromptPart(type="mood", excerpt="minimal", why="Sodda")])
    )
    assert explain["parts"][0]["type"] == "plain"


async def test_part_why_gets_uz_apostrophe(run_with):
    explain, _ = await run_with(
        _review(parts=[PromptPart(type="object", excerpt="minimal", why="o'zgarmas go'zallik")])
    )
    assert explain["parts"][0]["why"] == "oʻzgarmas goʻzallik"


# --------------------------------------------------------------------------- toifalar roʻyxati


async def test_review_system_lists_types_for_the_kind(run_with):
    _, fake = await run_with(_review(), kind="app")
    system = fake.systems[ReviewResult]
    assert "<segment_types>" in system
    for t in ("goal", "stack", "features", "acceptance"):
        assert t in system
    assert "composition" not in system


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("image", ("object", "composition", "light", "params", "plain")),
        ("video", ("object", "composition", "light", "params", "plain")),
        ("text", ("role", "task", "requirements", "format", "plain")),
        ("design", ("role", "task", "requirements", "format", "plain")),
        ("app", ("goal", "stack", "features", "acceptance", "plain")),
    ],
)
def test_segment_types_per_kind(kind, expected):
    assert segment_types(kind) == expected


def test_every_kind_has_segment_types():
    from app.schemas import KINDS

    assert set(SEGMENT_TYPES) == set(KINDS)
    for types in SEGMENT_TYPES.values():
        assert types[-1] == "plain"
