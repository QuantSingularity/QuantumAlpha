# Backend Service Dockerfile for QuantumAlpha
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system deps (including curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install (cached layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . /app/

# Create non-root user (avoid colliding with common UIDs)
RUN useradd -m -u 1001 appuser || usermod -u 1001 appuser || true && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Use curl for healthcheck (works regardless of what the app process is)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command: run your app file directly (avoid python -c)
# If you use a WSGI server (gunicorn/uvicorn) replace this with the appropriate command.
CMD ["python", "app.py"]