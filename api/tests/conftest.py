import os

# Testlar bazaga ulanmaydi va haqiqiy API chaqirmaydi.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("APP_ENV", "test")

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import get_session
from app.main import app
from app.services import jobs, usage

# Brauzerdagi bizning kodimiz yuboradigan sarlavhalar (SecurityMiddleware talab qiladi)
BROWSER_HEADERS = {"X-Requested-With": "promptcha", "Origin": "http://localhost:3000"}

# Haqiqiy limit funksiyasi (autouse fixture uni oʻchiradi; test_usage shuni chaqiradi)
REAL_CHECK_GUEST_QUOTA = usage.check_guest_quota


@pytest.fixture(autouse=True)
def _clear_classify_cache():
    from app.ai import pipeline

    pipeline._classify_cache.clear()
    yield
    pipeline._classify_cache.clear()


@pytest.fixture(autouse=True)
def _no_db(monkeypatch):
    """Baza yoʻq: limit tekshiruvi va usage yozuvi oʻchiriladi (alohida testlarda soxta sessiya bilan)."""

    async def _ok(*a, **k):
        return None

    monkeypatch.setattr(usage, "check_guest_quota", _ok)
    monkeypatch.setattr(jobs, "record_usage", _ok)

    async def _session():
        yield None

    app.dependency_overrides[get_session] = _session
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", headers=BROWSER_HEADERS
    ) as c:
        yield c


@pytest.fixture
async def raw_client():
    """Sarlavhasiz mijoz — tashqi/skript soʻrovlarini modellashtiradi."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
