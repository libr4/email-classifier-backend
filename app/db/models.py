# app/db/models.py
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

Base = declarative_base()

class Classification(Base):
    __tablename__ = "classification"

    # Use Postgres UUID + real uuid.UUID values
    classification_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,  # returns uuid.UUID
    )
    ts_utc: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False,
    )
    model_version: Mapped[str]    = mapped_column(sa.Text, nullable=False)
    embedding_model: Mapped[str]  = mapped_column(sa.Text, nullable=False)
    threshold_used: Mapped[float] = mapped_column(sa.Numeric(5, 4), nullable=False)
    label: Mapped[str]            = mapped_column(sa.Text, nullable=False)   # 'Produtivo' | 'Improdutivo'
    score_produtivo: Mapped[float]= mapped_column(sa.Numeric(5, 4), nullable=False)
    template_code: Mapped[str]    = mapped_column(sa.Text, nullable=False)   # 'status' | 'error' | ...
    text_length_chars: Mapped[int]= mapped_column(sa.Integer, nullable=False)
    latency_ms: Mapped[int]       = mapped_column(sa.Integer, nullable=False)
    language: Mapped[str]         = mapped_column(sa.Text, nullable=False)

    __table_args__ = (
        sa.CheckConstraint("threshold_used > 0 AND threshold_used <= 1", name="ck_threshold"),
        sa.CheckConstraint("score_produtivo >= 0 AND score_produtivo <= 1", name="ck_score"),
        sa.CheckConstraint("text_length_chars >= 0", name="ck_text_len"),
        sa.CheckConstraint("latency_ms >= 0", name="ck_latency"),
    )

    feedback: Mapped["Feedback"] = relationship(back_populates="classification", uselist=False)


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ts_utc: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False,
    )
    classification_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("classification.classification_id"),
        unique=True,
        nullable=False,
    )
    helpful: Mapped[bool]           = mapped_column(sa.Boolean, nullable=False)
    reason_code: Mapped[Optional[str]] = mapped_column(sa.Text)

    classification: Mapped[Classification] = relationship(back_populates="feedback")
