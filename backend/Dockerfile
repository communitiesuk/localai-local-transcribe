FROM python:3.14-slim@sha256:22eafb370920ad8b429e0aec3fff433e0669968519f5d60469d83729c138b28b AS base

# ==========================================
# Stage 1: Builder
# ==========================================
FROM base AS builder

ARG BUILD_ESSENTIAL_VERSION=12.12

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential=${BUILD_ESSENTIAL_VERSION} && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml poetry.lock README.md ./
COPY scripts/get-poetry-version.py scripts/get-poetry-version.py
RUN POETRY_VERSION=$(python scripts/get-poetry-version.py) && \
    pip install --no-cache-dir "poetry==${POETRY_VERSION}" poetry-plugin-export==1.9.0

COPY scripts/check-python-version.py scripts/check-python-version.py
RUN python scripts/check-python-version.py

# Install packages, strip debug symbols, and clean up pip/setuptools directly in Stage 1
RUN poetry export -f requirements.txt --output requirements.txt --with backend --without dev --without-hashes && \
    python -m pip install --no-cache-dir --ignore-installed --prefix=/install -r requirements.txt && \
    cd /install/lib/python*/site-packages && \
    # 1. Strip binary debug symbols from compiled extensions to save space
    find . -name "*.so" -exec strip --strip-unneeded {} + && \
    # 2. Purge pip, setuptools, wheels, and standard pycaches
    rm -rf pip* setuptools* wheel* && \
    find . -type d -name "__pycache__" -prune -exec rm -rf {} +

# ==========================================
# Stage 2: Runner
# ==========================================
FROM base AS runner

ARG CURL_VERSION=8.14.1-2+deb13u7

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl=${CURL_VERSION} && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Create necessary directories and ensure appuser ownership
RUN mkdir -p /app/config && \
    chown -R appuser:appuser /app

ADD --chown=appuser:appuser --chmod=0444 \
    https://truststore.pki.rds.amazonaws.com/eu-west-2/eu-west-2-bundle.pem \
    /app/config/rds-ca-bundle.pem

# Copy the installed packages and scripts from the builder stage to the runner stage
COPY --from=builder /install/ /usr/local/

# Copy only what the backend needs to run directly to /app
COPY --chown=appuser:appuser backend/ backend/
COPY --chown=appuser:appuser common/ common/
COPY --chown=appuser:appuser alembic/ alembic/
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser backend/entrypoint.sh .

# Ensure entrypoint is executable
RUN chmod +x backend/entrypoint.sh

# PYTHONPATH=/app is what makes our own backend/common/alembic source importable.
ENV PYTHONPATH=/app

USER appuser

ENTRYPOINT ["backend/entrypoint.sh"]
