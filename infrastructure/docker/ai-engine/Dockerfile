# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r -g 1000 appuser \
    && useradd -r -u 1000 -g appuser -s /sbin/nologin -d /app appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser . .

RUN mkdir -p /tmp /var/log/quantumalpha /app/models \
    && chown -R appuser:appuser /tmp /var/log/quantumalpha /app/models

USER 1000:1000

EXPOSE 8080 9090

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
