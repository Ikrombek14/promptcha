"""LLM chaqiruvlarini oʻlchash (token hisobi) — contextvar orqali, pipeline'ga argument uzatilmaydi.

Ishlatish:
    meter = metering.new()          # job boshida (asyncio task ichida)
    metering.set_stage("classify")  # pipeline har bosqichda
    metering.record("groq", "openai/gpt-oss-120b", input_tokens=120, output_tokens=40, duration_ms=800)
    meter.calls                     # job oxirida bazaga yoziladi (services/usage.record_llm_calls)

Provayder token bermasa `estimate_tokens(text)` bilan taxmin qilinadi va `estimated=True`.
Meter yoʻq boʻlsa (masalan /analyze) `record` jim oʻtadi — hech narsa buzilmaydi.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field

Stage = str  # classify | clarify | generate | explain | facts

CHARS_PER_TOKEN = 4


@dataclass
class Call:
    stage: Stage
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated: bool = False
    ok: bool = True
    duration_ms: int = 0


@dataclass
class Meter:
    stage: Stage = "classify"
    calls: list[Call] = field(default_factory=list)

    @property
    def input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    @property
    def output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.calls)


_current: ContextVar[Meter | None] = ContextVar("promptcha_meter", default=None)


def new() -> Meter:
    """Joriy kontekst uchun yangi oʻlchagich (asyncio task ichida chaqirilsin)."""
    m = Meter()
    _current.set(m)
    return m


def current() -> Meter | None:
    return _current.get()


def clear() -> None:
    _current.set(None)


def set_stage(stage: Stage) -> None:
    m = _current.get()
    if m is not None:
        m.stage = stage


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN) if text else 0


def record(
    provider: str,
    model: str,
    *,
    input_tokens: int | None,
    output_tokens: int | None,
    input_text: str = "",
    output_text: str = "",
    ok: bool = True,
    duration_ms: int = 0,
) -> Call | None:
    """Bitta chaqiruvni yozadi. Token None boʻlsa matndan taxmin (estimated=True)."""
    m = _current.get()
    if m is None:
        return None
    estimated = input_tokens is None or output_tokens is None
    call = Call(
        stage=m.stage,
        provider=provider,
        model=model,
        input_tokens=input_tokens if input_tokens is not None else estimate_tokens(input_text),
        output_tokens=output_tokens if output_tokens is not None else estimate_tokens(output_text),
        estimated=estimated,
        ok=ok,
        duration_ms=duration_ms,
    )
    m.calls.append(call)
    return call
