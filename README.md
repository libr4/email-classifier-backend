# AutoU Email Classifier API

A FastAPI-based microservice that classifies incoming email-like text as **Produtivo** or **Improdutivo**, returns a confidence score, and (optionally) logs telemetry to PostgreSQL via SQLAlchemy + Alembic.

---

## ✨ Features
- `/classify` single-text inference with suggestion text (PT).
- `/classify_batch` batch inference.
- `/feedback` endpoint to record end-user feedback (optional DB).
- Health probe at `/healthz` for load balancers.
- Pluggable threshold via `metadata.json` and/or `THRESHOLD` env.
- Dockerized; supports local dev with Compose and production on AWS ECS/Fargate.
- Model artifacts **not** tracked in Git (keeps the repo lean).

---

## 🗂️ Project Layout (backend only)
```
app/
  core/
    config.py
  db/
    models.py
    session.py
    migrations/
      alembic.ini
      env.py
      versions/
        0001_init_telemetry.py
  ml/
    inference.py
    model_loader.py
  repositories/
    telemetry_repo.py
  services/
    classify_service.py
  utils/
    suggest.py
    lang.py
  main.py
entrypoint.sh
requirements.txt
docker-compose.yml
Dockerfile
```

---

## 🔐 Environment Variables

| Name | Required | Default | Description |
|---|---|---:|---|
| `PORT` | no | `8000` | App port (Uvicorn) |
| `MODEL_DIR` | no | `model_artifacts` | Folder with `metadata.json`, `clf_cal.joblib`, and `embedder/` |
| `THRESHOLD` | no | from `metadata.json` | Decision threshold override |
| `TELEMETRY` | no | `off` | `on` enables DB telemetry + Alembic on startup |
| `DATABASE_URL` | if `TELEMETRY=on` | — | SQLAlchemy URL, e.g. `postgresql+psycopg://user:pass@host:5432/db` |
| `CORS_ORIGINS` | recommended | — | Comma-separated list of allowed origins (e.g. `https://your-frontend`) |
| `MAX_TEXT_CHARS` | no | `20000` | Input size guard |
| `MAX_BATCH_ITEMS` | no | `200` | Batch size guard |

> **Note**: In production (ECS) migrations run only when both `TELEMETRY=on` and a non-empty `DATABASE_URL` are present. For stateless runs, leave `TELEMETRY=off`.

---

## 📦 Model Artifacts (download step)

This repo doesn’t ship large weights. Before running locally, download and unpack the model bundle at the repo root:

```bash
python3 -m pip install -U gdown && \
gdown 1TTEgxeyZgg91h59oKIlR7ESLBiow9tam -O model_artifacts.zip && \
mkdir -p model_artifacts && \
unzip -o model_artifacts.zip -d model_artifacts
```

After this, you should have:
```
model_artifacts/
  metadata.json
  clf_cal.joblib
  embedder/
    config.json
    model.safetensors
    ...
```

> If you prefer a tarball: `tar -xzf model_artifacts.tgz -C model_artifacts`.

---

## 🐳 Run with Docker Compose (API + Postgres)
> Only enable DB telemetry if you actually want to store classification/feedback rows.

1) Ensure you have `model_artifacts/` locally (see download step).
2) In `.env` (example):
```
PORT=8000
TELEMETRY=off
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
# If enabling telemetry:
# TELEMETRY=on
# DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/autou
```
3) Start:
```bash
docker compose up --build
```

- API: `http://localhost:8000/healthz`
- If `TELEMETRY=on`, the container waits for DB and runs Alembic `upgrade head` on boot.

---

---

## ▶️ Run Locally (no DB)
```bash
# 1) Create and activate a venv (optional)
python3 -m venv .venv && source .venv/bin/activate

# 2) Copy the example into a .env (optional)
cp env.example .env

# 3) Install deps
python -m pip install -U pip
pip install -r requirements.txt

# 4) Download model artifacts (see step above)

# 5) Start the API
export PORT=8000
export TELEMETRY=off
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Open: `http://localhost:8000/healthz`

