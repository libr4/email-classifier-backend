import os

# Env/config
ARTS_DIR = os.environ.get("MODEL_DIR", "model_artifacts")
META_PATH = os.path.join(ARTS_DIR, "metadata.json")
CLF_PATH  = os.path.join(ARTS_DIR, "clf_cal.joblib")
EMB_DIR   = os.path.join(ARTS_DIR, "embedder")

ORIGINS = os.getenv("CORS_ORIGINS", "*")
# ORIGINS = [o.strip() for o in origins_env.split(",") if o.strip()]
DATABASE_URL = os.environ.get("DATABASE_URL")  # e.g., postgresql+psycopg://user:pass@host:5432/db

TELEMETRY_ON = os.environ.get("TELEMETRY", "on").lower() in ("1", "true", "on", "yes")
MAX_TEXT_CHARS = int(os.environ.get("MAX_TEXT_CHARS", "20000"))
MAX_BATCH_ITEMS = int(os.environ.get("MAX_BATCH_ITEMS", "200"))
LANG_SET = {"pt", "en", "unknown"}
