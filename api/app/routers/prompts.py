"""/api/prompts — analyze, generate (job + SSE). Router faqat HTTP bilan ishlaydi; AI mantiqi app.ai ichida.

Oqim:
  POST /api/prompts/analyze           → {kind, confidence, tools}
  POST /api/prompts/generate          → {"job_id"}  (ish fonda boshlanadi)
  GET  /api/prompts/jobs/{id}         → SSE: avval toʻplangan hodisalar, keyin jonli
  POST /api/prompts/jobs/{id}/cancel  → ishni toʻxtatish
Brauzer yangilansa ham ish davom etadi; qayta GET qilinsa boʻlgan joyidan ulanadi.
Limitlar: daqiqalik (IP), guest jami 3 (usage_log), IP kuniga 15.
"""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.ai import pipeline
from app.db import get_session
from app.rate_limit import limiter
from app.schemas import AnalyzeRequest, GenerateRequest
from app.security import client_ip
from app.services import jobs, usage

router = APIRouter(prefix="/prompts", tags=["prompts"])


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
    return {"kind": c.kind, "confidence": round(c.confidence, 2), "tools": c.tools}


@router.post("/generate")
@limiter.limit("20/minute")
async def generate(
    request: Request,
    body: GenerateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Ishni boshlaydi va id qaytaradi. Hodisalar: GET /jobs/{id}. Avval server limitlari."""
    ip = client_ip(request)
    await usage.check_guest_quota(session, body.guest_id, ip)
    job = jobs.create(body, ip=ip)
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
    explain   {notes:[...]}                         — izohlar
    done      {status, kind, ai, prompt}            — yakun. status: ok | needs_kind | needs_clarification
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
