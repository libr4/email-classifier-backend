from typing import List
from fastapi import APIRouter, HTTPException, status, Request

from app.api.v1.schemas import (
    ClassifyIn, ClassifyBatchIn, ClassificationOut, ClassificationBatchOut, FeedbackIn
)
from app.ml.model_loader import META, EMB_ID, THRESHOLD
from app.services.classifier_service import (
    classify_one_service, classify_batch_service, submit_feedback_service
)

router = APIRouter()

@router.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "model_version": META.get("created_at", "unknown"),
        "embedding_model": EMB_ID,
        "threshold": THRESHOLD,
        # Telemetry readiness is now implicit; DB errors won't bubble here
    }

@router.post("/classify", response_model=ClassificationOut)
def classify_one(payload: ClassifyIn, request: Request):
    try:
        cid, label, p, suggestion = classify_one_service(payload.text)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not ready") from e

    return ClassificationOut(
        classification_id=cid,
        label=label,
        score_produtivo=round(float(p), 3),
        threshold_used=THRESHOLD,
        suggestion=suggestion
    )

@router.post("/classify_batch", response_model=ClassificationBatchOut)
def classify_batch(payload: ClassifyBatchIn, request: Request):
    try:
        raw_results = classify_batch_service(payload.texts)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not ready") from e

    results: List[ClassificationOut] = []
    for cid, label, p, suggestion in raw_results:
        results.append(ClassificationOut(
            classification_id=cid,
            label=label,
            score_produtivo=round(float(p), 3),
            threshold_used=THRESHOLD,
            suggestion=suggestion
        ))
    return ClassificationBatchOut(results=results)

@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
def submit_feedback(payload: FeedbackIn):
    try:
        submit_feedback_service(str(payload.classification_id), payload.helpful, payload.reason_code)
    except HTTPException:
        raise
    return None
