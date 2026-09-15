"""classify → clarify → generate → explain.

Har bir qadam alohida funksiya. `run()` SSE hodisalarini (name, data) koʻrinishida beradi.
Provayder bilan ishlash faqat app.ai.llm orqali.
"""

import re
import time
from collections.abc import AsyncIterator

from app.ai import llm
from app.ai.catalog import TOOLS, classifier_guide
from app.ai.llm import ProviderError
from app.ai.prompts import (
    KIND_NAMES,
    context_block,
    examples_block,
    locale_name,
    system_prompt,
)
from app.schemas import (
    ClarifyQuestion,
    ClarifyResult,
    Classification,
    ContextFacts,
    ExplainResult,
    GenerateRequest,
)

CONFIDENCE_THRESHOLD = 0.7

# Tahlil keshi: bir xil matn (analyze + keyin generate ichidagi classify) ikki marta soʻralmaydi
CLASSIFY_CACHE_TTL = 15 * 60
CLASSIFY_CACHE_MAX = 500
_classify_cache: dict[str, tuple[float, Classification]] = {}

PipelineError = ProviderError

_UZ_APOSTROPHE = re.compile(r"(?<=[oOgGоОгГ])[’‘'ʼ`´]")


def uz_fix(text: str) -> str:
    """Oʻzbek lotin matnida oʻ/gʻ uchun faqat ʻ (U+02BB) ishlatiladi — modellar ‘ yoki ' qoʻyadi."""
    return _UZ_APOSTROPHE.sub("ʻ", text)


def _localize(text: str, locale: str) -> str:
    return uz_fix(text) if locale == "uz" else text


# --------------------------------------------------------------------------- classify


async def classify(text: str) -> Classification:
    """Soʻzdan turni va 2–3 ta eng mos AI vositani taxmin qil. Tur ishonchi < 0.7 boʻlsa soʻraladi."""
    kinds = "\n".join(f"- {k}: {v}" for k, v in KIND_NAMES.items())
    system = (
        "You classify a user's request into exactly one output kind and recommend the best AI "
        "tools for it. The user writes in Uzbek, Russian or English, often informally, and may "
        "not know AI tools at all — they will only see the tools you pick.\n"
        f"Kinds:\n{kinds}\n"
        f"Tool catalog (id, name, supported kinds, popularity, strengths):\n{classifier_guide()}\n"
        "tools: return 2 or 3 tool ids, BEST FIRST. Pick only tools whose supported kinds include "
        "the chosen kind. Prefer the best fit for the concrete task; among equally good tools "
        "prefer the more popular one. Give at most one niche tool. Rules of thumb: a flyer/poster/"
        "logo/banner the user wants to SEE as a picture → kind=image (Midjourney, Ideogram for "
        "readable text, ChatGPT, Canva for editable layouts); a brief for a human designer → "
        "kind=design (Claude/ChatGPT); a spoken/narrated video with a presenter → heygen; voice-over "
        "only → elevenlabs; research with sources/prices/comparisons → perplexity; slide deck → gamma; "
        "Uzbek-only everyday text without VPN → salomai may be one of the options.\n"
        "Return your kind confidence honestly: 0.9+ only when unambiguous; if the text could "
        "reasonably be two kinds, stay below 0.7. reason: one short sentence in English."
    )
    key = " ".join(text.lower().split())
    cached = _classify_cache.get(key)
    if cached and time.monotonic() - cached[0] < CLASSIFY_CACHE_TTL:
        return cached[1].model_copy(deep=True)
    result = await llm.parse(system, text, Classification, max_tokens=400)
    # Katalogga mos kelmaydigan yoki turga toʻgʻri kelmaydigan vositalarni tozalash
    ok = [t for t in dict.fromkeys(result.tools) if result.kind in TOOLS[t].kinds]
    if not ok:
        ok = [
            t.id
            for t in sorted(TOOLS.values(), key=lambda t: -t.popularity)
            if result.kind in t.kinds
        ][:3]
    result.tools = ok[:3]
    if len(_classify_cache) >= CLASSIFY_CACHE_MAX:
        _classify_cache.pop(next(iter(_classify_cache)))
    _classify_cache[key] = (time.monotonic(), result.model_copy(deep=True))
    return result


