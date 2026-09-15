"""AI vositalar katalogi — sayt shu vositalar uchun prompt yozadi.

Foydalanuvchiga toʻliq roʻyxat koʻrsatilmaydi: classify har soʻrov uchun 2–3 ta eng mos va
mashhur vositani tanlaydi. Har vosita uchun prompt uslubi «oila» (family) orqali:
  chat | image | video | code | search | design | slides | voice | avatar
Bir vosita bir nechta turni (kind) qoʻllashi mumkin (masalan ChatGPT: matn + rasm).
"""

from dataclasses import dataclass
from typing import Literal

Kind = Literal["image", "app", "design", "video", "text"]
Family = Literal["chat", "image", "video", "code", "search", "design", "slides", "voice", "avatar"]

AiTool = Literal[
    "chatgpt",
    "claude",
    "gemini",
    "grok",
    "deepseek",
    "perplexity",
    "salomai",
    "midjourney",
    "flux",
    "ideogram",
    "firefly",
    "higgsfield",
    "veo",
    "kling",
    "seedance",
    "runway",
    "pika",
    "heygen",
    "canva",
    "gamma",
    "elevenlabs",
    "cursor",
]


@dataclass(frozen=True)
class Tool:
    id: str
    name: str
    version: str  # foydalanuvchiga koʻrsatiladi (2026-09 holati)
    kinds: tuple[str, ...]  # qaysi turlarga mos
    family: dict[str, str]  # kind → prompt oilasi
    note: str  # classifier uchun qisqa tavsif (kuchli tomoni)
    popularity: int  # 1..10 — teng sharoitda mashhurroq tanlanadi
    examples_dir: str | None = None  # examples/<dir>; None → oila papkasi


def _t(
    id: str,
    name: str,
    version: str,
    kinds: tuple[str, ...],
    family: dict[str, str],
    note: str,
    popularity: int,
    examples_dir: str | None = None,
) -> Tool:
    return Tool(id, name, version, kinds, family, note, popularity, examples_dir)


