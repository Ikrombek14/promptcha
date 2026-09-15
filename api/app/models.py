"""SQLAlchemy modellari: User, UserContext, Prompt, UsageLog, LlmCall, Payment, AppSetting."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    google_sub: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(String(1000))
    locale: Mapped[str] = mapped_column(String(5), default="uz")
    plan: Mapped[str] = mapped_column(String(16), default="free")  # free | pro
    # Pro muddati (null = muddatsiz Pro, agar plan='pro'); toʻlov yozilganda uzayadi
    pro_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Admin bergan qoʻshimcha bepul urinishlar; kunlik limit tugagach sarflanadi
    bonus_generations: Mapped[int] = mapped_column(default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def is_pro(self) -> bool:
        if self.plan != "pro":
            return False
        if self.pro_until is None:
            return True
        return self.pro_until > datetime.now(UTC)

    contexts: Mapped[list["UserContext"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    prompts: Mapped[list["Prompt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserContext(Base):
    """Platforma foydalanuvchi haqida oʻrgangan doimiy faktlar (soha, brend, uslub)."""

    __tablename__ = "user_contexts"
    __table_args__ = (Index("ix_user_contexts_user_key", "user_id", "key", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(64))  # industry | brand | style | favorite_ai | ...
    value: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(16), default="inferred")  # inferred | user
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="contexts")


class Prompt(Base):
    """Har bir yasalgan prompt — tarix."""

    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    input_text: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(16))  # image | app | design | video | text
    ai: Mapped[str] = mapped_column(
        String(16)
    )  # chatgpt | claude | midjourney | dalle | sora | cursor
    clarifications: Mapped[dict | None] = mapped_column(JSON)  # {question_id: answer}
    result: Mapped[str] = mapped_column(Text)
    explanations: Mapped[list | None] = mapped_column(JSON)  # ["...", "..."]
    locale: Mapped[str] = mapped_column(String(5), default="uz")
    output_language: Mapped[str] = mapped_column(String(5), default="en")
    share_slug: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User | None"] = relationship(back_populates="prompts")


class UsageLog(Base):
    """Rate limit hisobi: kim, qachon, nima qildi."""

    __tablename__ = "usage_log"
    __table_args__ = (
        Index("ix_usage_log_user_created", "user_id", "created_at"),
        Index("ix_usage_log_ip_created", "ip", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    guest_id: Mapped[str | None] = mapped_column(String(64), index=True)
    ip: Mapped[str | None] = mapped_column(String(45))  # IPv4/IPv6; kunlik IP limiti uchun
    action: Mapped[str] = mapped_column(String(32), default="generate")
    ai: Mapped[str | None] = mapped_column(String(16))
    input_tokens: Mapped[int | None] = mapped_column()
    output_tokens: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LlmCall(Base):
    """Har bir LLM chaqiruvi: qaysi bosqich, provayder, model, qancha token (admin statistikasi)."""

    __tablename__ = "llm_calls"
    __table_args__ = (
        Index("ix_llm_calls_provider_created", "provider", "created_at"),
        Index("ix_llm_calls_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    guest_id: Mapped[str | None] = mapped_column(String(64))
    job_id: Mapped[str | None] = mapped_column(String(32))
    stage: Mapped[str] = mapped_column(
        String(16)
    )  # classify | clarify | generate | explain | facts
    provider: Mapped[str] = mapped_column(String(32))  # groq | gemini | ...
    model: Mapped[str] = mapped_column(String(80))
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    estimated: Mapped[bool] = mapped_column(Boolean, default=False)  # provayder token bermadi
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    duration_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class Payment(Base):
    """Toʻlov yozuvi. Hozir qoʻlda (admin), keyin Payme/Click shu jadvalga yozadi."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[int] = mapped_column()  # soʻm
    currency: Mapped[str] = mapped_column(String(3), default="UZS")
    method: Mapped[str] = mapped_column(String(16), default="manual")  # manual | payme | click
    days: Mapped[int] = mapped_column()  # Pro necha kunga uzaydi
    note: Mapped[str | None] = mapped_column(Text)
    provider_ref: Mapped[str | None] = mapped_column(String(128))  # Payme/Click tranzaksiya id
    created_by: Mapped[str | None] = mapped_column(String(320))  # admin email
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class AppSetting(Base):
    """Admin oʻzgartiradigan sozlamalar (limitlar). Yoʻq kalit → .env qiymati."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