# --------------------------------------------------------------------------- clarify


async def clarify(
    text: str,
    kind: str,
    ai: str,
    locale: str,
    context: dict[str, str] | None = None,
) -> list[ClarifyQuestion]:
    """1–2 ta qisqa aniqlashtiruvchi savol, chip variantlar bilan. Aniq boʻlsa — boʻsh roʻyxat."""
    system = (
        f"You help turn a rough idea into a precise prompt for {TOOLS[ai].name}. "
        f"The requested output kind is: {KIND_NAMES[kind]}.\n"
        "Decide what is genuinely missing to write an excellent prompt. Ask at most 2 questions, "
        "only about things that materially change the result (purpose, audience, style, format, "
        "key constraint). Do not ask what is already stated or implied. "
        "If the request is already clear enough, return an empty list.\n"
        f"Write questions in {locale_name(locale)}. Keep each under 12 words. "
        "Give 3–5 short chip options per question (2–4 words each), in the same language. "
        "id: short snake_case key in English (e.g. 'style', 'audience').\n"
        f"LANGUAGE RULE: question and options MUST be in {locale_name(locale)}; only the id is "
        "English.\n"
        f"{context_block(context)}"
    ).strip()
    result = await llm.parse(system, text, ClarifyResult, max_tokens=600)
    return [
        ClarifyQuestion(
            id=q.id,
            question=_localize(q.question, locale),
            options=[_localize(o, locale) for o in q.options],
        )
        for q in result.questions[:2]
    ]


# --------------------------------------------------------------------------- generate


def _generate_system(
    ai: str, kind: str, output_language: str, context: dict[str, str] | None
) -> str:
    lang = "English" if output_language == "en" else locale_name(output_language)
    parts = [
        system_prompt(ai, kind),
        (
            f"<task>\nTarget tool: {TOOLS[ai].name}. Output kind: {KIND_NAMES[kind]}.\n"
            f"Write the final prompt in {lang}. Output ONLY the prompt text — no preamble, "
            "no explanation, no markdown fences, no quotes around it.\n"
            "FACTS RULE: every proper name in the request — the user's brand, project, product, "
            "person, place (e.g. 'Promptcha', 'Urfon', 'Samarqand') — is a fact. Keep it exactly, "
            "with proper capitalization, wherever a name is needed (logo text, headline, title). "
            "Never replace a given name with generic words like BRAND, COMPANY, NAME or a "
            "[placeholder]. Use [placeholders] only for facts the user did NOT give (phone, address, "
            "price). The 'no brands' rule in the tool guide is about OTHER companies' brands and "
            "artists used as style references — it never applies to the user's own name.\n</task>"
        ),
        context_block(context),
        examples_block(ai, kind),
    ]
    return "\n\n".join(p for p in parts if p)


def _generate_user(text: str, answers: dict[str, str]) -> str:
    if not answers:
        return f"<request>\n{text}\n</request>"
    qa = "\n".join(f"- {k}: {v}" for k, v in answers.items())
    return f"<request>\n{text}\n</request>\n<clarifications>\n{qa}\n</clarifications>"


async def generate(
    text: str,
    kind: str,
    ai: str,
    answers: dict[str, str],
    output_language: str = "en",
    context: dict[str, str] | None = None,
) -> AsyncIterator[str]:
    """Promptni stream qilib qaytaradi (matn boʻlaklari)."""
    async for chunk in llm.stream(
        _generate_system(ai, kind, output_language, context),
        _generate_user(text, answers),
    ):
        yield chunk


# --------------------------------------------------------------------------- explain


