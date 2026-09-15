"""Server tomondagi guest/IP limitlari (soxta sessiya bilan)."""

import pytest
from fastapi import HTTPException

from app.services import usage
from tests.conftest import REAL_CHECK_GUEST_QUOTA


class FakeSession:
    """scalar() ketma-ket qiymatlar qaytaradi: [guest_total, ip_daily]"""

    def __init__(self, values):
        self.values = list(values)

    async def scalar(self, stmt):
        v = self.values.pop(0)
        if isinstance(v, Exception):
            raise v
        return v


async def test_guest_under_limit_passes():
    await REAL_CHECK_GUEST_QUOTA(FakeSession([2, 0]), "g1", "1.2.3.4")


async def test_guest_total_limit_429():
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_GUEST_QUOTA(FakeSession([3, 0]), "g1", "1.2.3.4")
    assert e.value.status_code == 429
    assert "Google" in e.value.detail


async def test_ip_daily_limit_429_even_with_new_guest_id():
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_GUEST_QUOTA(FakeSession([0, 15]), "fresh-guest", "1.2.3.4")
    assert e.value.status_code == 429
    assert "Bugungi" in e.value.detail


async def test_db_error_is_503_fail_closed():
    with pytest.raises(HTTPException) as e:
        await REAL_CHECK_GUEST_QUOTA(FakeSession([RuntimeError("db down")]), "g1", "1.2.3.4")
    assert e.value.status_code == 503


async def test_generate_route_enforces_quota(client, monkeypatch):
    async def deny(session, guest_id, ip):
        raise HTTPException(status_code=429, detail=usage.GUEST_EXHAUSTED)

    monkeypatch.setattr(usage, "check_guest_quota", deny)
    r = await client.post(
        "/api/prompts/generate",
        json={"text": "restoran uchun logo", "ai": "midjourney", "guest_id": "g1"},
    )
    assert r.status_code == 429
    assert r.json()["detail"] == usage.GUEST_EXHAUSTED