## 📡 Endpoints

### `GET /healthz`
Returns basic runtime info:
```json
{
  "status": "ok",
  "model_version": "2025-09-27 20:13:24",
  "embedding_model": "distiluse-base-multilingual-cased-v2",
  "threshold": 0.65,
  "telemetry": "off|ready|not_ready"
}
```

### `POST /classify`
**Request**
```json
{ "text": "Pode liberar meu acesso ao ERP?" }
```
Validation:
- non-empty, trimmed text
- `MAX_TEXT_CHARS` guard
- control characters rejected

**Response**
```json
{
  "classification_id": "UUID",
  "label": "Produtivo | Improdutivo",
  "score_produtivo": 0.736,
  "threshold_used": 0.65,
  "suggestion": "Obrigado pelo pedido de acesso/desbloqueio. Vamos validar a autorização e retornaremos com a liberação."
}
```

### `POST /classify_batch`
**Request**
```json
{
  "texts": ["resetar minha senha", "segue anexo o contrato", "..."]
}
```
**Response**
```json
{ "results": [ { "classification_id": "...", "label": "...", "score_produtivo": 0.88, "threshold_used": 0.65, "suggestion": "..." } ] }
```

### `POST /feedback`
**Request**
```json
{
  "classification_id": "UUID",
  "helpful": true,
  "reason_code": "WRONG_INTENT | TONE | MISSING_INFO | LOW_CONF | OTHER | null"
}
```
**Response**: `204 No Content`  
Errors: `404` if `classification_id` not found (only when telemetry is on and DB migrated).

---

## 🧠 How It Works
- Sentences are embedded via `SentenceTransformer` loaded from `MODEL_DIR`.
- A calibrated scikit-learn classifier produces `score_produtivo ∈ [0,1]`.
- The label is `Produtivo` if `score ≥ threshold` else `Improdutivo`.
- Threshold comes from `metadata.json` unless overridden via `THRESHOLD` env.
- Optional telemetry writes to `classification` and `feedback` tables; Alembic boots them on first run when enabled.

---

## 🚀 Deploying (high level)
- **ECS Fargate + ALB** (HTTP) works out of the box.
- For browsers on HTTPS frontends, put **CloudFront** in front of the ALB (gives HTTPS `*.cloudfront.net`) or attach an ACM cert + HTTPS listener to ALB.
- Set `CORS_ORIGINS` to your frontend origin(s), e.g. `https://yourapp.vercel.app`.
- Bake `model_artifacts/` into the image for ECS (`COPY model_artifacts ./model_artifacts`).

---

## 🧪 cURL Examples
```bash
# health
curl -s http://localhost:8000/healthz | jq

# classify
curl -s -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"text":"Pode liberar meu acesso ao ERP?"}' | jq

# batch
curl -s -X POST http://localhost:8000/classify_batch \
  -H "Content-Type: application/json" \
  -d '{"texts":["resetar minha senha","segue anexo o contrato"]}' | jq

# feedback (when telemetry enabled)
curl -s -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"classification_id":"<UUID>","helpful":true,"reason_code":"LOW_CONF"}' -i
```

---

## 🛠️ Troubleshooting
- **HTTP 5xx on boot**: confirm `model_artifacts/` exists with the expected files.
- **ALB health check flapping**: ensure `/healthz` is reachable, model is present, and container listens on `$PORT`.
- **CORS blocked**: set `CORS_ORIGINS` to the **exact** frontend origin (including scheme), comma-separated.
- **Huge repo push fails**: artifacts aren’t in Git by design. Use the download step above.
- **Alembic errors on ECS**: leave `TELEMETRY=off` if you don’t have a database yet.

---

## 📄 License
MIT — do your thing. Please keep the attributions in the source where present.
