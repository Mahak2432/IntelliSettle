# API container for Cloud Run. Build context is the repo root so the seed data can be included.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    SEED_DIR=/app/data/seed \
    PORT=8080

WORKDIR /app/api
COPY api/pyproject.toml api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY api/src ./src
RUN uv sync --frozen --no-dev

COPY data/seed /app/data/seed

CMD ["sh", "-c", "exec /app/api/.venv/bin/uvicorn claims_api.main:app --host 0.0.0.0 --port ${PORT}"]
