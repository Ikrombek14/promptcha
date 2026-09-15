"""Pydantic kirish/chiqish sxemalari."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.ai.catalog import TOOL_IDS, AiTool, Kind

Locale = Literal["uz", "ru", "en"]

KINDS: tuple[str, ...] = ("image", "app", "design", "video", "text")
AI_TOOLS: tuple[str, ...] = TOOL_IDS

__all__ = ["AI_TOOLS", "KINDS", "AiTool", "Kind", "Locale"]


# ---------- AI pipeline natijalari (structured output) ----------


class Classification(BaseModel):
    kind: Kind
    confidence: float = Field(ge=0, le=1)
    # Eng mos 2–3 vosita, birinchisi eng yaxshisi (foydalanuvchiga shular koʻrsatiladi)
    tools: list[AiTool] = Field(default_factory=lambda: ["chatgpt"], min_length=1, max_length=3)
    reason: str = ""

    @property
    def ai(self) -> AiTool:
        return self.tools[0]


class ClarifyQuestion(BaseModel):
    id: str
    question: str
    options: list[str] = Field(default_factory=list, max_length=5)


class ClarifyResult(BaseModel):
    questions: list[ClarifyQuestion] = Field(default_factory=list, max_length=2)


class ExplainResult(BaseModel):
    notes: list[str] = Field(default_factory=list, max_length=4)


class ContextFacts(BaseModel):
    """Foydalanuvchi matnidan aniqlangan doimiy faktlar."""

    facts: dict[str, str] = Field(default_factory=dict)


# ---------- HTTP ----------


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    locale: Locale = "uz"


class GenerateRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    ai: AiTool | None = None  # None → sayt oʻzi tanlaydi (classify)
    kind: Kind | None = None
    answers: dict[str, str] = Field(default_factory=dict)
    locale: Locale = "uz"
    output_language: Locale = "en"
    guest_id: str | None = Field(default=None, max_length=64)


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
    created_at: datetime

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: UUID
    email: str
    name: str | None
    avatar_url: str | None
    locale: str
    plan: str

    model_config = {"from_attributes": True}
