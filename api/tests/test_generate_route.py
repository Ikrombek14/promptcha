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


async def _fake_run_metered(body, context=None):
    """Pipeline oʻrnida: llm chaqiruvlarini meter'ga yozadi (job ichidagi contextvar tekshiriladi)."""
    from app.ai import metering

    metering.set_stage("generate")
    metering.record("groq", "q1", input_tokens=100, output_tokens=40)
    yield "delta", {"text": "hello"}
    metering.set_stage("explain")
    metering.record("groq", "q1", input_tokens=50, output_tokens=10)
    yield "explain", {"notes": ["a — b"]}
    yield "done", {"status": "ok", "kind": "image", "ai": "midjourney", "prompt": "hello"}


async def _drain(client, job_id):
    r = await client.get(f"/api/prompts/jobs/{job_id}")
    assert "event: done" in r.text
    # `done` dan keyingi finally (record_llm_calls) tugashini kutamiz
    await asyncio.wait_for(jobs.get(job_id).task, timeout=2)


async def test_guest_job_records_usage_with_token_sums(client, monkeypatch):
    monkeypatch.setattr(pipeline, "run", _fake_run_metered)
    calls = {}

    async def record_usage(**kw):
        calls["usage"] = kw

    async def record_llm_calls(meter, job):
        calls["llm"] = (list(meter.calls), job)

    async def never(*a, **k):
        raise AssertionError("guest uchun chaqirilmasligi kerak")

    monkeypatch.setattr(jobs.usage, "record_usage", record_usage)
    monkeypatch.setattr(jobs.usage, "record_llm_calls", record_llm_calls)
    monkeypatch.setattr(jobs.usage, "save_prompt", never)
    monkeypatch.setattr(jobs.usage, "consume_bonus_if_needed", never)

    job_id = await _start(client, guest_id="g1")
    assert jobs.get(job_id).user_id is None
    await _drain(client, job_id)

    assert calls["usage"] == {
        "user_id": None,
        "guest_id": "g1",
        "ip": "127.0.0.1",
        "ai": "midjourney",
        "input_tokens": 150,
        "output_tokens": 50,
    }
    meter_calls, job = calls["llm"]
    assert job.id == job_id
    assert [(c.stage, c.input_tokens) for c in meter_calls] == [("generate", 100), ("explain", 50)]


async def test_user_job_has_user_id_and_saves_prompt(client, as_user, monkeypatch):
    monkeypatch.setattr(pipeline, "run", _fake_run_metered)
    calls = {}

    async def record_usage(**kw):
        calls["usage"] = kw

    async def consume(user_id):
        calls["bonus"] = user_id

    async def save_prompt(user_id, body, done, notes):
        calls["prompt"] = (user_id, body.text, done["prompt"], notes)

    monkeypatch.setattr(jobs.usage, "record_usage", record_usage)
    monkeypatch.setattr(jobs.usage, "consume_bonus_if_needed", consume)
    monkeypatch.setattr(jobs.usage, "save_prompt", save_prompt)

    job_id = await _start(client)
    assert jobs.get(job_id).user_id == as_user.id
    await _drain(client, job_id)

    assert calls["usage"]["user_id"] == as_user.id
    assert calls["usage"]["input_tokens"] == 150
    assert calls["bonus"] == as_user.id
    assert calls["prompt"] == (as_user.id, "restoran uchun logo", "hello", ["a — b"])


async def test_failed_job_still_records_llm_calls(client, monkeypatch):
    async def run_fail(body, context=None):
        from app.ai import metering

        metering.record("groq", "q1", input_tokens=None, output_tokens=None, ok=False)
        raise pipeline.PipelineError("AI xizmati band.")
        yield  # pragma: no cover

    monkeypatch.setattr(pipeline, "run", run_fail)
    seen = []

    async def record_llm_calls(meter, job):
        seen.extend(meter.calls)

    monkeypatch.setattr(jobs.usage, "record_llm_calls", record_llm_calls)
    job_id = await _start(client)
    r = await client.get(f"/api/prompts/jobs/{job_id}")
    assert "event: error" in r.text
    await asyncio.wait_for(jobs.get(job_id).task, timeout=2)
    assert len(seen) == 1 and seen[0].ok is False and seen[0].estimated


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
