"""classify → plan (brif + savollar) → generate → review.

Har bir qadam alohida funksiya. `run()` SSE hodisalarini (name, data) koʻrinishida beradi.
Provayder bilan ishlash faqat app.ai.llm orqali. LLM chaqiruvlar: reja 1, prompt 1, tekshiruv 1.
Spec: docs/superpowers/specs/2026-09-16-quality-generation-design.md
"""

import asyncio
import logging
import re
import time
from collections.abc import AsyncIterator

from app.ai import llm, metering
from app.ai.catalog import TOOLS, classifier_guide
from app.ai.llm import ProviderError
from app.ai.prompts import (
    KIND_NAMES,
    RUBRIC,
    archetype_guide,
    brief_block,
    context_block,
    examples_block,
    locale_name,
    normalize_archetype,
    playbook,
    playbook_facts_block,
    playbook_rules_block,
    system_prompt,
)
from app.schemas import (
    Brief,
    ClarifyQuestion,
    Classification,
    ContextFacts,
    GenerateRequest,
    ImproveRequest,
    PlanResult,
    ReviewResult,
)

log = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7
NOT_SPECIFIED = "(not specified)"  # frontend «savolsiz yasash» shunday yuboradi

# Keshlar: bir xil matn uchun tahlil va reja qayta soʻralmaydi (analyze → generate → answers)
CACHE_TTL = 15 * 60
CACHE_MAX = 500
_classify_cache: dict[str, tuple[float, Classification]] = {}
_plan_cache: dict[tuple[str, str, str, str], tuple[float, PlanResult]] = {}

PipelineError = ProviderError

# Faqat harf oldidagi notoʻgʻri apostrof (oʻ, gʻ); qoʻshtirnoq sifatidagi ’ (soʻz oxirida) tegilmaydi
_UZ_APOSTROPHE = re.compile(r"(?<=[oOgGоОгГ])[’‘'ʼ`´](?=[A-Za-zА-Яа-яʻ])")
_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def unescape_unicode(text: str) -> str:
    """Model matn ichida qoldirgan backslash-u02bb kabi kodlarni harfga aylantiradi (JSON dekoder oʻtkazib yuborgan)."""
    return _UNICODE_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), text)


def uz_fix(text: str) -> str:
    """Oʻzbek lotin matnida oʻ/gʻ uchun faqat ʻ (U+02BB) ishlatiladi — modellar ‘ yoki ' qoʻyadi.

    Turkcha nuqtasiz ı (modellar «kısa» deb yozadi) oʻzbek lotinida yoʻq — i ga almashtiriladi.
    """
    return _UZ_APOSTROPHE.sub("ʻ", unescape_unicode(text)).replace("ı", "i").replace("İ", "I")


def _localize(text: str, locale: str) -> str:
    return uz_fix(text) if locale == "uz" else unescape_unicode(text)


def _cache_key(text: str) -> str:
    return " ".join(text.lower().split())


def _cache_put(cache: dict, key, value) -> None:
    if len(cache) >= CACHE_MAX:
        cache.pop(next(iter(cache)))
    cache[key] = (time.monotonic(), value)


def _cache_get(cache: dict, key):
    hit = cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL:
        return hit[1]
    return None


# --------------------------------------------------------------------------- classify


