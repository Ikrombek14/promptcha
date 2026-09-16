"""/api/prompts/translate — Tahrirchi Tilmoch (tarmoq soxta)."""

import httpx
import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.services import translate as tr


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.setenv("TAHRIRCHI_API_KEY", "th_test")
    get_settings.cache_clear()
    tr.reset_cache_for_tests()
    yield
    tr.reset_cache_for_tests()
    get_settings.cache_clear()


class FakeResponse:
    def __init__(self, status=200, data=None, text=""):
        self.status_code = status
        self._data = data or {}
        self.text = text

    def json(self):
        return self._data


def fake_post(calls, response):
    async def _post(self, url, headers=None, json=None, **kw):
        calls.append({"url": url, "headers": headers, "json": json})
        if isinstance(response, Exception):
            raise response
        return response

    return _post


async def test_translate_calls_tilmoch_and_caches(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        fake_post(calls, FakeResponse(data={"translated_text": "Salom dunyo"})),
    )
    out = await tr.translate("Hello world", "uz")
    assert out == "Salom dunyo"
    assert calls[0]["json"]["source_lang"] == "eng_Latn"
    assert calls[0]["json"]["target_lang"] == "uzn_Latn"
    assert calls[0]["json"]["model"] == "tilmoch"
    assert calls[0]["headers"]["Authorization"] == "th_test"
    # ikkinchi marta — keshdan, tarmoqqa chiqmaydi
    assert await tr.translate("Hello world", "uz") == "Salom dunyo"
    assert len(calls) == 1


async def test_russian_target_code(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        fake_post(calls, FakeResponse(data={"translated_text": "Привет"})),
    )
    assert await tr.translate("Hello", "ru") == "Привет"
    assert calls[0]["json"]["target_lang"] == "rus_Cyrl"


async def test_same_language_returns_input(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post(calls, FakeResponse()))
    assert await tr.translate("Hello", "en") == "Hello"
    assert not calls


async def test_service_error_is_503(monkeypatch):
    monkeypatch.setattr(
        httpx.AsyncClient, "post", fake_post([], FakeResponse(status=500, text="boom"))
    )
    with pytest.raises(HTTPException) as e:
        await tr.translate("Hello", "uz")
    assert e.value.status_code == 503
    assert e.value.detail == tr.FAILED


async def test_network_error_is_503(monkeypatch):
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post([], httpx.ConnectError("no network")))
    with pytest.raises(HTTPException) as e:
        await tr.translate("Hello", "uz")
    assert e.value.status_code == 503


async def test_not_configured_is_503(monkeypatch):
    monkeypatch.setenv("TAHRIRCHI_API_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(HTTPException) as e:
        await tr.translate("Hello", "uz")
    assert e.value.detail == tr.NOT_CONFIGURED


async def test_too_long_is_422():
    with pytest.raises(HTTPException) as e:
        await tr.translate("x" * 5001, "uz")
    assert e.value.status_code == 422


async def test_route_applies_uz_apostrophe(client, monkeypatch):
    async def fake(text, locale, source_locale="en"):
        return "bo'lsin va go'zal"

    monkeypatch.setattr(tr, "translate", fake)
    r = await client.post("/api/prompts/translate", json={"text": "let it be", "locale": "uz"})
    assert r.status_code == 200
    assert r.json()["text"] == "boʻlsin va goʻzal"


async def test_route_validates(client):
    r = await client.post("/api/prompts/translate", json={"text": ""})
    assert r.status_code == 422
