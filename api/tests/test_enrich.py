"""`POST /api/prompts/enrich` — qisqa gʻoyani 2–4 jumlaga kengaytirish (LLM soxta)."""

import pytest

from app.ai import llm, pipeline
from app.schemas import EnrichResult


class FakeLLM:
    def __init__(self, text: str):
        self.text = text
        self.calls: list[dict] = []

    async def parse(self, system, user, schema, max_tokens=600, tier="quality"):
        self.calls.append(
            {"system": system, "user": user, "schema": schema, "tier": tier, "max": max_tokens}
        )
        return EnrichResult(text=self.text)


@pytest.fixture
def fake(monkeypatch):
    def _make(text="Maqsadim restoran uchun logo."):
        f = FakeLLM(text)
        monkeypatch.setattr(llm, "parse", f.parse)
        return f

    return _make


async def test_enrich_returns_expanded_text(fake):
    f = fake("Restoran uchun zamonaviy logo kerak. Mijozlar yosh shahar aholisi.")
    out = await pipeline.enrich("restoran logosi", "uz")
    assert out.startswith("Restoran uchun")
    assert f.calls[0]["user"] == "restoran logosi"
    assert f.calls[0]["schema"] is EnrichResult
    assert f.calls[0]["tier"] == "fast"
    assert f.calls[0]["max"] <= 1500


async def test_enrich_applies_uz_apostrophe(fake):
    fake("bo'lsin va go'zal")
    assert await pipeline.enrich("logo", "uz") == "boʻlsin va goʻzal"


async def test_enrich_system_prompt_has_locale_and_rules(fake):
    f = fake()
    await pipeline.enrich("logo", "ru")
    system = f.calls[0]["system"]
    assert "Russian" in system
    assert "NEVER INVENT FACTS" in system
    assert "Do not ask questions" in system


async def test_enrich_strips_whitespace(fake):
    fake("  matn  ")
    assert await pipeline.enrich("logo", "en") == "matn"


# --------------------------------------------------------------------------- HTTP


async def test_route_returns_text(client, monkeypatch):
    async def enrich(text, locale):
        assert (text, locale) == ("restoran logosi", "uz")
        return "Kengaytirilgan goʻyoki matn"

    monkeypatch.setattr(pipeline, "enrich", enrich)
    r = await client.post("/api/prompts/enrich", json={"text": "restoran logosi"})
    assert r.status_code == 200
    assert r.json() == {"text": "Kengaytirilgan goʻyoki matn"}


async def test_route_passes_locale(client, monkeypatch):
    seen = {}

    async def enrich(text, locale):
        seen["locale"] = locale
        return "x"

    monkeypatch.setattr(pipeline, "enrich", enrich)
    r = await client.post("/api/prompts/enrich", json={"text": "logo kerak", "locale": "ru"})
    assert r.status_code == 200
    assert seen["locale"] == "ru"


async def test_route_provider_error_is_503(client, monkeypatch):
    async def boom(text, locale):
        raise pipeline.PipelineError("AI xizmati band.")

    monkeypatch.setattr(pipeline, "enrich", boom)
    r = await client.post("/api/prompts/enrich", json={"text": "logo kerak"})
    assert r.status_code == 503
    assert r.json()["detail"] == "AI xizmati band."


@pytest.mark.parametrize("body", [{"text": ""}, {"text": "ab"}, {"text": "x" * 2001}, {}])
async def test_route_validates(client, body):
    r = await client.post("/api/prompts/enrich", json=body)
    assert r.status_code == 422


async def test_route_is_open_for_guests(client, monkeypatch):
    async def enrich(text, locale):
        return "ok"

    monkeypatch.setattr(pipeline, "enrich", enrich)
    r = await client.post("/api/prompts/enrich", json={"text": "logo kerak"})
    assert r.status_code == 200
