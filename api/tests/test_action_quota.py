"""Yordamchi endpointlarning kunlik chegarasi: analyze / enrich / translate.

Nega kerak: bu uchtasi generate limitiga kirmaydi, lekin har biri pul turadi
(LLM chaqiruvi yoki tarjima xizmati — har belgi uchun toʻlanadi). Chegara boʻlmasa
saytni ochmasdan, oddiy skript bilan hisobni boʻshatib yuborish mumkin.
"""

import pytest

from app.services import usage

pytestmark = pytest.mark.anyio


class _Session:
    """count() → `used` qaytaradi."""

    def __init__(self, used: int):
        self.used = used

    async def scalar(self, _stmt):
        return self.used


async def test_under_the_limit_passes():
    await usage.check_action_quota(_Session(5), "analyze", "1.2.3.4")


async def test_over_the_limit_is_429():
    limit = usage.ACTION_DAILY_LIMITS["translate"]
    with pytest.raises(Exception) as e:
        await usage.check_action_quota(_Session(limit), "translate", "1.2.3.4")
    assert getattr(e.value, "status_code", None) == 429


async def test_signed_in_user_gets_three_times_more(make_user):
    limit = usage.ACTION_DAILY_LIMITS["enrich"]
    user = make_user()
    # oddiy chegaradan oshgan, lekin 3× dan kam — oʻtadi
    await usage.check_action_quota(_Session(limit + 1), "enrich", "1.2.3.4", user)
    with pytest.raises(Exception) as e:
        await usage.check_action_quota(_Session(limit * 3), "enrich", "1.2.3.4", user)
    assert getattr(e.value, "status_code", None) == 429


async def test_pro_user_has_no_action_limit(make_user):
    from datetime import UTC, datetime, timedelta

    pro = make_user(plan="pro", pro_until=datetime.now(UTC) + timedelta(days=30))
    await usage.check_action_quota(_Session(10_000), "translate", "1.2.3.4", pro)


async def test_unknown_action_is_not_limited():
    await usage.check_action_quota(_Session(10_000), "whatever", "1.2.3.4")


async def test_db_error_does_not_block_the_user():
    class Broken:
        async def scalar(self, _stmt):
            raise RuntimeError("baza yoʻq")

    # Bu asosiy oqim emas — baza ishlamasa foydalanuvchi toʻxtab qolmaydi
    await usage.check_action_quota(Broken(), "analyze", "1.2.3.4")
