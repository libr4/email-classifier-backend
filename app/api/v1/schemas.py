from typing import List, Optional, Literal
from pydantic import BaseModel, Field, UUID4, field_validator
from app.core.config import MAX_TEXT_CHARS, MAX_BATCH_ITEMS

class ClassifyIn(BaseModel):
    text: str = Field(..., description="Email text in PT or EN.")

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, v: str):
        if v is None:
            raise ValueError("text is required")
        txt = str(v).strip()
        if len(txt) == 0:
            raise ValueError("text cannot be empty")
        if len(txt) > MAX_TEXT_CHARS:
            raise ValueError(f"text too long (>{MAX_TEXT_CHARS} chars)")
        # allow \n\t; block other control chars
        nonprintables = sum(1 for ch in txt if ord(ch) < 9 or (13 < ord(ch) < 32))
        if nonprintables > 0:
            raise ValueError("text contains invalid control characters")
        return txt

class ClassifyBatchIn(BaseModel):
    texts: List[str] = Field(
        ...,
        description="Batch of email texts.",
        min_items=1,
        max_items=MAX_BATCH_ITEMS,
    )

    @field_validator("texts", mode="before")
    @classmethod
    def validate_each(cls, arr):
        if arr is None:
            raise ValueError("texts is required")
        try:
            items = list(arr)
        except TypeError:
            raise ValueError("texts must be a list of strings")
        cleaned: List[str] = []
        for i, t in enumerate(items):
            if t is None:
                raise ValueError(f"texts[{i}] is null")
            s = str(t).strip()
            if len(s) == 0:
                raise ValueError(f"texts[{i}] is empty")
            if len(s) > MAX_TEXT_CHARS:
                raise ValueError(f"texts[{i}] too long (>{MAX_TEXT_CHARS} chars)")
            cleaned.append(s)
        return cleaned

class ClassificationOut(BaseModel):
    classification_id: UUID4
    label: Literal["Produtivo", "Improdutivo"]
    score_produtivo: float
    threshold_used: float
    suggestion: Optional[str] = None

class ClassificationBatchOut(BaseModel):
    results: List[ClassificationOut]

class FeedbackIn(BaseModel):
    classification_id: UUID4
    helpful: bool
    reason_code: Optional[Literal["WRONG_INTENT", "TONE", "MISSING_INFO", "LOW_CONF", "OTHER"]] = None
