"""A.1 — hodisalar jurnali: endpoint, nom tekshiruvi, payload meʼyori.

Baza yoʻq (conftest) — shuning uchun yozish funksiyasi almashtiriladi va nima
yozilayotgani tekshiriladi. Asosiy shart: hodisa yozilmasa ham soʻrov yiqilmaydi.
"""

import pytest

from app.services import events

pytestmark = pytest.mark.anyio


@pytest.fixture
def written(monkeypatch):
    """`events.record` oʻrniga roʻyxatga yigʻadi (fon vazifasi ishga tushmaydi)."""
    rows: list[tuple] = []

    def _record(name, payload=None, *, user_id=None, guest_id=None, session_id=None):
        rows.append((name, payload, user_id, guest_id, session_id))

    monkeypatch.setattr(events, "record", _record)
    import app.routers.events as router_module

    monkeypatch.setattr(router_module.events_service, "record", _record)
    return rows


async def test_events_endpoint_accepts_a_batch(client, written):
    r = await client.post(
        "/api/events",
        json={
            "session_id": "s-1",
            "events": [
                {"name": "idea_submitted", "payload": {"input": "text", "locale": "uz"}},
                {"name": "prompt_copied", "payload": {"prompt_id": "p-1"}, "guest_id": "g-1"},
            ],
        },
    )
    assert r.status_code == 202
    assert [x[0] for x in written] == ["idea_submitted", "prompt_copied"]
    assert written[0][4] == "s-1"
    assert written[1][3] == "g-1"


async def test_unknown_event_name_is_ignored(monkeypatch):
    """Notanish nom jadvalga tushmaydi (yozuvga ham borilmaydi)."""
    called = False

    async def _write(*a, **k):  # pragma: no cover — chaqirilmasligi kerak
        nonlocal called
        called = True

    monkeypatch.setattr(events, "_write", _write)
    events.record("hacker_event", {"x": 1})
    assert called is False


def test_payload_is_trimmed():
    out = events._trim({"long": "a" * 5000, "n": 3, "obj": {"k": "v"}, "none": None})
    assert len(out["long"]) == 1000
    assert out["n"] == 3
    assert out["obj"] == "{'k': 'v'}"
    assert out["none"] is None


def test_known_names_cover_the_funnel():
    for name in ("idea_submitted", "prompt_generated", "prompt_copied", "prompt_feedback"):
        assert name in events.EVENT_NAMES
