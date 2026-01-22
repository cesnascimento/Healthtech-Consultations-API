# ==============================================
# Healthtech Consultations API - Dockerfile
# ==============================================
# Multi-stage build otimizado para produção com uv
#
# Build:
#   docker build -t healthtech-consultations .
#
# Run:
#   docker run --env-file .env -p 8000:8000 healthtech-consultations
#
# ==============================================

FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml ./

RUN uv venv /app/.venv && \
    uv sync --frozen --no-dev --no-install-project

COPY app ./app


FROM python:3.11-slim AS runtime

LABEL maintainer="Healthtech Team <cesar@sofyaai.com>" \
      version="1.0.0" \
      description="API para processamento de consultas médicas"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/app /app/app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
