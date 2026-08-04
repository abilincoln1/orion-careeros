FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Build context is the repository root (see docker-compose.yml) so the
# ORION Platform Kernel is available to install as a local editable
# dependency, per the ORION Platform architecture (platform/ + products/).
COPY platform/kernel /app/platform/kernel
COPY products/careeros/backend/requirements.txt /app/products/careeros/backend/requirements.txt

WORKDIR /app/products/careeros/backend
RUN pip install --no-cache-dir -r requirements.txt

COPY products/careeros/backend /app/products/careeros/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
