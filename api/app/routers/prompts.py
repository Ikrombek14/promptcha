"""/api/prompts — analyze, generate (job + SSE). Router faqat HTTP bilan ishlaydi; AI mantiqi app.ai ichida.

Oqim:
  POST /api/prompts/analyze           → {kind, confidence, tools}
  POST /api/prompts/enrich            → {text}  (qisqa gʻoyani 2–4 jumlaga kengaytirish)
  POST /api/prompts/generate          → {"job_id"}  (ish fonda boshlanadi)
  GET  /api/prompts/jobs/{id}         → SSE: avval toʻplangan hodisalar, keyin jonli
  POST /api/prompts/jobs/{id}/cancel  → ishni toʻxtatish
Brauzer yangilansa ham ish davom etadi; qayta GET qilinsa boʻlgan joyidan ulanadi.

Tarix va kutubxona (faqat kirgan foydalanuvchi, SQL `services/library.py` da):
  GET    /api/prompts/history?page=&limit=   → hamma yasalgan promptlar (yangidan eskiga)
  GET    /api/prompts/library?page=&limit=   → faqat saqlanganlar (`is_saved`)
  POST   /api/prompts/{id}/save              {saved} → yangilangan element
  DELETE /api/prompts/{id}                   → {"status": "ok"}
Limitlar (`services/usage.check_quota`, qiymatlar admin sozlamalaridan yoki .env):
  daqiqalik (IP, slowapi); guest jami `guest_total_generations` va IP kuniga
  `guest_daily_ip_generations`; kirgan bepul kuniga `free_daily_generations` (+ bonus); Pro cheksiz.
"""

import asyncio
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.ai import metering, pipeline
from app.db import get_session
from app.rate_limit import limiter
from app.schemas import (
    AnalyzeRequest,
    EnrichRequest,
    GenerateRequest,
    HistoryItem,
    HistoryPage,
    SaveRequest,
    TranslateRequest,
)
from app.security import client_ip
from app.services import jobs, library, usage
from app.services import translate as translate_service
from app.services.auth import CurrentUser, LoggedInUser

router = APIRouter(prefix="/prompts", tags=["prompts"])

Session = Annotated[AsyncSession, Depends(get_session)]
Page = Annotated[int, Query(ge=1)]
Limit = Annotated[int, Query(ge=1, le=library.PAGE_LIMIT_MAX)]


def _event(name: str, data: dict) -> dict:
    return {"event": name, "data": json.dumps(data, ensure_ascii=False)}


@router.post("/analyze")
@limiter.limit("30/minute")
async def analyze(request: Request, body: AnalyzeRequest):
    """Matnni tahlil: tur + 2–3 ta eng mos vosita (foydalanuvchi yozib toʻxtagach chaqiriladi)."""
    try:
        c = await pipeline.classify(body.text)
    except pipeline.PipelineError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    # Fonda reja (brif + savollar) tayyorlanadi — «Prompt yasash» bosilganda savollar 0 s da chiqadi
    asyncio.create_task(pipeline.prefetch_plan(body.text, c.kind, c.ai, body.locale))
    return {
        "kind": c.kind,
        "confidence": round(c.confidence, 2),
        "tools": c.tools,
        "archetype": c.archetype,
    }


@router.post("/enrich")
@limiter.limit("20/minute")
async def enrich(request: Request, body: EnrichRequest, user: CurrentUser):
    """«Gʻoyani boyitish»: qisqa matnni 2–4 jumlaga kengaytiradi (foydalanuvchi tilida)."""
    meter = metering.new()
    try:
        text = await pipeline.enrich(body.text, body.locale)
    except pipeline.PipelineError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    finally:
        await usage.record_llm_calls(
            meter, job=None, user_id=user.id if user else None, job_id="enrich"
        )
    return {"text": text}


@router.post("/translate")
@limiter.limit("20/minute")
async def translate(request: Request, body: TranslateRequest):
    """Tayyor promptni foydalanuvchi tiliga oʻgiradi (talab boʻyicha — har belgi pullik)."""
    text = await translate_service.translate(body.text, body.locale)
    return {"text": pipeline.uz_fix(text) if body.locale == "uz" else text}


@router.post("/generate")
@limiter.limit("20/minute")
async def generate(
    request: Request,
    body: GenerateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: CurrentUser,
):
    """Ishni boshlaydi va id qaytaradi. Hodisalar: GET /jobs/{id}. Avval server limitlari."""
    ip = client_ip(request)
    await usage.check_quota(session, user, body.guest_id, ip)
    job = jobs.create(body, ip=ip, user_id=user.id if user else None)
    return {"job_id": job.id}


@router.get("/jobs/{job_id}")
@limiter.limit("60/minute")
async def job_events(request: Request, job_id: str):
    """SSE hodisalari:

    stage     {stage}                               — bosqich boshlandi
    classify  {kind, confidence, ask, ai, tools}    — tur va vositalar
    clarify   {questions:[{id,question,options}]}   — aniqlashtiruvchi savollar
    delta     {text}                                — prompt boʻlagi (stream)
    reset     {}                                    — provayder uzildi, prompt boshidan
    explain   {notes, score, criteria, segments, parts}  — izohlar, ball, rangli boʻlaklar,
                                                      «anatomiya» kartalari
    done      {status, kind, ai, prompt, prompt_id} — yakun. status: ok | needs_kind |
                                                      needs_clarification. `prompt_id` faqat
                                                      `ok` da (kirmagan foydalanuvchida null)
    error     {detail}
    """
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Bu ish topilmadi yoki muddati oʻtgan.")

    async def stream():
        async for name, data in jobs.subscribe(job):
            yield _event(name, data)

    return EventSourceResponse(stream())


@router.post("/jobs/{job_id}/cancel")
@limiter.limit("30/minute")
async def cancel_job(request: Request, job_id: str):
    if not jobs.cancel(job_id):
        raise HTTPException(status_code=404, detail="Bu ish topilmadi yoki muddati oʻtgan.")
    return {"status": "cancelled"}


# ---------------------------------------------------------------- tarix va kutubxona


@router.get("/history", response_model=HistoryPage)
@limiter.limit("60/minute")
async def history(
    request: Request,
    session: Session,
    user: LoggedInUser,
    page: Page = 1,
    limit: Limit = 20,
):
    """Hamma yasalgan promptlar, yangidan eskiga."""
    return await library.list_prompts(session, user.id, page=page, limit=limit)


@router.get("/library", response_model=HistoryPage)
@limiter.limit("60/minute")
async def saved_library(
    request: Request,
    session: Session,
    user: LoggedInUser,
    page: Page = 1,
    limit: Limit = 20,
):
    """Faqat kutubxonaga saqlangan promptlar."""
    return await library.list_prompts(session, user.id, page=page, limit=limit, saved_only=True)


@router.post("/{prompt_id}/save", response_model=HistoryItem)
@limiter.limit("60/minute")
async def save_to_library(
    request: Request,
    prompt_id: UUID,
    body: SaveRequest,
    session: Session,
    user: LoggedInUser,
):
    """Kutubxonaga qoʻshish yoki olib tashlash. Begona prompt → 404."""
    return await library.set_saved(session, user.id, prompt_id, body.saved)


@router.delete("/{prompt_id}")
@limiter.limit("60/minute")
async def delete_prompt(
    request: Request,
    prompt_id: UUID,
    session: Session,
    user: LoggedInUser,
):
    """Oʻz promptini oʻchirish. Begona prompt → 404."""
    await library.delete_prompt(session, user.id, prompt_id)
    return {"status": "ok"}
