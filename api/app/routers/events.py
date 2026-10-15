"""/api/events — brauzerdan keladigan mahsulot hodisalari (voronka oʻlchovi uchun).

Server oʻzi biladigan hodisalarni (`type_detected`, `prompt_generated`, `limit_reached`)
pipeline va usage xizmatlari yozadi; bu endpoint faqat brauzerda sodir boʻladiganlar uchun:
nusxa olish, ulashish, gʻoya yuborilishi, savollarga javob, «ishladimi?» javobi.

Hodisa yozilmasa ham soʻrov muvaffaqiyatli tugaydi — oʻlchov foydalanuvchi ishini buzmasin.
"""

from fastapi import APIRouter, Request

from app.schemas import EventsIn
from app.services import events as events_service
from app.services.auth import CurrentUser
from app.rate_limit import limiter

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=202)
@limiter.limit("120/minute")
async def collect(request: Request, body: EventsIn, user: CurrentUser) -> dict:
    """Bir nechta hodisani qabul qiladi (brauzer `sendBeacon` bilan yuboradi)."""
    for item in body.events:
        events_service.record(
            item.name,
            item.payload,
            user_id=user.id if user else None,
            guest_id=item.guest_id,
            session_id=body.session_id,
        )
    return {"status": "ok"}
