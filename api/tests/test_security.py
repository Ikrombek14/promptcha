"""Kirish nazorati: tashqi/skript soʻrovlar rad etiladi, sayt soʻrovlari oʻtadi."""

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.config import Settings
from app.security import SecurityMiddleware

BODY = {"text": "restoran uchun logo kerak", "locale": "uz"}


async def test_health_is_public(raw_client):
    r = await raw_client.get("/api/health")
    assert r.status_code == 200


async def test_missing_requested_with_is_rejected(raw_client):
    r = await raw_client.post(
        "/api/prompts/analyze", json=BODY, headers={"Origin": "http://localhost:3000"}
    )
    assert r.status_code == 403
    assert "sayt orqali" in r.json()["detail"]


async def test_foreign_origin_is_rejected(raw_client):
    r = await raw_client.post(
        "/api/prompts/analyze",
        json=BODY,
        headers={"X-Requested-With": "promptcha", "Origin": "https://evil.example"},
    )
    assert r.status_code == 403


async def test_post_without_origin_or_referer_is_rejected(raw_client):
    r = await raw_client.post(
        "/api/prompts/analyze", json=BODY, headers={"X-Requested-With": "promptcha"}
    )
    assert r.status_code == 403


async def test_referer_from_site_is_enough_for_get(raw_client):
    r = await raw_client.get(
        "/api/prompts/jobs/yoq",
        headers={"X-Requested-With": "promptcha", "Referer": "http://localhost:3000/uz/app"},
    )
    assert r.status_code == 404  # oʻtdi, ish topilmadi


async def test_oversized_body_is_rejected(client):
    r = await client.post(
        "/api/prompts/analyze",
        content=b"{" + b" " * (70 * 1024) + b"}",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 413


async def test_security_headers_present(client):
    r = await client.get("/api/health")
    assert r.headers["cache-control"] == "no-store"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def _mini_app(settings: Settings):
    async def ok(request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/api/x", ok, methods=["GET", "POST"])])
    return SecurityMiddleware(app, settings)


async def test_internal_key_required_when_configured():
    s = Settings(
        internal_api_key="k" * 32,
        cors_origins="https://promptcha.uz",
        frontend_url="https://promptcha.uz",
    )
    async with AsyncClient(transport=ASGITransport(app=_mini_app(s)), base_url="http://t") as c:
        base = {"X-Requested-With": "promptcha", "Origin": "https://promptcha.uz"}
        assert (await c.post("/api/x", headers=base)).status_code == 403
        assert (
            await c.post("/api/x", headers={**base, "X-Internal-Key": "x" * 32})
        ).status_code == 403
        assert (
            await c.post("/api/x", headers={**base, "X-Internal-Key": "k" * 32})
        ).status_code == 200


@pytest.mark.parametrize(
    ("overrides", "expect_problem"),
    [
        ({}, "APP_SECRET"),
        (
            {
                "app_secret": "a" * 40,
                "jwt_secret": "b" * 40,
                "internal_api_key": "c" * 40,
                "trust_proxy": True,
                "cors_origins": "https://promptcha.uz",
                "frontend_url": "https://promptcha.uz",
                "database_url": "postgresql+asyncpg://promptcha:Str0ngPass@localhost/promptcha",
            },
            None,
        ),
    ],
)
def test_production_problems(overrides, expect_problem):
    s = Settings(app_env="production", **overrides)
    problems = s.production_problems()
    if expect_problem is None:
        assert problems == []
    else:
        assert any(expect_problem in p for p in problems)


def test_dev_has_no_production_problems():
    assert Settings(app_env="development").production_problems() == []
