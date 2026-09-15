"""/api/auth — Google oqimi (soxta Google), sessiya cookie, /me, logout, migrate, dev-login."""

import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest

from app.config import get_settings
from app.models import User
from app.services import auth as auth_service

COOKIE = "promptcha_session"


@pytest.fixture
def env(monkeypatch):
    """Env oʻzgartirib settings keshini tozalaydi; test oxirida kesh yana tozalanadi."""

    def _set(**kw):
        for k, v in kw.items():
            monkeypatch.setenv(k, v)
        get_settings.cache_clear()

    yield _set
    get_settings.cache_clear()


@pytest.fixture
def fake_google(monkeypatch):
    """Google'ga chiqmaydi: kod → token → userinfo → upsert (bazasiz)."""
    calls = {}

    async def _exchange(code):
        calls["code"] = code
        return "tok-123"

    async def _userinfo(token):
        calls["token"] = token
        return {
            "sub": "g-sub-1",
            "email": "Ali@Example.com",
            "name": "Ali",
            "picture": "https://p/ali.png",
        }

    async def _upsert(session, sub, email, name, avatar):
        calls["upsert"] = (sub, email, name, avatar)
        return User(id=uuid.uuid4(), google_sub=sub, email=email, name=name, avatar_url=avatar)

    monkeypatch.setattr(auth_service, "exchange_code", _exchange)
    monkeypatch.setattr(auth_service, "fetch_userinfo", _userinfo)
    monkeypatch.setattr(auth_service, "upsert_user", _upsert)
    return calls


def _set_cookies(r) -> list[str]:
    return r.headers.get_list("set-cookie")


def _session_cookie(r) -> str | None:
    return next((c for c in _set_cookies(r) if c.startswith(COOKIE + "=")), None)


async def _start(client, next_path="/uz/app") -> str:
    """GET /google → cookie mijoz jarida qoladi; Location'dagi `state` qaytadi."""
    r = await client.get("/api/auth/google", params={"next": next_path})
    assert r.status_code == 302
    return parse_qs(urlsplit(r.headers["location"]).query)["state"][0]


# ---------------------------------------------------------------- GET /google


async def test_google_redirects_with_state_cookie(client, env):
    env(GOOGLE_CLIENT_ID="cid-test")
    r = await client.get("/api/auth/google", params={"next": "/uz/app"})
    assert r.status_code == 302
    loc = urlsplit(r.headers["location"])
    assert loc.netloc == "accounts.google.com"
    q = parse_qs(loc.query)
    assert q["client_id"] == ["cid-test"]
    assert q["scope"] == ["openid email profile"]
    assert q["prompt"] == ["select_account"]
    assert q["response_type"] == ["code"]
    assert len(q["state"][0]) >= 20
    state_cookie = next(c for c in _set_cookies(r) if c.startswith(auth_service.STATE_COOKIE))
    assert "HttpOnly" in state_cookie
    assert "SameSite=lax" in state_cookie
    assert "Max-Age=600" in state_cookie


async def test_google_without_client_id_is_503(client, env):
    env(GOOGLE_CLIENT_ID="")
    r = await client.get("/api/auth/google")
    assert r.status_code == 503
    assert r.json()["detail"] == auth_service.GOOGLE_NOT_CONFIGURED


async def test_google_is_public_without_browser_headers(raw_client, env):
    env(GOOGLE_CLIENT_ID="cid-test")
    r = await raw_client.get("/api/auth/google")
    assert r.status_code == 302


# ---------------------------------------------------------------- GET /google/callback


async def test_callback_sets_session_and_redirects_to_next(client, env, fake_google):
    env(GOOGLE_CLIENT_ID="cid-test")
    state = await _start(client, "/ru/app")
    r = await client.get("/api/auth/google/callback", params={"code": "abc", "state": state})
    assert r.status_code == 302
    assert r.headers["location"] == get_settings().frontend_url + "/ru/app"
    cookie = _session_cookie(r)
    assert cookie is not None
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie
    # state cookie oʻchirildi
    assert any(
        c.startswith(auth_service.STATE_COOKIE) and "Max-Age=0" in c for c in _set_cookies(r)
    )
    assert fake_google["code"] == "abc"
    assert fake_google["token"] == "tok-123"
    assert fake_google["upsert"] == ("g-sub-1", "Ali@Example.com", "Ali", "https://p/ali.png")
    # cookie'dagi token haqiqiy sessiya
    token = cookie.split(";", 1)[0].split("=", 1)[1]
    assert auth_service.decode_token(token) is not None


async def test_callback_wrong_state_is_400(client, env, fake_google):
    env(GOOGLE_CLIENT_ID="cid-test")
    await _start(client)
    r = await client.get("/api/auth/google/callback", params={"code": "abc", "state": "boshqa"})
    assert r.status_code == 400
    assert r.json()["detail"] == auth_service.STATE_MISMATCH
    assert _session_cookie(r) is None


async def test_callback_without_state_cookie_is_400(client, env, fake_google):
    env(GOOGLE_CLIENT_ID="cid-test")
    r = await client.get("/api/auth/google/callback", params={"code": "abc", "state": "x"})
    assert r.status_code == 400


