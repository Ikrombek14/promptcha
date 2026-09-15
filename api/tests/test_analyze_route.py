"""/api/prompts/analyze — matn tahlili: tur + 2–3 vosita (classify soxta)."""

from app.ai import pipeline
from app.schemas import Classification


async def test_analyze_returns_kind_and_tools(client, monkeypatch):
    async def fake_classify(text):
        return Classification(
            kind="image",
            confidence=0.93,
            tools=["midjourney", "ideogram", "chatgpt"],
            reason="flyer",
        )

    monkeypatch.setattr(pipeline, "classify", fake_classify)
    r = await client.post(
        "/api/prompts/analyze", json={"text": "urfon uchun flayer", "locale": "uz"}
    )
    assert r.status_code == 200
    assert r.json() == {
        "kind": "image",
        "confidence": 0.93,
        "tools": ["midjourney", "ideogram", "chatgpt"],
    }


async def test_analyze_provider_error_is_503(client, monkeypatch):
    async def boom(text):
        raise pipeline.PipelineError("AI xizmati band.")

    monkeypatch.setattr(pipeline, "classify", boom)
    r = await client.post("/api/prompts/analyze", json={"text": "salom dunyo"})
    assert r.status_code == 503
    assert r.json()["detail"] == "AI xizmati band."


async def test_analyze_validates(client):
    r = await client.post("/api/prompts/analyze", json={"text": "ab"})
    assert r.status_code == 422
