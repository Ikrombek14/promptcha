"""Admin API: kirish nazorati (401/403), javob shakli (soxta servis), sof Pro/bonus qoidalari."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.services import admin as service
from app.services import settings as app_settings

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)

STATS = {
    "days": 30,
    "active_users": {"today": 1, "d7": 2, "d30": 3},
    "generations": {"today": 1, "d7": 5, "d30": 9},
    "tokens": {"input": 100, "output": 200},
    "by_tool": [{"ai": "chatgpt", "generations": 9, "input_tokens": 100, "output_tokens": 200}],
    "by_provider": [
        {
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
            "calls": 20,
            "input_tokens": 100,
            "output_tokens": 200,
            "estimated_calls": 2,
        }
    ],
    "by_stage": [{"stage": "generate", "calls": 9, "input_tokens": 50, "output_tokens": 150}],
    "top_users": [
        {
            "user_id": str(uuid.uuid4()),
            "email": "a@example.com",
            "generations": 9,
            "input_tokens": 100,
            "output_tokens": 200,
        }
    ],
    "daily": [{"date": "2026-09-15", "generations": 1, "input_tokens": 10, "output_tokens": 20}],
}


def _user_dict(user, **over):
    d = service.user_item(user, 3, 30, 60)
    d.update(over)
    return d


# ---------- kirish nazorati ----------


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/admin/stats"),
        ("GET", "/api/admin/users"),
        ("POST", f"/api/admin/users/{uuid.uuid4()}/grant"),
        ("GET", "/api/admin/payments"),
        ("POST", "/api/admin/payments"),
        ("GET", "/api/admin/settings"),
        ("PUT", "/api/admin/settings"),
    ],
)
async def test_anonymous_is_401(client, method, path):
    r = await client.request(method, path, json={})
    assert r.status_code == 401
    assert "Kirish" in r.json()["detail"]


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/admin/stats"),
        ("GET", "/api/admin/users"),
        ("POST", f"/api/admin/users/{uuid.uuid4()}/grant"),
        ("GET", "/api/admin/payments"),
        ("POST", "/api/admin/payments"),
        ("GET", "/api/admin/settings"),
        ("PUT", "/api/admin/settings"),
    ],
)
async def test_plain_user_is_403(client, as_user, method, path):
    r = await client.request(method, path, json={})
    assert r.status_code == 403
    assert "administrator" in r.json()["detail"]


# ---------- stats ----------


async def test_stats_ok_for_admin(client, as_admin, monkeypatch):
    seen = {}

    async def fake_stats(session, days):
        seen["days"] = days
        return STATS

    monkeypatch.setattr(service, "stats", fake_stats)
    r = await client.get("/api/admin/stats")
    assert r.status_code == 200
    assert seen["days"] == 30
    body = r.json()
    assert body["active_users"] == {"today": 1, "d7": 2, "d30": 3}
    assert body["by_provider"][0]["estimated_calls"] == 2
    assert body["daily"][0]["date"] == "2026-09-15"


async def test_stats_days_is_validated(client, as_admin, monkeypatch):
    async def fake_stats(session, days):
        return {**STATS, "days": days}

    monkeypatch.setattr(service, "stats", fake_stats)
    r = await client.get("/api/admin/stats?days=7")
    assert r.status_code == 200 and r.json()["days"] == 7
    assert (await client.get("/api/admin/stats?days=0")).status_code == 422
    assert (await client.get("/api/admin/stats?days=366")).status_code == 422


# ---------- users ----------


async def test_users_list_shape(client, as_admin, make_user, monkeypatch):
    u = make_user(email="x@example.com")
    u.created_at = NOW
    u.last_login_at = NOW
    calls = {}

    async def fake_list(session, q, page, limit):
        calls.update(q=q, page=page, limit=limit)
        return {"items": [_user_dict(u)], "total": 1, "page": page, "limit": limit}

    monkeypatch.setattr(service, "list_users", fake_list)
    r = await client.get("/api/admin/users?q=x&page=2&limit=10")
    assert r.status_code == 200
    assert calls == {"q": "x", "page": 2, "limit": 10}
    body = r.json()
    assert body["total"] == 1 and body["page"] == 2
    item = body["items"][0]
    assert item["id"] == str(u.id)
    assert item["email"] == "x@example.com"
    assert item["generations_total"] == 3
    assert item["last_login_at"].startswith("2026-09-15T12:00:00")
    assert item["is_admin"] is False
    assert set(item) == {
        "id",
        "email",
        "name",
        "avatar_url",
        "plan",
        "pro_until",
        "bonus_generations",
        "generations_total",
        "input_tokens",
        "output_tokens",
        "created_at",
        "last_login_at",
        "is_admin",
    }


async def test_users_limit_over_200_is_422(client, as_admin):
    r = await client.get("/api/admin/users?limit=201")
    assert r.status_code == 422


async def test_users_admin_flag(client, as_admin, monkeypatch):
    async def fake_list(session, q, page, limit):
        return {"items": [_user_dict(as_admin)], "total": 1, "page": 1, "limit": 50}

    monkeypatch.setattr(service, "list_users", fake_list)
    r = await client.get("/api/admin/users")
    assert r.json()["items"][0]["is_admin"] is True


# ---------- grant ----------


async def test_grant_passes_body_and_returns_user(client, as_admin, make_user, monkeypatch):
    u = make_user(email="g@example.com")
    got = {}

    async def fake_grant(session, user_id, plan, pro_days, bonus_generations):
        got.update(user_id=user_id, plan=plan, pro_days=pro_days, bonus=bonus_generations)
        service.extend_pro(u, pro_days, NOW)
        return _user_dict(u)

    monkeypatch.setattr(service, "grant", fake_grant)
    r = await client.post(f"/api/admin/users/{u.id}/grant", json={"pro_days": 30})
    assert r.status_code == 200
    assert got == {"user_id": u.id, "plan": None, "pro_days": 30, "bonus": None}
    assert r.json()["plan"] == "pro"
    assert r.json()["pro_until"].startswith("2026-10-15")


async def test_grant_validation(client, as_admin, make_user):
    u = make_user()
    for body in ({"pro_days": 0}, {"pro_days": 3651}, {"bonus_generations": 1001}, {"plan": "vip"}):
        r = await client.post(f"/api/admin/users/{u.id}/grant", json=body)
        assert r.status_code == 422, body
    r = await client.post("/api/admin/users/not-a-uuid/grant", json={"pro_days": 1})
    assert r.status_code == 422


async def test_grant_404_when_user_missing(client, as_admin, monkeypatch):
    async def fake_grant(session, user_id, **kw):
        raise HTTPException(status_code=404, detail=service.USER_NOT_FOUND)

    monkeypatch.setattr(service, "grant", fake_grant)
    r = await client.post(f"/api/admin/users/{uuid.uuid4()}/grant", json={"pro_days": 1})
    assert r.status_code == 404
    assert r.json()["detail"] == "Foydalanuvchi topilmadi."


async def test_grant_empty_body_is_422_pure():
    class S:  # bazaga yetmasdan turib rad etiladi
        pass

    with pytest.raises(HTTPException) as e:
        await service.grant(S(), uuid.uuid4())
    assert e.value.status_code == 422


# ---------- sof qoidalar ----------


def test_extend_pro_from_now_when_no_pro(make_user):
    u = make_user()
    service.extend_pro(u, 30, NOW)
    assert u.plan == "pro"
    assert u.pro_until == NOW + timedelta(days=30)


def test_extend_pro_adds_to_future_date(make_user):
    future = NOW + timedelta(days=10)
    u = make_user(plan="pro", pro_until=future)
    service.extend_pro(u, 5, NOW)
    assert u.pro_until == future + timedelta(days=5)


def test_extend_pro_expired_starts_from_now(make_user):
    u = make_user(plan="pro", pro_until=NOW - timedelta(days=3))
    service.extend_pro(u, 7, NOW)
    assert u.pro_until == NOW + timedelta(days=7)
    assert u.plan == "pro"


def test_extend_pro_makes_user_pro_now(make_user):
    u = make_user()
    service.extend_pro(u, 1)
    assert u.is_pro is True


def test_apply_bonus_adds_and_never_negative(make_user):
    u = make_user(bonus=2)
    service.apply_bonus(u, 5)
    assert u.bonus_generations == 7
    service.apply_bonus(u, -100)
    assert u.bonus_generations == 0
    u.bonus_generations = None
    service.apply_bonus(u, 3)
    assert u.bonus_generations == 3


def test_set_plan_free_clears_pro_until(make_user):
    u = make_user(plan="pro", pro_until=NOW + timedelta(days=30))
    service.set_plan(u, "free")
    assert u.plan == "free" and u.pro_until is None


def test_set_plan_pro_without_days_is_unlimited(make_user):
    u = make_user(plan="pro", pro_until=NOW - timedelta(days=1))
    service.set_plan(u, "pro")
    assert u.plan == "pro" and u.pro_until is None and u.is_pro is True


# ---------- payments ----------


async def test_payments_list(client, as_admin, make_user, monkeypatch):
    from app.models import Payment

    u = make_user(email="p@example.com")
    p = Payment(
        id=uuid.uuid4(),
        user_id=u.id,
        amount=49000,
        currency="UZS",
        method="manual",
        days=30,
        note="naqd",
        created_by="admin@example.com",
        paid_at=NOW,
    )

    async def fake_list(session, page, limit):
        return {
            "items": [service.payment_item(p, u.email)],
            "total": 1,
            "page": page,
            "limit": limit,
        }

    monkeypatch.setattr(service, "list_payments", fake_list)
    r = await client.get("/api/admin/payments")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["email"] == "p@example.com"
    assert item["amount"] == 49000 and item["days"] == 30
    assert item["provider_ref"] is None
    assert item["paid_at"].startswith("2026-09-15")


async def test_create_payment_passes_admin_email(client, as_admin, make_user, monkeypatch):
    from app.models import Payment

    u = make_user(email="p@example.com")
    got = {}

    async def fake_create(session, user_id, amount, days, method, note, created_by):
        got.update(user_id=user_id, amount=amount, days=days, method=method, created_by=created_by)
        p = Payment(
            id=uuid.uuid4(),
            user_id=user_id,
            amount=amount,
            currency="UZS",
            method=method,
            days=days,
            note=note,
            created_by=created_by,
            paid_at=NOW,
        )
        return service.payment_item(p, u.email)

    monkeypatch.setattr(service, "create_payment", fake_create)
    r = await client.post(
        "/api/admin/payments", json={"user_id": str(u.id), "amount": 49000, "days": 30}
    )
    assert r.status_code == 200
    assert got == {
        "user_id": u.id,
        "amount": 49000,
        "days": 30,
        "method": "manual",
        "created_by": "admin@example.com",
    }
    assert r.json()["created_by"] == "admin@example.com"


async def test_create_payment_validation(client, as_admin):
    uid = str(uuid.uuid4())
    for body in (
        {"user_id": uid, "amount": 1, "days": 0},
        {"user_id": uid, "amount": -1, "days": 1},
        {"user_id": uid, "amount": 1, "days": 1, "method": "cash"},
        {"user_id": uid, "amount": 1, "days": 1, "note": "x" * 501},
        {"amount": 1, "days": 1},
    ):
        r = await client.post("/api/admin/payments", json=body)
        assert r.status_code == 422, body


# ---------- settings ----------


async def test_settings_get(client, as_admin, monkeypatch):
    async def fake_view(session):
        return {
            "guest_total_generations": 3,
            "guest_daily_ip_generations": 15,
            "free_daily_generations": 5,
            "defaults": {
                "guest_total_generations": 3,
                "guest_daily_ip_generations": 15,
                "free_daily_generations": 5,
            },
        }

    monkeypatch.setattr(service, "get_settings_view", fake_view)
    r = await client.get("/api/admin/settings")
    assert r.status_code == 200
    assert r.json()["free_daily_generations"] == 5
    assert r.json()["defaults"]["guest_total_generations"] == 3


async def test_settings_put_passes_only_given_keys(client, as_admin, monkeypatch):
    got = {}

    async def fake_update(session, values):
        got.update(values)
        return {
            "guest_total_generations": 3,
            "guest_daily_ip_generations": 15,
            "free_daily_generations": 10,
            "defaults": {
                "guest_total_generations": 3,
                "guest_daily_ip_generations": 15,
                "free_daily_generations": 5,
            },
        }

    monkeypatch.setattr(service, "update_settings", fake_update)
    r = await client.put("/api/admin/settings", json={"free_daily_generations": 10})
    assert r.status_code == 200
    assert got == {"free_daily_generations": 10}
    assert r.json()["free_daily_generations"] == 10


class FakeSettingsSession:
    """set_int uchun: get → None, add → roʻyxatga; commit → belgi."""

    def __init__(self):
        self.added = []
        self.committed = False

    async def get(self, model, key):
        return None

    def add(self, row):
        self.added.append(row)

    async def commit(self):
        self.committed = True


async def test_settings_update_out_of_range_is_422(monkeypatch):
    s = FakeSettingsSession()
    with pytest.raises(HTTPException) as e:
        await service.update_settings(s, {"free_daily_generations": 5000})
    assert e.value.status_code == 422
    assert "oraligʻida" in e.value.detail
    assert s.committed is False


async def test_settings_update_empty_is_422():
    with pytest.raises(HTTPException) as e:
        await service.update_settings(FakeSettingsSession(), {"unknown_key": 1})
    assert e.value.status_code == 422


async def test_settings_update_writes_and_returns_view(monkeypatch):
    s = FakeSettingsSession()

    async def fake_limits(session=None):
        return {k: 1 for k in app_settings.LIMIT_KEYS}

    monkeypatch.setattr(app_settings, "get_limits", fake_limits)
    out = await service.update_settings(s, {"free_daily_generations": 7})
    assert s.committed is True
    assert [(r.key, r.value) for r in s.added] == [("free_daily_generations", "7")]
    assert out["free_daily_generations"] == 1
    assert set(out["defaults"]) == set(app_settings.LIMIT_KEYS)


async def test_settings_put_range_error_via_http(client, as_admin, monkeypatch):
    async def fake_update(session, values):
        raise HTTPException(status_code=422, detail="Notoʻgʻri qiymat — 0–1000")

    monkeypatch.setattr(service, "update_settings", fake_update)
    r = await client.put("/api/admin/settings", json={"free_daily_generations": 5000})
    assert r.status_code == 422
    assert "Notoʻgʻri" in r.json()["detail"]