async def classify(text: str) -> Classification:
    """Soʻzdan turni, vazifa arxetipini va 2–3 ta eng mos AI vositani taxmin qil."""
    kinds = "\n".join(f"- {k}: {v}" for k, v in KIND_NAMES.items())
    system = (
        "You classify a user's request into exactly one output kind, one task archetype and "
        "recommend the best AI tools for it. The user writes in Uzbek, Russian or English, often "
        "informally, and may not know AI tools at all — they will only see the tools you pick.\n"
        f"Kinds:\n{kinds}\n"
        f"Archetypes per kind (id (title)):\n{archetype_guide()}\n"
        "archetype: the id from the chosen kind's list that best matches what the user wants "
        "made; use 'general' only when nothing fits.\n"
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
    key = _cache_key(text)
    cached = _cache_get(_classify_cache, key)
    if cached:
        return cached.model_copy(deep=True)
    result = await llm.parse(system, text, Classification, max_tokens=400, light=True)
    # Katalogga mos kelmaydigan yoki turga toʻgʻri kelmaydigan vositalarni tozalash
    ok = [t for t in dict.fromkeys(result.tools) if result.kind in TOOLS[t].kinds]
    if not ok:
        ok = [
            t.id
            for t in sorted(TOOLS.values(), key=lambda t: -t.popularity)
            if result.kind in t.kinds
        ][:3]
    result.tools = ok[:3]
    result.archetype = normalize_archetype(result.kind, result.archetype)
    _cache_put(_classify_cache, key, result.model_copy(deep=True))
    return result


# --------------------------------------------------------------------------- plan (brif + savollar)


def _plan_system(kind: str, ai: str, archetype: str, locale: str, context) -> str:
    pb = playbook(kind, archetype)
    return (
        f"You prepare a BRIEF for writing an excellent prompt for {TOOLS[ai].name} "
        f"(output kind: {KIND_NAMES[kind]}; task type: {pb.title}). The user is a beginner and "
        "writes informally in Uzbek, Russian or English.\n"
        "Fill `brief` strictly from what the user wrote:\n"
        "- goal (why they need it), deliverable (exactly what will be produced), audience, tone, "
        "answer_language (language the assistant should answer in — the audience's language; for "
        "image/video tools leave empty).\n"
        "- facts: every concrete fact the user gave — names, brand, product, numbers, prices, "
        "city, dates, links — keyed by short snake_case ids (use the required_facts ids when they "
        "match). Copy values verbatim, never invent or 'improve' them.\n"
        "- missing: ids from required_facts that the user did NOT give and whose default would "
        "noticeably change the result. If the default is fine, it is NOT missing.\n"
        "- constraints: limits stated or clearly implied (length, platform, budget, deadline, "
        "what to avoid). success_criteria: 2–4 checks a good result must pass. framework: one "
        "named method if it genuinely helps (SWOT, AIDA, PAS, SMART, RFM, 5W1H, Business Model "
        "Canvas…), else empty. tool_params: tool-specific settings implied by the task "
        "(e.g. aspect ratio, duration), else empty.\n"
        "Then `questions`: ask ONLY about the 1–2 most decisive ids in `missing` (at most 2, "
        "fewer is better; none if the defaults are good enough). Each question: id = the fact id, "
        f"text in {locale_name(locale)}, under 12 words, with 3–5 short options (2–4 words) that "
        "can be combined (facets, not exclusive choices). Never ask what the user already said.\n"
        f"LANGUAGE RULE: question and options MUST be in {locale_name(locale)}; ids and the "
        "brief fields are English.\n"
        f"{playbook_facts_block(pb)}\n"
        f"{context_block(context)}"
    ).strip()


async def plan(
    text: str,
    kind: str,
    ai: str,
    locale: str,
    context: dict[str, str] | None = None,
    archetype: str | None = None,
) -> PlanResult:
    """Brif + savollar (bitta chaqiruv). Kesh 15 min: analyze fonda tayyorlab qoʻyadi."""
    if archetype is None:
        archetype = (await classify(text)).archetype
    key = (_cache_key(text), kind, ai, locale)
    cached = _cache_get(_plan_cache, key)
    if cached:
        return cached.model_copy(deep=True)
    metering.set_stage("clarify")
    result = await llm.parse(
        _plan_system(kind, ai, archetype, locale, context),
        text,
        PlanResult,
        max_tokens=900,
        light=True,
    )
    questions = []
    for q in result.questions[:2]:
        if q.id in result.brief.facts:
            continue  # bor faktni soʻramaymiz
        said = _option_said_in_text(q.options, text)
        if said:
            # Foydalanuvchi buni allaqachon yozgan (masalan brend nomi) — savolsiz faktga aylanadi
            result.brief.facts[q.id] = said
            continue
        questions.append(
            ClarifyQuestion(
                id=q.id,
                question=_localize(q.question, locale),
                options=[_localize(o, locale) for o in q.options],
            )
        )
    result.questions = questions
    result.brief.missing = [
        m for m in dict.fromkeys(result.brief.missing) if m not in result.brief.facts
    ]
    _cache_put(_plan_cache, key, result.model_copy(deep=True))
    return result


def _option_said_in_text(options: list[str], text: str) -> str | None:
    """Variantlardan biri foydalanuvchi matnida soʻzma-soʻz bor boʻlsa — eng uzunini qaytaradi."""
    low = " ".join(text.lower().split())
    hits = [o for o in options if len(o.strip()) >= 3 and " ".join(o.lower().split()) in low]
    return max(hits, key=len).strip() if hits else None


async def prefetch_plan(text: str, kind: str, ai: str, locale: str) -> None:
    """analyze'dan fonda: foydalanuvchi «Prompt yasash» bosguncha savollar tayyor turadi."""
    from app.services import usage

    meter = metering.new()
    try:
        await plan(text, kind, ai, locale)
    except Exception as e:  # noqa: BLE001 — fon ishi, foydalanuvchiga taʼsir qilmaydi
        log.info("plan prefetch oʻtmadi: %s", str(e)[:120])
    finally:
        await usage.record_llm_calls(meter, job=None, job_id="prefetch")


def apply_answers(brief: Brief, questions: list[ClarifyQuestion], answers: dict[str, str]) -> Brief:
    """Javoblarni brifga qoʻshish — LLM'siz. «(not specified)» → default qoladi, missing'da turadi."""
    out = brief.model_copy(deep=True)
    for fid, value in answers.items():
        v = value.strip()
        if not v or v == NOT_SPECIFIED:
            continue
        out.facts[fid] = v
        out.missing = [m for m in out.missing if m != fid]
    return out


# --------------------------------------------------------------------------- generate


def _generate_system(
    ai: str,
    kind: str,
    archetype: str,
    output_language: str,
    brief: Brief | None,
    context: dict[str, str] | None,
) -> str:
    lang = "English" if output_language == "en" else locale_name(output_language)
    parts = [
        system_prompt(ai, kind),
        playbook_rules_block(playbook(kind, archetype)),
        RUBRIC,
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
            "artists used as style references — it never applies to the user's own name. "
            "This rule wins over the brief: a name written in <request> is never a placeholder "
            "even if the brief lists that id under `missing`. Copy names character by character, "
            "including the ʻ apostrophe (oʻ, gʻ).\n"
            "SELF-CHECK before you answer: walk through the rubric; if a criterion fails, fix the "
            "prompt, then output it. Keep the playbook's must-include items and quality rules; "
            "do not add sections the task does not need.\n</task>"
        ),
        brief_block(brief.model_dump_json(exclude_defaults=True)) if brief else "",
        context_block(context),
        examples_block(ai, kind),
    ]
    return "\n\n".join(p for p in parts if p)


