import uuid
from typing import Optional
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Classification, Feedback


def insert_classification_row(
    db: Session,
    classification_id: uuid.UUID,   # <-- UUID, not str
    model_version: str,
    embedding_model: str,
    threshold_used: float,
    label: str,
    score_produtivo: float,
    template_code: str,
    text_length_chars: int,
    latency_ms: int,
    language: str,
) -> None:
    """Insert a classification snapshot. Swallow errors so requests don't fail due to telemetry."""
    try:
        row = Classification(
            classification_id=classification_id,  # <-- pass UUID object
            model_version=model_version,
            embedding_model=embedding_model,
            threshold_used=Decimal(str(threshold_used)),
            label=label,
            score_produtivo=Decimal(str(round(score_produtivo, 4))),
            template_code=template_code,
            text_length_chars=text_length_chars,
            latency_ms=latency_ms,
            language=language,
        )
        db.add(row)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        # telemetry errors are intentionally swallowed


def classification_exists(db: Session, classification_id: uuid.UUID) -> bool:
    """Primary-key lookup; fastest way to check existence."""
    return db.get(Classification, classification_id) is not None


def upsert_feedback_row(
    db: Session,
    feedback_id: uuid.UUID,          # <-- UUID, not str
    classification_id: uuid.UUID,    # <-- UUID, not str
    helpful: bool,
    reason_code: Optional[str],
) -> None:
    """Insert or update feedback keyed by classification_id (unique). Raise on DB errors."""
    try:
        existing = db.execute(
            select(Feedback).where(Feedback.classification_id == classification_id)
        ).scalar_one_or_none()
        if existing:
            existing.helpful = helpful
            existing.reason_code = reason_code
        else:
            db.add(
                Feedback(
                    feedback_id=feedback_id,             # UUID object
                    classification_id=classification_id, # UUID object
                    helpful=helpful,
                    reason_code=reason_code,
                )
            )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
