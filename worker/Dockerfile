FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS base

# ==========================================
# Stage 1: Builder
# ==========================================
FROM base AS builder

ARG BUILD_ESSENTIAL_VERSION=12.12

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build tools only if needed for compiled deps
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

RUN poetry export \
      -f requirements.txt \
      --output requirements.txt \
      --with worker \
      --without dev \
      --without-hashes

RUN python -m pip install --no-cache-dir --ignore-installed \
      --prefix=/install \
      -r requirements.txt

# -------------------------------------------------------------
# Clean unnecessary files directly in Stage 1 to keep Stage 2 light
# -------------------------------------------------------------
# 1. Strip debug symbols from compiled Python extensions (.so files)
RUN cd /install/lib/python*/site-packages && \
    find . -name "*.so" -exec strip --strip-unneeded {} + && \
# 2. Delete pip, setuptools, and wheel
    rm -rf pip* setuptools* wheel* && \
# 3. Clean up pycaches and test directories
    find . -type d -name "__pycache__" -prune -exec rm -rf {} + && \
    find . -type d -name "tests" -prune -exec rm -rf {} + && \
# 4. Remove Ray's Java runtime. This worker only creates Python actors; removing the jars prevents unnecessary vuln detections
    rm -rf ray/jars

# ==========================================
# Stage 2: Runner
# ==========================================
FROM base AS runner

ARG FFMPEG_VERSION=7:7.1.5-0+deb13u1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Set PYTHONPATH to /app so python naturally finds common, worker, and backend
    PYTHONPATH=/app

# Use Debian ffmpeg for now (caf-friendly version)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg=${FFMPEG_VERSION} && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# Create /tmp directory mapped to appuser
RUN mkdir -p /tmp && \
    chown -R appuser:appuser /tmp && \
    chmod 1777 /tmp

VOLUME [ "/tmp" ]

WORKDIR /app

# Create writable directories
# (no /app/logs - logs go to CloudWatch, nothing writes locally, same as backend)
RUN mkdir -p /app/config && \
    chown -R appuser:appuser /app

ADD --chown=appuser:appuser --chmod=0444 \
    https://truststore.pki.rds.amazonaws.com/eu-west-2/eu-west-2-bundle.pem \
    /app/config/rds-ca-bundle.pem

# Copy built packages and scripts from builder (already pre-cleaned & stripped)
COPY --from=builder /install/ /usr/local/

# Copy runtime code cleanly directly to /app (No duplication in site-packages)
COPY --chown=appuser:appuser common/ common/
COPY --chown=appuser:appuser worker/ worker/
COPY --chown=appuser:appuser backend/__init__.py backend/__init__.py
COPY --chown=appuser:appuser worker/entrypoint.sh ./entrypoint.sh

# Ensure entrypoint is executable
RUN chmod +x /app/worker/entrypoint.sh

USER appuser

ENTRYPOINT ["worker/entrypoint.sh"]
