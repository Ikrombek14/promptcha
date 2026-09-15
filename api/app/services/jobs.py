"""Generate ishlari (job) — brauzerdan mustaqil yuradi.

Brauzer sahifani yangilasa yoki boshqa joyga oʻtsa, ish serverda davom etadi; qayta ulanganda
toʻplangan hodisalar boshidan qaytariladi (replay), keyin jonli davom etadi.
Xotira ichida (Redis yoʻq); bitta uvicorn jarayoni uchun yetarli.

Hisob: ish boshida `metering.new()`; oxirida (ok/xato/cancel) `usage.record_llm_calls`;
`done ok` da `usage.record_usage` (+ kirgan foydalanuvchida bonus sarfi va Prompt avto-saqlash).
"""

import asyncio
import logging
import secrets
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.ai import metering, pipeline
from app.schemas import GenerateRequest
from app.services import usage

log = logging.getLogger(__name__)

JOB_TTL_SECONDS = 15 * 60  # tugagan ish shuncha vaqt replay uchun saqlanadi
JOB_MAX_AGE_SECONDS = 60 * 60  # undan eski ish (tugamagan boʻlsa ham) oʻchiriladi
GENERIC_ERROR = "Prompt yasashda xatolik yuz berdi. Qayta urinib koʻring."
CANCELLED_ERROR = "Toʻxtatildi."

Event = tuple[str, dict]


@dataclass
class Job:
    id: str
    body: GenerateRequest
    ip: str = "unknown"
    user_id: uuid.UUID | None = None
    events: list[Event] = field(default_factory=list)
    done: bool = False
    created_at: float = field(default_factory=time.monotonic)
    cond: asyncio.Condition = field(default_factory=asyncio.Condition)
    task: asyncio.Task | None = None

    async def push(self, name: str, data: dict) -> None:
        async with self.cond:
            self.events.append((name, data))
            self.cond.notify_all()

    async def finish(self) -> None:
        async with self.cond:
            self.done = True
            self.cond.notify_all()


_jobs: dict[str, Job] = {}


def _prune() -> None:
    now = time.monotonic()
    for job_id, job in list(_jobs.items()):
        age = now - job.created_at
        if (job.done and age > JOB_TTL_SECONDS) or age > JOB_MAX_AGE_SECONDS:
            if job.task and not job.task.done():
                job.task.cancel()
            del _jobs[job_id]


async def _on_success(job: Job, meter: metering.Meter, done: dict, notes: list[str]) -> None:
    """Muvaffaqiyatli generate — server tomondagi limit hisobi va tarix."""
    await usage.record_usage(
        user_id=job.user_id,
        guest_id=job.body.guest_id,
        ip=job.ip,
        ai=done.get("ai"),
        input_tokens=meter.input_tokens,
        output_tokens=meter.output_tokens,
    )
    if job.user_id is not None:
        await usage.consume_bonus_if_needed(job.user_id)
        await usage.save_prompt(job.user_id, job.body, done, notes)


async def _run(job: Job, context: dict[str, str] | None) -> None:
    meter = metering.new()
    notes: list[str] = []
    try:
        async for name, data in pipeline.run(job.body, context):
            await job.push(name, data)
            if name == "explain":
                notes = list(data.get("notes") or [])
            elif name == "done" and data.get("status") == "ok":
                await _on_success(job, meter, data, notes)
    except asyncio.CancelledError:
        await job.push("error", {"detail": CANCELLED_ERROR})
        raise
    except pipeline.PipelineError as e:
        await job.push("error", {"detail": str(e)})
    except Exception:
        log.exception("job %s failed", job.id)
        await job.push("error", {"detail": GENERIC_ERROR})
    finally:
        await job.finish()
        await usage.record_llm_calls(meter, job)


def create(
    body: GenerateRequest,
    context: dict[str, str] | None = None,
    ip: str = "unknown",
    user_id: uuid.UUID | None = None,
) -> Job:
    _prune()
    job = Job(id=secrets.token_urlsafe(16), body=body, ip=ip, user_id=user_id)
    _jobs[job.id] = job
    job.task = asyncio.create_task(_run(job, context), name=f"generate:{job.id}")
    return job


def get(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def cancel(job_id: str) -> bool:
    job = _jobs.get(job_id)
    if job is None:
        return False
    if job.task and not job.task.done():
        job.task.cancel()
    return True


async def subscribe(job: Job) -> AsyncIterator[Event]:
    """Avval toʻplangan hodisalar (replay), keyin tugaguncha jonli hodisalar."""
    idx = 0
    while True:
        async with job.cond:
            while idx >= len(job.events) and not job.done:
                await job.cond.wait()
            batch = job.events[idx:]
            idx = len(job.events)
            finished = job.done and idx >= len(job.events)
        for ev in batch:
            yield ev
        if finished:
            return


def reset_for_tests() -> None:
    for job in _jobs.values():
        if job.task and not job.task.done():
            job.task.cancel()
    _jobs.clear()
