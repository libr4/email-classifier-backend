from typing import List, Literal
import numpy as np
from app.ml.model_loader import EMB, CLF, THRESHOLD

def infer_labels(texts: List[str]) -> np.ndarray:
    X = EMB.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    p = CLF.predict_proba(X)[:, 1]
    return p

def decide_label(p: float, threshold: float = THRESHOLD) -> Literal["Produtivo","Improdutivo"]:
    return "Produtivo" if p >= threshold else "Improdutivo"
