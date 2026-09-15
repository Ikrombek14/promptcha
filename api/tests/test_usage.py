"""Server tomondagi limitlar (soxta sessiya bilan): guest/IP, kirgan bepul, bonus, Pro."""

import uuid

import pytest
from fastapi import HTTPException

from app.models import User
from app.services import settings as app_settings
from app.services import usage
from tests.conftest import REAL_CHECK_GUEST_QUOTA

# Modul import vaqtida — autouse `_no_db` fixture uni keyin no-op qiladi
REAL_CHECK_QUOTA = usage.check_quota

LIMITS = {
    "guest_total_generations": 3,
    "guest_daily_ip_generations": 15,
    "free_daily_generations": 5,
}


@pytest.fixture(autouse=True)
def _fixed_limits(monkeypatch):
    """Limitlar .env ga bogʻlanmaydi — settings.get_int soxta."""

    async def get_int(key, session=None):
        return LIMITS[key]

    monkeypatch.setattr(app_settings, "get_int", get_int)


class FakeSession:
    """scalar() ketma-ket qiymatlar qaytaradi: guest — [guest_total, ip_daily]; user — [today]"""

    def __init__(self, values):
        self.values = list(values)

    async def scalar(self, stmt):
        v = self.values.pop(0)
        if isinstance(v, Exception):
            raise v
        return v


def _user(plan="free", bonus=0, pro_until=None) -> User:
    return User(
        id=uuid.uuid4(),
        google_sub="s",
        email="u@example.com",
        plan=plan,
        bonus_generations=bonus,
        pro_until=pro_until,
    )


# --------------------------------------------------------------------------- guest


async def test_guest_under_limit_passes():
    await REAL_CHECK_GUEST_QUOTA(FakeSession([2, 0]), "g1", "1.2.3.4")


async def test_guest_total_limit_429():
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_GUEST_QUOTA(FakeSession([3, 0]), "g1", "1.2.3.4")
    assert e.value.status_code == 429
    assert "Google" in e.value.detail


async def test_ip_daily_limit_429_even_with_new_guest_id():
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_QUOTA(FakeSession([0, 15]), None, "fresh-guest", "1.2.3.4")
    assert e.value.status_code == 429
    assert "Bugungi" in e.value.detail


async def test_guest_limits_come_from_settings(monkeypatch):
    async def get_int(key, session=None):
        return {"guest_total_generations": 10, "guest_daily_ip_generations": 100}[key]

    monkeypatch.setattr(app_settings, "get_int", get_int)
    await REAL_CHECK_QUOTA(FakeSession([9, 50]), None, "g1", "1.2.3.4")


async def test_db_error_is_503_fail_closed():
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_GUEST_QUOTA(FakeSession([RuntimeError("db down")]), "g1", "1.2.3.4")
    assert e.value.status_code == 503


# --------------------------------------------------------------------------- kirgan foydalanuvchi


async def test_free_user_under_daily_limit_passes():
    await REAL_CHECK_QUOTA(FakeSession([4]), _user(), "g1", "1.2.3.4")


async def test_free_user_at_daily_limit_429():
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_QUOTA(FakeSession([5]), _user(), None, "1.2.3.4")
    assert e.value.status_code == 429
    assert e.value.detail == usage.USER_EXHAUSTED


async def test_free_user_at_limit_passes_with_bonus():
    await REAL_CHECK_QUOTA(FakeSession([5]), _user(bonus=1), None, "1.2.3.4")


async def test_pro_user_always_passes():
    # Pro'da baza soʻralmaydi — FakeSession boʻsh
    await REAL_CHECK_QUOTA(FakeSession([]), _user(plan="pro"), None, "1.2.3.4")


async def test_expired_pro_is_treated_as_free():
    from datetime import UTC, datetime, timedelta

    expired = _user(plan="pro", pro_until=datetime.now(UTC) - timedelta(days=1))
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_QUOTA(FakeSession([5]), expired, None, "1.2.3.4")
    assert e.value.status_code == 429


async def test_user_db_error_is_503():
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_QUOTA(FakeSession([RuntimeError("db down")]), _user(), None, "1.2.3.4")
    assert e.value.status_code == 503


# --------------------------------------------------------------------------- router


async def test_generate_route_enforces_quota(client, monkeypatch):
    async def deny(session, user, guest_id, ip):
        raise HTTPException(status_code=429, detail=usage.GUEST_EXHAUSTED)

    monkeypatch.setattr(usage, "check_quota", deny)
    r = await client.post(
        "/api/prompts/generate",
        json={"text": "restoran uchun logo", "ai": "midjourney", "guest_id": "g1"},
    )
    assert r.status_code == 429
    assert r.json()["detail"] == usage.GUEST_EXHAUSTED


async def test_generate_route_passes_user_to_quota(client, as_user, monkeypatch):
    seen = {}

    async def check(session, user, guest_id, ip):
        seen["user"] = user
        raise HTTPException(status_code=429, detail=usage.USER_EXHAUSTED)

    monkeypatch.setattr(usage, "check_quota", check)
    r = await client.post(
        "/api/prompts/generate", json={"text": "restoran uchun logo", "ai": "midjourney"}
    )
    assert r.status_code == 429
    assert r.json()["detail"] == usage.USER_EXHAUSTED
    assert seen["user"] is as_user
