FROM python:3.12-slim
WORKDIR /app

# --- add libpq runtime so psycopg can always load ---
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# speed up pip
RUN --mount=type=cache,target=/root/.cache/pip python -m pip install --upgrade pip

COPY requirements.txt .

# CPU-only torch first (no CUDA)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.8.0

# install deps (with psycopg[binary] pinned in requirements.txt)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

COPY . .
RUN chmod +x /app/entrypoint.sh

ENV TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
