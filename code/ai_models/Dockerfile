FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY ai_models/requirements.txt ai_models/requirements-ml.txt ./ai_models/
ARG INSTALL_ML=true
RUN if [ "$INSTALL_ML" = "true" ]; then pip install --no-cache-dir --prefix=/install -r ai_models/requirements-ml.txt; else pip install --no-cache-dir --prefix=/install -r ai_models/requirements.txt; fi

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/* \
    && groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser -s /sbin/nologin -d /app appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser ai_models ./ai_models
RUN mkdir -p /app/models && chown -R appuser:appuser /app/models
ENV PYTHONUNBUFFERED=1 AI_MODEL_DIR=/app/models PORT=8080
USER 1000:1000
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD curl -fs http://localhost:8080/health || exit 1
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 300 ai_models.api.wsgi:app"]
