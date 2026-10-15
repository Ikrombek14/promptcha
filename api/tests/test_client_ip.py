"""Haqiqiy IP aniqlash — limitlar shunga tayanadi.

Nega muhim: `X-Forwarded-For` ni mijozning oʻzi ham yuborishi mumkin, proxy esa oʻzi
koʻrgan IP ni roʻyxat **oxiriga** qoʻshadi. Birinchi qiymatga ishonilsa, odam istalgan
IP yozib oʻz limitini aylanib oʻtadi yoki begona odamning kunlik hisobini yoqib yuboradi.
"""

import pytest

from app.config import get_settings
from app.security import client_ip


class _Req:
    def __init__(self, headers: dict[str, str], peer: str = "10.0.0.1"):
        self.headers = headers

        class _C:
            host = peer

        self.client = _C()


@pytest.fixture
def proxied(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "true")
    get_settings.cache_clear()
    yield
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    get_settings.cache_clear()


def test_forged_first_entry_is_ignored(proxied):
    """Mijoz yozgan qiymat emas, proxy qoʻshgan oxirgisi olinadi."""
    req = _Req({"x-forwarded-for": "203.0.113.9, 198.51.100.7"})
    assert client_ip(req) == "198.51.100.7"


def test_single_entry_is_the_client(proxied):
    assert client_ip(_Req({"x-forwarded-for": "198.51.100.7"})) == "198.51.100.7"


def test_x_real_ip_is_not_trusted(proxied):
    """Caddy `X-Real-IP` qoʻymaydi — demak uni faqat mijoz yuborgan boʻlishi mumkin."""
    assert client_ip(_Req({"x-real-ip": "203.0.113.9"})) == "10.0.0.1"


def test_without_proxy_the_socket_wins():
    get_settings.cache_clear()
    assert client_ip(_Req({"x-forwarded-for": "203.0.113.9"})) == "10.0.0.1"
