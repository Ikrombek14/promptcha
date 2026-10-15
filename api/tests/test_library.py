"""Tarix va kutubxona: `services/library.py` (soxta sessiya) va `/api/prompts/*` yoʻllari."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.db import get_session
from app.main import app
from app.models import Prompt
from app.services import library

PID = uuid.UUID("22222222-2222-2222-2222-222222222222")
UID = uuid.UUID("33333333-3333-3333-3333-333333333333")


def _row(
    pid: uuid.UUID = PID,
    user_id: uuid.UUID = UID,
    *,
    is_saved: bool = False,
    score: int | None = 82,
    result: str = "/imagine minimal logo",
) -> Prompt:
    return Prompt(
        id=pid,
        user_id=user_id,
        input_text="restoran uchun logo",
        kind="image",
        ai="midjourney",
        clarifications={"style": "minimal"},
        result=result,
        explanations=["a — b"],
        score=score,
        locale="uz",
        output_language="en",
        is_public=False,
        is_saved=is_saved,
        created_at=datetime(2026, 10, 15, 12, 0, tzinfo=UTC),
    )


class FakeSession:
    """scalar(): count(...) → `count`, aks holda `row`; execute(): `rows`."""

    def __init__(self, rows=(), row=None, count=None):
        self.rows = list(rows)
        self.row = row
        self.count = len(self.rows) if count is None else count
        self.statements: list[str] = []
        self.committed = 0

    async def scalar(self, stmt):
        text = str(stmt)
        self.statements.append(text)
        return self.count if "count(" in text else self.row

    async def execute(self, stmt):
        self.statements.append(str(stmt))
        rows = self.rows

        class _Result:
            def scalars(self):
                return self

            def all(self):
                return rows

        return _Result()

    async def commit(self):
        self.committed += 1


# --------------------------------------------------------------------------- servis


async def test_item_shape():
    out = library.item(_row(is_saved=True))
    assert out == {
        "id": PID,
        "input_text": "restoran uchun logo",
        "kind": "image",
        "ai": "midjourney",
        "result": "/imagine minimal logo",
        "explanations": ["a — b"],
        "score": 82,
        "is_saved": True,
        "feedback": None,
        "created_at": datetime(2026, 10, 15, 12, 0, tzinfo=UTC),
    }


async def test_list_prompts_page_shape_and_order():
    session = FakeSession(rows=[_row(), _row(uuid.uuid4())], count=7)
    out = await library.list_prompts(session, UID, page=2, limit=20)
    assert out["total"] == 7
    assert out["page"] == 2
    assert out["limit"] == 20
    assert len(out["items"]) == 2
    sql = session.statements[-1]
    assert "ORDER BY prompts.created_at DESC" in sql
    assert "OFFSET" in sql and "LIMIT" in sql


async def test_list_prompts_filters_by_user():
    session = FakeSession(rows=[_row()])
    await library.list_prompts(session, UID)
    assert "prompts.user_id = " in session.statements[0]
    assert "prompts.is_saved IS true" not in session.statements[0]


async def test_library_filters_saved_only():
    session = FakeSession(rows=[_row(is_saved=True)])
    await library.list_prompts(session, UID, saved_only=True)
    assert "prompts.is_saved IS true" in session.statements[0]


async def test_empty_page():
    session = FakeSession(rows=[], count=0)
    out = await library.list_prompts(session, UID, page=5)
    assert out == {"items": [], "total": 0, "page": 5, "limit": 20}


async def test_set_saved_updates_and_commits():
    row = _row(is_saved=False)
    session = FakeSession(row=row)
    out = await library.set_saved(session, UID, PID, True)
    assert out["is_saved"] is True
    assert row.is_saved is True
    assert session.committed == 1


async def test_set_saved_can_unsave():
    row = _row(is_saved=True)
    out = await library.set_saved(FakeSession(row=row), UID, PID, False)
    assert out["is_saved"] is False


async def test_set_saved_foreign_prompt_is_404():
    session = FakeSession(row=None)  # user_id shartiga tushmadi
    with pytest.raises(HTTPException) as e:
        await library.set_saved(session, UID, PID, True)
    assert e.value.status_code == 404
    assert e.value.detail == library.NOT_FOUND
    assert session.committed == 0


async def test_delete_prompt_deletes_own():
    session = FakeSession(row=_row())
    await library.delete_prompt(session, UID, PID)
    assert any("DELETE FROM prompts" in s for s in session.statements)
    assert session.committed == 1


async def test_delete_foreign_prompt_is_404():
    session = FakeSession(row=None)
    with pytest.raises(HTTPException) as e:
        await library.delete_prompt(session, UID, PID)
    assert e.value.status_code == 404
    assert not any("DELETE FROM prompts" in s for s in session.statements)


# --------------------------------------------------------------------------- HTTP


@pytest.fixture
def session(monkeypatch):
    """`get_session` oʻrniga soxta sessiya (conftest None beradi)."""

    def _use(fake):
        async def _dep():
            yield fake

        app.dependency_overrides[get_session] = _dep
        return fake

    yield _use
    app.dependency_overrides.pop(get_session, None)


async def test_history_requires_login(client):
    r = await client.get("/api/prompts/history")
    assert r.status_code == 401


async def test_library_requires_login(client):
    r = await client.get("/api/prompts/library")
    assert r.status_code == 401


async def test_save_requires_login(client):
    r = await client.post(f"/api/prompts/{PID}/save", json={"saved": True})
    assert r.status_code == 401


async def test_delete_requires_login(client):
    r = await client.delete(f"/api/prompts/{PID}")
    assert r.status_code == 401


async def test_history_returns_items(client, as_user, session):
    session(FakeSession(rows=[_row(user_id=as_user.id)], count=1))
    r = await client.get("/api/prompts/history")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["limit"] == 20
    item = body["items"][0]
    assert item["id"] == str(PID)
    assert item["kind"] == "image"
    assert item["score"] == 82
    assert item["is_saved"] is False
    assert item["created_at"].startswith("2026-10-15T12:00:00")
    # tanlangan maydonlar: ichki holat tashqariga chiqmaydi
    assert set(item) == {
        "id",
        "input_text",
        "kind",
        "ai",
        "result",
        "explanations",
        "feedback",
        "score",
        "is_saved",
        "created_at",
    }


async def test_history_passes_page_and_limit(client, as_user, monkeypatch):
    seen = {}

    async def list_prompts(s, user_id, *, page, limit, saved_only=False):
        seen.update(user_id=user_id, page=page, limit=limit, saved_only=saved_only)
        return {"items": [], "total": 0, "page": page, "limit": limit}

    monkeypatch.setattr(library, "list_prompts", list_prompts)
    r = await client.get("/api/prompts/history?page=3&limit=5")
    assert r.status_code == 200
    assert seen == {"user_id": as_user.id, "page": 3, "limit": 5, "saved_only": False}


async def test_library_uses_saved_only(client, as_user, monkeypatch):
    seen = {}

    async def list_prompts(s, user_id, *, page, limit, saved_only=False):
        seen["saved_only"] = saved_only
        return {"items": [], "total": 0, "page": page, "limit": limit}

    monkeypatch.setattr(library, "list_prompts", list_prompts)
    assert (await client.get("/api/prompts/library")).status_code == 200
    assert seen["saved_only"] is True


@pytest.mark.parametrize("query", ["page=0", "limit=0", "limit=1000", "page=-1"])
async def test_history_validates_pagination(client, as_user, query):
    r = await client.get(f"/api/prompts/history?{query}")
    assert r.status_code == 422


async def test_save_returns_updated_item(client, as_user, session):
    session(FakeSession(row=_row(user_id=as_user.id)))
    r = await client.post(f"/api/prompts/{PID}/save", json={"saved": True})
    assert r.status_code == 200
    assert r.json()["is_saved"] is True
    assert r.json()["id"] == str(PID)


async def test_save_foreign_prompt_is_404(client, as_user, session):
    session(FakeSession(row=None))
    r = await client.post(f"/api/prompts/{PID}/save", json={"saved": True})
    assert r.status_code == 404
    assert r.json()["detail"] == library.NOT_FOUND


async def test_save_validates_body(client, as_user, session):
    session(FakeSession(row=_row(user_id=as_user.id)))
    r = await client.post(f"/api/prompts/{PID}/save", json={})
    assert r.status_code == 422


async def test_save_validates_uuid(client, as_user, session):
    session(FakeSession(row=_row(user_id=as_user.id)))
    r = await client.post("/api/prompts/not-a-uuid/save", json={"saved": True})
    assert r.status_code == 422


async def test_delete_own_prompt(client, as_user, session):
    fake = session(FakeSession(row=_row(user_id=as_user.id)))
    r = await client.delete(f"/api/prompts/{PID}")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    assert fake.committed == 1


async def test_delete_foreign_prompt_is_404_over_http(client, as_user, session):
    session(FakeSession(row=None))
    r = await client.delete(f"/api/prompts/{PID}")
    assert r.status_code == 404


# --------------------------------------------------------------- «ishladimi?» (A.4)


async def test_set_feedback_writes_answer_and_note():
    row = _row()
    session = FakeSession(row=row)
    out = await library.set_feedback(session, UID, PID, "not_worked", "  rasm boshqacha chiqdi  ")
    assert out["feedback"] == "not_worked"
    assert row.feedback_note == "rasm boshqacha chiqdi"
    assert session.committed == 1


async def test_set_feedback_rejects_unknown_answer():
    session = FakeSession(row=_row())
    with pytest.raises(HTTPException) as e:
        await library.set_feedback(session, UID, PID, "maybe")
    assert e.value.status_code == 422
    assert session.committed == 0


async def test_set_feedback_on_someone_elses_prompt_is_404():
    session = FakeSession(row=None)
    with pytest.raises(HTTPException) as e:
        await library.set_feedback(session, UID, PID, "worked")
    assert e.value.status_code == 404


async def test_pending_feedback_none_when_nothing_to_ask():
    session = FakeSession(row=None)
    assert await library.pending_feedback(session, UID) is None


async def test_pending_feedback_returns_short_item():
    session = FakeSession(row=_row())
    out = await library.pending_feedback(session, UID)
    assert out["id"] == PID
    assert out["kind"] == "image"
    assert out["score"] == 82
    # faqat kerakli maydonlar — prompt matni chiqmaydi
    assert set(out) == {"id", "kind", "ai", "input_text", "score", "created_at"}