async def test_callback_open_redirect_falls_back_to_root(client, env, fake_google):
    env(GOOGLE_CLIENT_ID="cid-test")
    state = await _start(client, "//evil.com")
    r = await client.get("/api/auth/google/callback", params={"code": "abc", "state": state})
    assert r.status_code == 302
    assert r.headers["location"] == get_settings().frontend_url + "/"


async def test_callback_google_error_redirects_to_login(client, env, fake_google, monkeypatch):
    env(GOOGLE_CLIENT_ID="cid-test")

    async def _boom(code):
        raise auth_service.GoogleAuthError("tarmoq")

    monkeypatch.setattr(auth_service, "exchange_code", _boom)
    state = await _start(client, "/en/app")
    r = await client.get("/api/auth/google/callback", params={"code": "abc", "state": state})
    assert r.status_code == 302
    assert r.headers["location"] == get_settings().frontend_url + "/en/login?error=google"
    assert _session_cookie(r) is None


async def test_callback_user_denied_redirects_to_login(client, env, fake_google):
    env(GOOGLE_CLIENT_ID="cid-test")
    state = await _start(client, "/uz/app")
    r = await client.get(
        "/api/auth/google/callback", params={"error": "access_denied", "state": state}
    )
    assert r.status_code == 302
    assert r.headers["location"].endswith("/uz/login?error=google")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/uz/app", "/uz/app"),
        ("/ru/prompts?x=1", "/ru/prompts?x=1"),
        ("//evil.com", "/"),
        ("/\\evil.com", "/"),
        ("https://evil.com", "/"),
        ("uz/app", "/"),
        ("", "/"),
        (None, "/"),
        ("/uz\r\nSet-Cookie: x", "/"),
    ],
)
def test_safe_next(raw, expected):
    assert auth_service.safe_next(raw) == expected


def test_state_roundtrip_and_tamper():
    value = auth_service.sign_state("s1", "/uz/app")
    assert auth_service.load_state(value) == {"state": "s1", "next": "/uz/app"}
    assert auth_service.load_state(value + "x") is None
    assert auth_service.load_state(None) is None


# ---------------------------------------------------------------- GET /me


