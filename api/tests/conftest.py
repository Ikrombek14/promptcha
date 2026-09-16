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
def _clear_pipeline_caches(monkeypatch):
    from app.ai import pipeline

    pipeline.reset_caches_for_tests()

    async def _no_prefetch(*a, **k):
        return None

    # analyze fonda reja tayyorlaydi — testlarda haqiqiy LLM chaqirilmasin
    monkeypatch.setattr(pipeline, "prefetch_plan", _no_prefetch)
    yield
    pipeline.reset_caches_for_tests()


@pytest.fixture(autouse=True)
def _no_db(monkeypatch):
    """Baza yoʻq: limit tekshiruvi va usage/llm_calls/prompt yozuvlari oʻchiriladi (alohida testlarda soxta sessiya bilan)."""

    async def _ok(*a, **k):
        return None

    monkeypatch.setattr(usage, "check_quota", _ok)
    monkeypatch.setattr(usage, "check_guest_quota", _ok)
    # jobs.py `from app.services import usage` qiladi — jobs.usage oʻsha modul, shu orqali patch
    monkeypatch.setattr(jobs.usage, "record_usage", _ok)
    monkeypatch.setattr(jobs.usage, "record_llm_calls", _ok)
    monkeypatch.setattr(jobs.usage, "save_prompt", _ok)
    monkeypatch.setattr(jobs.usage, "consume_bonus_if_needed", _ok)

    async def _session():
        yield None

    app.dependency_overrides[get_session] = _session
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def make_user():
    """Bazasiz User obyekti (auth dependency override uchun)."""
    import uuid

    from app.models import User

    def _make(email="user@example.com", plan="free", bonus=0, pro_until=None, is_admin=False):
        u = User(
            id=uuid.uuid4(),
            google_sub="sub-" + email,
            email=email,
            name=email.split("@")[0],
            plan=plan,
            bonus_generations=bonus,
            pro_until=pro_until,
        )
        if is_admin:
            os.environ["ADMIN_EMAILS"] = email
            from app.config import get_settings

            get_settings.cache_clear()
        return u

    return _make


@pytest.fixture
def as_user(make_user):
    """Soʻrovlar shu foydalanuvchi nomidan (cookie/JWT shart emas). Qaytaradi: User."""
    from app.services import auth as auth_service

    user = make_user()

    async def _current():
        return user

    app.dependency_overrides[auth_service.get_current_user] = _current
    yield user
    app.dependency_overrides.pop(auth_service.get_current_user, None)


@pytest.fixture
def as_admin(make_user):
    """Soʻrovlar admin nomidan (ADMIN_EMAILS shu email). Qaytaradi: User."""
    from app.config import get_settings
    from app.services import auth as auth_service

    user = make_user(email="admin@example.com", is_admin=True)

    async def _current():
        return user

    app.dependency_overrides[auth_service.get_current_user] = _current
    yield user
    app.dependency_overrides.pop(auth_service.get_current_user, None)
    os.environ.pop("ADMIN_EMAILS", None)
    get_settings.cache_clear()


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