def _generate_user(
    text: str, answers: dict[str, str], improve: ImproveRequest | None = None
) -> str:
    parts = [f"<request>\n{text}\n</request>"]
    if answers:
        qa = "\n".join(f"- {k}: {v}" for k, v in answers.items())
        parts.append(
            f"<clarifications>\n{qa}\n"
            "(a comma-separated value means the user chose several options — honour all of them)\n"
            "</clarifications>"
        )
    if improve is not None:
        fb = "\n".join(f"- {f}" for f in improve.feedback) or "- (no specific notes)"
        parts.append(
            f"<previous_prompt>\n{improve.previous_prompt}\n</previous_prompt>\n"
            f"<review_feedback>\n{fb}\n</review_feedback>\n"
            "REWRITE the previous prompt: keep everything that already works, fix every point in "
            "the feedback, and make it pass all rubric criteria. Output only the improved prompt."
        )
    return "\n".join(parts)


async def generate(
    text: str,
    kind: str,
    ai: str,
    answers: dict[str, str],
    output_language: str = "en",
    context: dict[str, str] | None = None,
    brief: Brief | None = None,
    archetype: str = "general",
    improve: ImproveRequest | None = None,
) -> AsyncIterator[str]:
    """Promptni stream qilib qaytaradi (matn boʻlaklari)."""
    async for chunk in llm.stream(
        _generate_system(ai, kind, archetype, output_language, brief, context),
        _generate_user(text, answers, improve),
    ):
        yield chunk


# --------------------------------------------------------------------------- review (ball + izohlar)


