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

#: Bitta soʻrovda nechta hodisa (sxemada ham cheklangan — bu ikkinchi chegara)
MAX_EVENTS = 10


@router.post("", status_code=202)
@limiter.limit("60/minute")
async def collect(request: Request, body: EventsIn, user: CurrentUser) -> dict:
    """Bir nechta hodisani qabul qiladi.

    Ishonch chegarasi: brauzer faqat **oʻzida** sodir boʻladigan hodisalarni yubora oladi
    (`CLIENT_EVENT_NAMES`). `prompt_generated` kabi server hodisalari bu yerdan qabul
    qilinmaydi — aks holda voronka raqamlarini istalgan odam toʻqib yozishi mumkin edi.
    Egalik ham serverdan olinadi: kirgan foydalanuvchida `user_id`, mehmonda esa
    brauzer bergan `guest_id` (u baribir ishonchsiz, faqat taxminiy hisob uchun).
    """
    for item in body.events[:MAX_EVENTS]:
        if item.name not in events_service.CLIENT_EVENT_NAMES:
            continue
        events_service.record(
            item.name,
            item.payload,
            user_id=user.id if user else None,
            guest_id=None if user else item.guest_id,
            session_id=body.session_id,
        )
    return {"status": "ok"}