TOOLS: dict[str, Tool] = {
    t.id: t
    for t in [
        # ---- chat / umumiy
        _t(
            "chatgpt",
            "ChatGPT",
            "GPT-6 Astra",
            ("text", "image", "design", "app"),
            {"text": "chat", "design": "chat", "app": "chat", "image": "image"},
            "most popular general assistant: everyday texts, posts, plans, lessons; also makes images (GPT Image) with exact text/logos",
            10,
            examples_dir="chat",
        ),
        _t(
            "claude",
            "Claude",
            "Fable 5.1",
            ("text", "design", "app"),
            {"text": "chat", "design": "chat", "app": "chat"},
            "best for long careful writing, analysis, documents, contracts, structured briefs; strong at code",
            9,
            examples_dir="claude",
        ),
        _t(
            "gemini",
            "Gemini",
            "3.8 Flash",
            ("text", "image", "video", "design"),
            {"text": "chat", "design": "chat", "image": "image", "video": "video"},
            "Google assistant: chat, images and video (Veo inside), good with Google Docs/Sheets, free tier",
            9,
        ),
        _t(
            "grok",
            "Grok",
            "4.6",
            ("text", "image", "video"),
            {"text": "chat", "image": "image", "video": "video"},
            "xAI chat with real-time X/Twitter data; Grok Imagine makes images and short videos",
            6,
        ),
        _t(
            "deepseek",
            "DeepSeek",
            "V4-Pro",
            ("text", "app"),
            {"text": "chat", "app": "chat"},
            "free strong chat and coding model; good for budget users",
            7,
        ),
        _t(
            "perplexity",
            "Perplexity",
            "",
            ("text",),
            {"text": "search"},
            "research with cited sources: comparisons, prices, facts, latest news, market research",
            7,
        ),
        _t(
            "salomai",
            "Salom AI",
            "",
            ("text",),
            {"text": "chat"},
            "Uzbek-language assistant, works without VPN in Uzbekistan; everyday Uzbek texts",
            5,
        ),
        # ---- rasm
        _t(
            "midjourney",
            "Midjourney",
            "v7",
            ("image", "design"),
            {"image": "image", "design": "image"},
            "highest-quality artistic images, photos, illustrations, logos, posters (no reliable text inside image)",
            9,
            examples_dir="midjourney",
        ),
        _t(
            "flux",
            "Flux",
            "",
            ("image", "design"),
            {"image": "image", "design": "image"},
            "open photorealistic image model, follows long natural-language prompts precisely, renders text well",
            6,
        ),
        _t(
            "ideogram",
            "Ideogram",
            "",
            ("image", "design"),
            {"image": "image", "design": "image"},
            "best for images with readable text: logos, posters, banners, typography",
            6,
        ),
        _t(
            "firefly",
            "Adobe Firefly",
            "",
            ("image", "design"),
            {"image": "image", "design": "image"},
            "commercially safe images and design assets; integrates with Photoshop/Illustrator",
            5,
        ),
        _t(
            "higgsfield",
            "Higgsfield",
            "",
            ("image", "video"),
            {"image": "image", "video": "video"},
            "all video/image models in one place: cinematic camera motion, lipsync, effects",
            6,
        ),
        # ---- video
        _t(
            "veo",
            "Veo",
            "3.1",
            ("video",),
            {"video": "video"},
            "Google video with native sound and dialogue, realistic 8-second clips",
            9,
        ),
        _t(
            "kling",
            "Kling",
            "3.0",
            ("video",),
            {"video": "video"},
            "realistic motion and people, 5–10 s clips, image-to-video, good for product and lifestyle",
            8,
        ),
        _t(
            "seedance",
            "Seedance",
            "2.0",
            ("video",),
            {"video": "video"},
            "ByteDance video: multi-shot scenes, consistent characters, fast",
            6,
        ),
        _t(
            "runway",
            "Runway",
            "Gen-4.5",
            ("video",),
            {"video": "video"},
            "professional video generation and editing, precise camera control, image-to-video",
            7,
        ),
        _t(
            "pika",
            "Pika",
            "",
            ("video",),
            {"video": "video"},
            "short playful social videos and effects, quick and simple",
            5,
        ),
        _t(
            "heygen",
            "HeyGen",
            "",
            ("video",),
            {"video": "avatar"},
            "talking avatar videos, dubbing and lip-sync: presenters, ads, courses, explainers with a speaking person",
            7,
        ),
        # ---- dizayn / taqdimot / ovoz
        _t(
            "canva",
            "Canva AI",
            "",
            ("design", "image"),
            {"design": "design", "image": "design"},
            "ready design layouts: flyers, posts, banners, cards, menus with editable text; beginner friendly",
            9,
        ),
        _t(
            "gamma",
            "Gamma",
            "",
            ("design", "text"),
            {"design": "slides", "text": "slides"},
            "presentations and slide decks from a description; documents and one-pagers",
            7,
        ),
        _t(
            "elevenlabs",
            "ElevenLabs",
            "",
            ("text", "video"),
            {"text": "voice", "video": "voice"},
            "voice-over and narration from text; dubbing; realistic voices in many languages",
            6,
        ),
        # ---- kod
        _t(
            "cursor",
            "Cursor / Claude Code",
            "Agent",
            ("app",),
            {"app": "code"},
            "AI code editor and agents (Cursor, Claude Code, GitHub Copilot): build apps, sites, bots from a spec",
            8,
            examples_dir="cursor",
        ),
    ]
}

TOOL_IDS: tuple[str, ...] = tuple(TOOLS)


def family_for(tool_id: str, kind: str) -> str:
    """Vosita + tur → prompt oilasi. Mos kelmasa vositaning birinchi oilasi."""
    t = TOOLS[tool_id]
    return t.family.get(kind) or next(iter(t.family.values()))


def classifier_guide() -> str:
    lines = []
    for t in TOOLS.values():
        lines.append(
            f"- {t.id} ({t.name}; kinds: {', '.join(t.kinds)}; popularity {t.popularity}/10): {t.note}"
        )
    return "\n".join(lines)
