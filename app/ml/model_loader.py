import os
import json
import joblib
from sentence_transformers import SentenceTransformer
from app.core.config import META_PATH, CLF_PATH, EMB_DIR

# Load META, embeddings, classifier
with open(META_PATH, "r", encoding="utf-8") as f:
    META = json.load(f)

THRESHOLD = float(os.environ.get("THRESHOLD", META["threshold_produtivo"]))
EMB_ID = META.get("embedding_model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

if os.path.isdir(EMB_DIR):
    EMB = SentenceTransformer(EMB_DIR)
else:
    EMB = SentenceTransformer(EMB_ID)

CLF = joblib.load(CLF_PATH)

# Warmup
try:
    EMB.encode(["warmup"], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
except Exception:
    pass