async def review(
    text: str, prompt: str, ai: str, locale: str, brief: Brief | None = None
) -> ReviewResult:
    """Tayyor promptni rubrika boʻyicha baholaydi: ball 0–100, 6 mezon, 2–4 izoh («qoida — nega»)."""
    system = (
        f"A prompt for {TOOLS[ai].name} was written from the user's request and brief. "
        "Grade it strictly against the rubric.\n"
        "criteria: exactly 6 items with names task_clear, facts_kept, measurable, audience_tone, "
        "constraints, no_filler; ok=true/false; note = what is missing when not ok (short, "
        f"in {locale_name(locale)}). score: 0–100 (roughly: each criterion ~16 points; deduct "
        "partially for weak spots). Be honest — 90+ only for prompts a professional would send "
        "as is.\n"
        "notes: the 2–4 most important decisions in the prompt, one line each, for a beginner: "
        "quote the key phrase/parameter from the prompt (keep the quote as is), then ' — ', "
        f"then why it matters (max 18 words, in {locale_name(locale)}). If a criterion failed, "
        "one note says what the user should add. No fluff, no numbering.\n"
        f"LANGUAGE RULE: every note and criterion note MUST be in {locale_name(locale)}.\n"
        f"{RUBRIC}"
    )
    user = (
        f"<request>\n{text}\n</request>\n"
        + (f"<brief>\n{brief.model_dump_json(exclude_defaults=True)}\n</brief>\n" if brief else "")
        + f"<prompt>\n{prompt}\n</prompt>"
    )
    result = await llm.parse(system, user, ReviewResult, max_tokens=700)
    result.notes = [_localize(n, locale) for n in result.notes[:4]]
    for c in result.criteria:
        c.note = _localize(c.note, locale)
    return result


# --------------------------------------------------------------------------- context facts


async def extract_facts(text: str, answers: dict[str, str]) -> dict[str, str]:
    """Doimiy faktlar (soha, brend, uslub). Kirgan foydalanuvchi uchun UserContext'ga yoziladi."""
    metering.set_stage("facts")
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

    - classify har doim (keshdan — analyze allaqachon qilgan): tur, arxetip, vositalar.
      Foydalanuvchi tanlagan kind/ai ustun; tur ishonchi past va tanlanmagan → `done{needs_kind}`
    - plan (keshdan yoki 1 chaqiruv): answers boʻsh va savol boʻlsa → `clarify` + `done{needs_clarification}`
    - answers bilan: brif += javoblar (LLM'siz) → generate (stream) → review → done{ok}
    Hodisa nomlari oʻzgarmagan: stage/classify/clarify/delta/reset/explain/done.
    """
    kind = body.kind
    ai = body.ai
    metering.set_stage("classify")
    if kind is None or ai is None:
        yield "stage", {"stage": "classify"}
    c = await classify(body.text)
    archetype = normalize_archetype(kind or c.kind, c.archetype)
    if kind is None or ai is None:
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
                "archetype": archetype,
            },
        )
        if ask:
            yield "done", {"status": "needs_kind", "kind": c.kind, "ai": ai, "prompt": ""}
            return
        if kind is None:
            kind = c.kind

    metering.set_stage("clarify")
    asking_allowed = not body.answers and body.improve is None
    if asking_allowed:
        yield "stage", {"stage": "clarify"}
    p = await plan(body.text, kind, ai, body.locale, context, archetype=archetype)
    if asking_allowed and p.questions:
        yield "clarify", {"questions": [q.model_dump() for q in p.questions]}
        yield "done", {"status": "needs_clarification", "kind": kind, "ai": ai, "prompt": ""}
        return
    brief = apply_answers(p.brief, p.questions, body.answers)

    parts: list[str] = []
    metering.set_stage("generate")
    yield "stage", {"stage": "generate"}
    for attempt in range(2):
        try:
            async for chunk in generate(
                body.text,
                kind,
                ai,
                body.answers,
                body.output_language,
                context,
                brief=brief,
                archetype=archetype,
                improve=body.improve,
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

    metering.set_stage("explain")
    yield "stage", {"stage": "explain"}
    r = await review(body.text, prompt, ai, body.locale, brief)
    yield (
        "explain",
        {
            "notes": r.notes,
            "score": r.score,
            "criteria": [cr.model_dump() for cr in r.criteria],
        },
    )
    yield "done", {"status": "ok", "kind": kind, "ai": ai, "prompt": prompt}


def reset_caches_for_tests() -> None:
    _classify_cache.clear()
    _plan_cache.clear()


__all__ = ["asyncio"]  # prefetch chaqiruvchilar uchun (router create_task)
