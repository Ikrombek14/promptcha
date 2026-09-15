"""SQLAlchemy modellari: User, UserContext, Prompt, UsageLog."""

import uuid
from datetime import datetime

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

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
