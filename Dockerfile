# ==============================================
# Healthtech Consultations API - Dockerfile
# ==============================================
# Multi-stage build otimizado para produção com uv
#
# Build:
#   docker build -t healthtech-consultations .
#
# Run:
#   docker run -p 8000:8000 healthtech-consultations
#
# Com LLM:
#   docker build --build-arg INSTALL_LLM=true -t healthtech-consultations .
# ==============================================

# ----------------------------------------------
# Stage 1: Builder
# ----------------------------------------------
FROM python:3.11-slim AS builder

# Argumentos de build
ARG INSTALL_LLM=false

# Instala uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Configura uv para não usar cache externo
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Copia arquivos de dependência primeiro (cache layer)
COPY pyproject.toml ./

# Cria venv e instala dependências
RUN uv venv /app/.venv

# Instala dependências base
RUN uv sync --frozen --no-dev --no-install-project

# Instala dependências LLM se solicitado
RUN if [ "$INSTALL_LLM" = "true" ]; then \
        uv sync --frozen --no-dev --no-install-project --extra llm; \
    fi

# Copia código fonte
COPY app ./app

# ----------------------------------------------
# Stage 2: Runtime
# ----------------------------------------------
FROM python:3.11-slim AS runtime

# Labels
LABEL maintainer="Healthtech Team <cesar@sofyaai.com>" \
      version="1.0.0" \
      description="API para processamento de consultas médicas"

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    # Configurações da aplicação
    APP_NAME="Healthtech Consultations API" \
    APP_VERSION="1.0.0" \
    SUMMARIZER_STRATEGY="rule_based"

# Cria usuário não-root para segurança
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copia venv e código do builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/app /app/app

# Troca para usuário não-root
USER appuser

# Expõe porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando de execução
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
