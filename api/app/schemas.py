"""Pydantic kirish/chiqish sxemalari."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.ai.catalog import TOOL_IDS, AiTool, Kind

Locale = Literal["uz", "ru", "en"]
# Nisbat — faqat rasm/video uchun maʼnoli (`ai.prompts.RATIO_KINDS`)
Ratio = Literal["1:1", "4:5", "16:9", "9:16"]

KINDS: tuple[str, ...] = ("image", "app", "design", "video", "text")
AI_TOOLS: tuple[str, ...] = TOOL_IDS
RATIOS: tuple[str, ...] = ("1:1", "4:5", "16:9", "9:16")

__all__ = ["AI_TOOLS", "KINDS", "RATIOS", "AiTool", "Kind", "Locale", "Ratio"]


# ---------- AI pipeline natijalari (structured output) ----------


class Classification(BaseModel):
    kind: Kind
    confidence: float = Field(ge=0, le=1)
    # Eng mos 2–3 vosita, birinchisi eng yaxshisi (foydalanuvchiga shular koʻrsatiladi)
    tools: list[AiTool] = Field(default_factory=lambda: ["chatgpt"], min_length=1, max_length=3)
    # Vazifa arxetipi (playbook): post, logo, plan ... — kind roʻyxatida boʻlmasa `general`
    archetype: str = "general"
    reason: str = ""

    @property
    def ai(self) -> AiTool:
        return self.tools[0]


class ClarifyQuestion(BaseModel):
    id: str
    question: str
    options: list[str] = Field(default_factory=list, max_length=5)


class Brief(BaseModel):
    """Reja (spec): prompt shu brif asosida yoziladi — taxmin oʻrniga aniq faktlar."""

    goal: str = ""
    deliverable: str = ""
    audience: str = ""
    tone: str = ""
    answer_language: str = ""
    constraints: list[str] = Field(default_factory=list, max_length=12)
    facts: dict[str, str] = Field(default_factory=dict)  # foydalanuvchi bergan: nom, raqam, joy
    missing: list[str] = Field(default_factory=list, max_length=12)  # playbook fact id'lari
    success_criteria: list[str] = Field(default_factory=list, max_length=8)
    framework: str = ""
    tool_params: dict[str, str] = Field(default_factory=dict)


class PlanResult(BaseModel):
    """Bitta chaqiruv: brif + (faqat yetishmayotgan hal qiluvchi faktlar uchun) ≤2 savol."""

    brief: Brief = Field(default_factory=Brief)
    questions: list[ClarifyQuestion] = Field(default_factory=list, max_length=2)


class ReviewCriterion(BaseModel):
    """Bitta mezon: 0–10 ball + nima yetishmayotgani.

    `ok` — eski maydon (ball ≥ 7 boʻlsa rost), moslik uchun saqlanadi.
    """

    name: str
    score: int = Field(default=10, ge=0, le=10)
    ok: bool = True
    note: str = ""


class Segment(BaseModel):
    """Promptning ketma-ket boʻlagi — frontend rangli koʻrsatadi.

    `text` lar birlashtirilganda asl prompt harfma-harf chiqadi; oradagi tinish va boʻshliqlar
    `type="plain"` boʻlak sifatida turadi. Toifalar kind boʻyicha: `ai.prompts.SEGMENT_TYPES`.
    """

    type: str = "plain"
    text: str = ""


class PromptPart(BaseModel):
    """«Prompt anatomiyasi» kartasi: promptdan qisqa parcha va nega kerakligi."""

    type: str = "plain"
    excerpt: str = ""  # ≤60 belgi
    why: str = ""  # foydalanuvchi tilida, ≤20 soʻz


class ReviewResult(BaseModel):
    """Tayyor promptni rubrika boʻyicha tekshirish: ball + izohlar («qoida — nega») + boʻlaklar."""

    score: int = Field(default=0, ge=0, le=100)
    criteria: list[ReviewCriterion] = Field(default_factory=list, max_length=6)
    notes: list[str] = Field(default_factory=list, max_length=4)
    # Model koʻp boʻlak qaytarishi mumkin — chegara qoʻymaymiz (validatsiya yiqilmasin),
    # serverda tozalanadi va kesiladi (`pipeline.review`).
    segments: list[Segment] = Field(default_factory=list)
    parts: list[PromptPart] = Field(default_factory=list)


class EnrichResult(BaseModel):
    """Qisqa gʻoyani 2–4 jumlaga kengaytirish (foydalanuvchi tilida)."""

    text: str = ""


class ContextFacts(BaseModel):
    """Foydalanuvchi matnidan aniqlangan doimiy faktlar."""

    facts: dict[str, str] = Field(default_factory=dict)


# ---------- HTTP ----------


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    locale: Locale = "uz"


class EventIn(BaseModel):
    """Brauzerdan keladigan bitta hodisa (`services/events.EVENT_NAMES` dagi nomlar)."""

    name: str = Field(max_length=48)
    payload: dict | None = None
    guest_id: str | None = Field(default=None, max_length=64)


class EventsIn(BaseModel):
    """Bir soʻrovda bir nechta hodisa (sendBeacon)."""

    session_id: str | None = Field(default=None, max_length=64)
    events: list[EventIn] = Field(default_factory=list, max_length=10)


class EnrichRequest(BaseModel):
    """«Gʻoyani boyitish»: qisqa matnni 2–4 jumlaga kengaytirish."""

    text: str = Field(min_length=3, max_length=2000)
    locale: Locale = "uz"


class ImproveRequest(BaseModel):
    """«Yaxshilash»: avvalgi prompt + tekshiruv izohlari asosida qayta yozish (savollarsiz)."""

    previous_prompt: str = Field(min_length=1, max_length=20000)
    feedback: list[str] = Field(default_factory=list, max_length=8)


class GenerateRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    ai: AiTool | None = None  # None → sayt oʻzi tanlaydi (classify)
    kind: Kind | None = None
    # Nisbat (aspect ratio) — faqat image/video turlarida qoʻllanadi, boshqa turda eʼtiborsiz
    ratio: Ratio | None = None
    answers: dict[str, str] = Field(default_factory=dict)
    locale: Locale = "uz"
    output_language: Locale = "en"
    guest_id: str | None = Field(default=None, max_length=64)
    # Brauzer sessiyasi — hodisalar voronkasini bogʻlash uchun (shaxsiy maʼlumot emas)
    session_id: str | None = Field(default=None, max_length=64)
    improve: ImproveRequest | None = None


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    locale: Locale = "uz"  # qaysi tilga


class PromptOut(BaseModel):
    id: UUID
    input_text: str
    kind: str
    ai: str
    clarifications: dict | None
    result: str
    explanations: list | None
    locale: str
    output_language: str
    share_slug: str | None
    is_public: bool
    is_saved: bool = False
    score: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    """«Prompt ishladimi?» javobi."""

    answer: Literal["worked", "not_worked"]
    note: str | None = Field(default=None, max_length=500)


class PendingFeedback(BaseModel):
    """Javob kutilayotgan prompt (yoʻq boʻlsa `item: null`)."""

    id: UUID
    kind: str
    ai: str
    input_text: str
    score: int | None = None
    created_at: datetime


class SaveRequest(BaseModel):
    """`POST /api/prompts/{id}/save` — kutubxonaga qoʻshish yoki olib tashlash."""

    saved: bool


class HistoryItem(BaseModel):
    """Tarix/kutubxona roʻyxatining bitta elementi."""

    id: UUID
    input_text: str
    kind: str
    ai: str
    result: str
    explanations: list | None = None
    score: int | None = None
    is_saved: bool = False
    feedback: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryPage(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    limit: int


class UserOut(BaseModel):
    id: UUID
    email: str
    name: str | None
    avatar_url: str | None
    locale: str
    plan: str

    model_config = {"from_attributes": True}
