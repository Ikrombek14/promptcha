"""/api/prompts/generate + /jobs/{id} — pipeline soxta, HTTP va job qatlami tekshiriladi."""

import asyncio

import pytest

from app.ai import pipeline
from app.services import jobs


@pytest.fixture(autouse=True)
def _clean_jobs():
    yield
    jobs.reset_for_tests()


async def _fake_run_ok(body, context=None):
    yield "classify", {"kind": "image", "confidence": 0.9, "ask": False}
    yield "delta", {"text": "hello "}
    yield "delta", {"text": "world"}
    yield "explain", {"notes": ["x — y"]}
    yield "done", {"status": "ok", "kind": "image", "prompt": "hello world"}


async def _fake_run_slow(body, context=None):
    yield "delta", {"text": "a"}
    await asyncio.sleep(0.2)
    yield "delta", {"text": "b"}
    await asyncio.sleep(0.2)
    yield "done", {"status": "ok", "kind": "image", "prompt": "ab"}


async def _fake_run_error(body, context=None):
    raise pipeline.PipelineError("AI xizmati band.")
    yield  # pragma: no cover


async def _fake_run_forever(body, context=None):
    yield "delta", {"text": "start"}
    await asyncio.sleep(60)
    yield "done", {"status": "ok", "kind": "image", "prompt": "never"}


async def _start(client, **overrides):
    r = await client.post(
        "/api/prompts/generate",
        json={"text": "restoran uchun logo", "ai": "midjourney", **overrides},
    )
    assert r.status_code == 200
    return r.json()["job_id"]


async def test_generate_returns_job_and_events_stream(client, monkeypatch):
    monkeypatch.setattr(pipeline, "run", _fake_run_ok)
    job_id = await _start(client)
    r = await client.get(f"/api/prompts/jobs/{job_id}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    body = r.text
    assert "event: classify" in body
    assert body.count("event: delta") == 2
    assert "event: done" in body
    assert '"prompt": "hello world"' in body


async def test_reconnect_replays_full_history(client, monkeypatch):
    """Sahifa yangilanganidek: ish tugagach yana ulansa hamma hodisalar qaytariladi."""
    monkeypatch.setattr(pipeline, "run", _fake_run_slow)
    job_id = await _start(client)
    first = await client.get(f"/api/prompts/jobs/{job_id}")
    second = await client.get(f"/api/prompts/jobs/{job_id}")
    assert first.text == second.text
    assert second.text.count("event: delta") == 2
    assert '"prompt": "ab"' in second.text


async def test_error_is_delivered_as_event(client, monkeypatch):
    monkeypatch.setattr(pipeline, "run", _fake_run_error)
    job_id = await _start(client, ai="chatgpt")
    r = await client.get(f"/api/prompts/jobs/{job_id}")
    assert "event: error" in r.text
    assert "AI xizmati band." in r.text


async def test_cancel_stops_job(client, monkeypatch):
    monkeypatch.setattr(pipeline, "run", _fake_run_forever)
    job_id = await _start(client)
    await asyncio.sleep(0.05)
    r = await client.post(f"/api/prompts/jobs/{job_id}/cancel")
    assert r.status_code == 200
    r = await client.get(f"/api/prompts/jobs/{job_id}")
    assert "event: error" in r.text
    assert jobs.CANCELLED_ERROR in r.text


async def test_unknown_job_is_404(client):
    r = await client.get("/api/prompts/jobs/yoq")
    assert r.status_code == 404
    r = await client.post("/api/prompts/jobs/yoq/cancel")
    assert r.status_code == 404


async def test_generate_validates_body(client):
    r = await client.post("/api/prompts/generate", json={"text": "ab", "ai": "midjourney"})
    assert r.status_code == 422
    r = await client.post("/api/prompts/generate", json={"text": "salom dunyo", "ai": "sora"})
    assert r.status_code == 422


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
