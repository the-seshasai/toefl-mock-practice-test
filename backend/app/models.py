from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Item(Base):
    """A generated question/prompt. content_hash enforces never-repeat."""

    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_item_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    task_type: Mapped[str] = mapped_column(String(40), index=True)
    difficulty: Mapped[str] = mapped_column(String(20))
    topic: Mapped[str] = mapped_column(String(120), default="")
    content_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    served: Mapped[bool] = mapped_column(default=False, index=True)  # False = in fallback/pre-generated bank
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(20))  # full | section | task
    difficulty: Mapped[str] = mapped_column(String(20))
    exam_mode: Mapped[str] = mapped_column(String(20), default="exam")  # exam | practice
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    overall_band: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sections: Mapped[list["SectionAttempt"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")


class SectionAttempt(Base):
    __tablename__ = "section_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"), index=True)
    section: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    band: Mapped[float | None] = mapped_column(Float, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempt: Mapped[Attempt] = relationship(back_populates="sections")
    responses: Mapped[list["Response"]] = relationship(back_populates="section_attempt", cascade="all, delete-orphan")


class Response(Base):
    """A user's answer to one served item, with its score and feedback."""

    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_attempt_id: Mapped[int] = mapped_column(ForeignKey("section_attempts.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    answer: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    section_attempt: Mapped[SectionAttempt] = relationship(back_populates="responses")
