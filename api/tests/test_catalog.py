"""Katalog va classify tozalash: turga mos kelmagan vositalar chiqarib tashlanadi."""

import pytest

from app.ai import llm, pipeline
from app.ai.catalog import TOOLS, family_for
from app.schemas import Classification


def test_catalog_shape():
    assert "sora" not in TOOLS
    for t in TOOLS.values():
        assert t.kinds, t.id
        for k in t.kinds:
            assert k in t.family, (t.id, k)
        assert 1 <= t.popularity <= 10
    assert family_for("chatgpt", "image") == "image"
    assert family_for("chatgpt", "text") == "chat"
    assert family_for("heygen", "video") == "avatar"


@pytest.mark.parametrize(
    ("raw", "kind", "expected"),
    [
        (["midjourney", "veo", "ideogram"], "image", ["midjourney", "ideogram"]),  # veo rasm emas
        (["midjourney", "midjourney"], "image", ["midjourney"]),  # takror
        (["cursor"], "video", ["gemini", "veo", "kling"]),  # hech biri mos emas → mashhurlar
    ],
)
async def test_classify_filters_tools_by_kind(monkeypatch, raw, kind, expected):
    async def fake_parse(system, user, schema, max_tokens=600, light=False):
        return Classification(kind=kind, confidence=0.9, tools=raw[:3])

    monkeypatch.setattr(llm, "parse", fake_parse)
    c = await pipeline.classify("x")
    assert c.tools == expected