async def test_me_returns_profile(client, as_user, monkeypatch):
    async def _remaining(session, user):
        return 4

    monkeypatch.setattr(auth_service, "remaining_today", _remaining)
    r = await client.get("/api/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(as_user.id)
    assert body["email"] == as_user.email
    assert body["name"] == as_user.name
    assert body["avatar_url"] is None
    assert body["plan"] == "free"
    assert body["pro_until"] is None
    assert body["is_admin"] is False
    assert body["bonus_generations"] == 0
    assert body["remaining_today"] == 4


async def test_me_admin_and_pro_fields(client, as_admin, monkeypatch):
    as_admin.plan = "pro"
    as_admin.pro_until = datetime(2030, 1, 1, tzinfo=UTC)
    r = await client.get("/api/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["is_admin"] is True
    assert body["plan"] == "pro"
    assert body["pro_until"].startswith("2030-01-01")
    assert body["remaining_today"] is None  # Pro — cheksiz


async def test_me_without_cookie_is_401(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["detail"] == auth_service.NOT_LOGGED_IN


async def test_me_with_invalid_token_is_401(client):
    client.cookies.set(COOKIE, "yaroqsiz.token.qiymat")
    r = await client.get("/api/auth/me")
    assert r.status_code == 401


# ---------------------------------------------------------------- remaining_today


class FakeCountSession:
    def __init__(self, count):
        self.count = count

    async def scalar(self, stmt):
        return self.count


@pytest.mark.parametrize(
    ("plan", "bonus", "used", "limit", "expected"),
    [
        ("free", 0, 2, 5, 3),
        ("free", 0, 7, 5, 0),
        ("free", 3, 7, 5, 3),
        ("free", 1, 0, 5, 6),
    ],
)
async def test_remaining_today_math(make_user, monkeypatch, plan, bonus, used, limit, expected):
    async def _limit(key, session=None):
        assert key == "free_daily_generations"
        return limit

    monkeypatch.setattr(auth_service.app_settings, "get_int", _limit)
    user = make_user(plan=plan, bonus=bonus)
    assert await auth_service.remaining_today(FakeCountSession(used), user) == expected


async def test_remaining_today_pro_is_none(make_user):
    user = make_user(plan="pro", pro_until=datetime.now(UTC) + timedelta(days=3))
    assert await auth_service.remaining_today(None, user) is None
    expired = make_user(plan="pro", pro_until=datetime.now(UTC) - timedelta(days=1))
    assert expired.is_pro is False


async def test_remaining_today_without_session_uses_limit(make_user, monkeypatch):
    async def _limit(key, session=None):
        return 5

    monkeypatch.setattr(auth_service.app_settings, "get_int", _limit)
    user = make_user(bonus=2)
    assert await auth_service.remaining_today(None, user) == 7


# ---------------------------------------------------------------- POST /logout


async def test_logout_clears_cookie(client, as_user):
    r = await client.post("/api/auth/logout")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    cookie = _session_cookie(r)
    assert cookie is not None
    assert "Max-Age=0" in cookie


async def test_logout_when_not_logged_in_is_ok(client):
    r = await client.post("/api/auth/logout")
    assert r.status_code == 200


# ---------------------------------------------------------------- POST /migrate

PROMPT = {
    "input_text": "restoran uchun logo",
    "kind": "image",
    "ai": "midjourney",
    "clarifications": {"style": "minimal"},
    "result": "minimal restaurant logo --v 7",
    "explanations": ["qisqa", "aniq"],
    "locale": "uz",
}


async def test_migrate_saves_prompts(client, as_user, monkeypatch):
    got = {}

    async def _save(session, user_id, items):
        got["user_id"] = user_id
        got["items"] = items
        return len(items)

    monkeypatch.setattr(auth_service, "save_prompts", _save)
    r = await client.post("/api/auth/migrate", json={"prompts": [PROMPT, {**PROMPT, "ai": "flux"}]})
    assert r.status_code == 200
    assert r.json() == {"saved": 2}
    assert got["user_id"] == as_user.id
    assert got["items"][0]["input_text"] == "restoran uchun logo"
    assert got["items"][0]["output_language"] == "en"
    assert got["items"][1]["ai"] == "flux"


async def test_migrate_too_many_is_422(client, as_user, monkeypatch):
    async def _save(session, user_id, items):
        raise AssertionError("chaqirilmasligi kerak")

    monkeypatch.setattr(auth_service, "save_prompts", _save)
    r = await client.post("/api/auth/migrate", json={"prompts": [PROMPT] * 51})
    assert r.status_code == 422


async def test_migrate_invalid_kind_is_422(client, as_user):
    r = await client.post("/api/auth/migrate", json={"prompts": [{**PROMPT, "kind": "music"}]})
    assert r.status_code == 422


async def test_migrate_requires_login(client):
    r = await client.post("/api/auth/migrate", json={"prompts": [PROMPT]})
    assert r.status_code == 401


async def test_migrate_without_db_is_503(client, as_user):
    r = await client.post("/api/auth/migrate", json={"prompts": [PROMPT]})
    assert r.status_code == 503


class FakePromptSession:
    """execute() mavjud (input_text, result) juftliklarini beradi; add() ni sanaydi."""

    def __init__(self, existing):
        self.existing = existing
        self.added = []
        self.committed = False

    async def execute(self, stmt):
        class _R:
            def __init__(s, rows):
                s.rows = rows

            def all(s):
                return s.rows

        return _R(self.existing)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


async def test_save_prompts_skips_duplicates():
    session = FakePromptSession([("restoran uchun logo", "minimal restaurant logo --v 7")])
    items = [PROMPT, {**PROMPT, "result": "boshqa natija"}, {**PROMPT, "result": "boshqa natija"}]
    saved = await auth_service.save_prompts(session, uuid.uuid4(), items)
    assert saved == 1
    assert len(session.added) == 1
    assert session.added[0].result == "boshqa natija"
    assert session.committed


# ---------------------------------------------------------------- GET /dev-login


async def test_dev_login_sets_cookie_in_dev(client, env, monkeypatch):
    env(APP_ENV="development", AUTH_DEV_LOGIN="true")
    got = {}

    async def _upsert(session, sub, email, name, avatar):
        got["sub"] = sub
        return User(id=uuid.uuid4(), google_sub=sub, email=email, name=name)

    monkeypatch.setattr(auth_service, "upsert_user", _upsert)
    # `_no_db` fixture sessiyani None qiladi — soxta sessiya beramiz
    from app.db import get_session
    from app.main import app

    async def _session():
        yield object()

    app.dependency_overrides[get_session] = _session
    try:
        r = await client.get(
            "/api/auth/dev-login", params={"email": "Test@Example.com", "next": "/uz/app"}
        )
    finally:
        app.dependency_overrides.pop(get_session, None)
    assert r.status_code == 302
    assert r.headers["location"] == get_settings().frontend_url + "/uz/app"
    assert got["sub"] == "dev-test@example.com"
    cookie = _session_cookie(r)
    assert cookie is not None and "HttpOnly" in cookie


async def test_dev_login_is_404_in_production(client, env):
    env(APP_ENV="production", AUTH_DEV_LOGIN="true")
    r = await client.get("/api/auth/dev-login", params={"email": "a@b.c"})
    assert r.status_code == 404


async def test_dev_login_is_404_when_flag_off(client, env):
    env(APP_ENV="development", AUTH_DEV_LOGIN="false")
    r = await client.get("/api/auth/dev-login", params={"email": "a@b.c"})
    assert r.status_code == 404


async def test_dev_login_bad_email_is_422(client, env):
    env(APP_ENV="development", AUTH_DEV_LOGIN="true")
    r = await client.get("/api/auth/dev-login", params={"email": "notemail"})
    assert r.status_code == 422