async def explain(text: str, prompt: str, ai: str, locale: str) -> list[str]:
    """2–4 ta bir qatorlik izoh: nega prompt shunday yozildi."""
    system = (
        f"A prompt for {TOOLS[ai].name} was written from the user's request. "
        "Explain the 2–4 most important decisions in the prompt, one line each, "
        f"in {locale_name(locale)}, for a beginner. "
        "Each note: quote the key phrase/parameter from the prompt (keep the quote as is), "
        "then ' — ', then why it matters (max 20 words). No fluff, no numbering.\n"
        f"LANGUAGE RULE: every explanation after the dash MUST be written in {locale_name(locale)}. "
        "Do not write the explanations in English unless the language above is English."
    )
    user = f"<request>\n{text}\n</request>\n<prompt>\n{prompt}\n</prompt>"
    result = await llm.parse(system, user, ExplainResult, max_tokens=500)
    return [_localize(n, locale) for n in result.notes[:4]]


# --------------------------------------------------------------------------- context facts


async def extract_facts(text: str, answers: dict[str, str]) -> dict[str, str]:
    """Doimiy faktlar (soha, brend, uslub). Kirgan foydalanuvchi uchun UserContext'ga yoziladi."""
    system = (
        "Extract durable facts about the user that would be useful for their FUTURE requests: "
        "industry (e.g. 'restaurant'), brand name, preferred style, city, audience. "
        "Only facts explicitly stated. Keys in English snake_case, values short, in the user's "
        "language. Return an empty object if nothing durable is stated."
    )
    qa = "\n".join(f"- {k}: {v}" for k, v in answers.items())
    result = await llm.parse(system, f"{text}\n{qa}".strip(), ContextFacts, max_tokens=300)
    return result.facts


# --------------------------------------------------------------------------- orchestration


async def run(
    body: GenerateRequest,
    context: dict[str, str] | None = None,
) -> AsyncIterator[tuple[str, dict]]:
    """Toʻliq oqim. (event_name, data) juftliklarini beradi.

    - kind yoki ai berilmagan → classify; tur ishonchi past boʻlsa `done{status:needs_kind}`
    - answers boʻsh → clarify; savol boʻlsa `done{status:needs_clarification}` va toʻxtash
    - aks holda generate (stream) → explain → done{status:ok}
    Har `classify` va `done` hodisasida tanlangan/aniqlangan `ai` qaytadi.
    """
    kind = body.kind
    ai = body.ai
    if kind is None or ai is None:
        yield "stage", {"stage": "classify"}
        c = await classify(body.text)
        ask = kind is None and c.confidence < CONFIDENCE_THRESHOLD
        if ai is None:
            ai = c.ai
        yield (
            "classify",
            {
                "kind": c.kind,
                "confidence": round(c.confidence, 2),
                "ask": ask,
                "ai": ai,
                "tools": c.tools,
            },
        )
        if ask:
            yield "done", {"status": "needs_kind", "kind": c.kind, "ai": ai, "prompt": ""}
            return
        if kind is None:
            kind = c.kind

    if not body.answers:
        yield "stage", {"stage": "clarify"}
        questions = await clarify(body.text, kind, ai, body.locale, context)
        if questions:
            yield "clarify", {"questions": [q.model_dump() for q in questions]}
            yield "done", {"status": "needs_clarification", "kind": kind, "ai": ai, "prompt": ""}
            return

    parts: list[str] = []
    yield "stage", {"stage": "generate"}
    for attempt in range(2):
        try:
            async for chunk in generate(
                body.text, kind, ai, body.answers, body.output_language, context
            ):
                parts.append(chunk)
                yield "delta", {"text": chunk}
            break
        except llm.MidStreamError:
            # Provayder oqim oʻrtasida uzildi: mijozga "boshidan" deb aytamiz va qayta urinamiz
            if attempt == 1:
                raise
            parts = []
            yield "reset", {}
    prompt = "".join(parts).strip()
    if not prompt:
        raise PipelineError("Prompt boʻsh chiqdi. Qayta urinib koʻring.")

    yield "stage", {"stage": "explain"}
    notes = await explain(body.text, prompt, ai, body.locale)
    yield "explain", {"notes": notes}
    yield "done", {"status": "ok", "kind": kind, "ai": ai, "prompt": prompt}
