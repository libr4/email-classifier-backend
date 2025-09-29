# app/services/classifier_service.py
import uuid
import time
from typing import List, Optional
from app.ml.inference import infer_labels, decide_label
from app.ml.model_loader import META, EMB_ID, THRESHOLD
from app.utils.suggest import suggest_reply_pt
from app.utils.lang import detect_language
from app.core.config import LANG_SET, TELEMETRY_ON
from app.db.session import SessionLocal
from app.repositories.telemetry_repo import (
    insert_classification_row, upsert_feedback_row, classification_exists
)

def classify_one_service(text: str):
    start = time.perf_counter()
    p = float(infer_labels([text])[0])
    label = decide_label(p)
    suggestion, template_code = suggest_reply_pt(text, label)
    cid = uuid.uuid4()  
    latency_ms = int((time.perf_counter() - start) * 1000)
    lang = detect_language(text)

    if TELEMETRY_ON and SessionLocal:
        try:
            with SessionLocal() as db:
                insert_classification_row(
                    db=db,
                    classification_id=cid,  # <-- UUID object
                    model_version=META.get("created_at", "unknown"),
                    embedding_model=EMB_ID,
                    threshold_used=float(THRESHOLD),
                    label=label,
                    score_produtivo=float(p),
                    template_code=template_code,
                    text_length_chars=len(text),
                    latency_ms=latency_ms,
                    language=lang if lang in LANG_SET else "unknown",
                )
        except Exception:
            # Telemetry must never break the request
            pass

    return cid, label, p, suggestion  # FastAPI/Pydantic will serialize UUID

def classify_batch_service(texts: List[str]):
    start = time.perf_counter()
    probs = infer_labels(texts).tolist()
    results = []

    db_ctx = SessionLocal() if (TELEMETRY_ON and SessionLocal) else None
    try:
        for t, p in zip(texts, probs):
            label = decide_label(float(p))
            suggestion, template_code = suggest_reply_pt(t, label)
            cid = uuid.uuid4()  # <-- UUID object
            latency_ms = int((time.perf_counter() - start) * 1000)
            lang = detect_language(t)

            if db_ctx:
                try:
                    insert_classification_row(
                        db=db_ctx,
                        classification_id=cid,  # <-- UUID object
                        model_version=META.get("created_at", "unknown"),
                        embedding_model=EMB_ID,
                        threshold_used=float(THRESHOLD),
                        label=label,
                        score_produtivo=float(p),
                        template_code=template_code,
                        text_length_chars=len(t),
                        latency_ms=latency_ms,
                        language=lang if lang in LANG_SET else "unknown",
                    )
                except Exception:
                    pass

            results.append((cid, label, float(p), suggestion))
        if db_ctx:
            # ensure all pending inserts are flushed
            db_ctx.commit()
    finally:
        if db_ctx:
            db_ctx.close()

    return results

def submit_feedback_service(classification_id: uuid.UUID, helpful: bool, reason_code: Optional[str]) -> None:
    """Accept a real UUID here; your Pydantic schema can be UUID4 so FastAPI hands a uuid.UUID."""
    if not SessionLocal:
        raise RuntimeError("Telemetry disabled or DATABASE_URL not configured")
    with SessionLocal() as db:
        if not classification_exists(db, classification_id):
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="classification_id not found")
        upsert_feedback_row(
            db=db,
            feedback_id=uuid.uuid4(),         # <-- UUID object
            classification_id=classification_id,  # <-- UUID object
            helpful=helpful,
            reason_code=reason_code
        )
