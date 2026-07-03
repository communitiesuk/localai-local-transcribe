# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build tools only if needed for compiled deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential=12.12 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==2.4.1 poetry-plugin-export==1.9.0

COPY pyproject.toml poetry.lock README.md ./

RUN poetry export \
      -f requirements.txt \
      --output requirements.txt \
      --with worker \
      --without dev \
      --without-hashes

RUN pip install --no-cache-dir \
      --target=/opt/site-packages \
      -r requirements.txt

# -------------------------------------------------------------
# Clean unnecessary files directly in Stage 1 to keep Stage 2 light
# -------------------------------------------------------------
# 1. Strip debug symbols from compiled Python extensions (.so files)
RUN find /opt/site-packages -name "*.so" -exec strip --strip-unneeded {} + && \
# 2. Delete pip, setuptools, and wheel
    rm -rf /opt/site-packages/pip* \
           /opt/site-packages/setuptools* \
           /opt/site-packages/wheel* \
# 3. Clean up pycaches and test directories
    && find /opt/site-packages -type d -name "__pycache__" -prune -exec rm -rf {} + \
    && find /opt/site-packages -type d -name "tests" -prune -exec rm -rf {} +

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Set PYTHONPATH to /app so python naturally finds common, worker, and backend
    PYTHONPATH=/app

# Use Debian ffmpeg for now (caf-friendly version)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg=7:7.1.3-0+deb13u1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Create writable directories
RUN mkdir -p /app/config /app/logs && \
    chown -R appuser:appuser /app

# Copy built site-packages from builder (already pre-cleaned & stripped)
COPY --from=builder /opt/site-packages /usr/local/lib/python3.12/site-packages

# Copy runtime code cleanly directly to /app (No duplication in site-packages)
COPY --chown=appuser:appuser common/ common/
COPY --chown=appuser:appuser worker/ worker/
COPY --chown=appuser:appuser backend/__init__.py backend/__init__.py
COPY --chown=appuser:appuser worker/entrypoint.sh ./entrypoint.sh

# Ensure entrypoint is executable
RUN chmod +x /app/worker/entrypoint.sh

USER appuser

ENTRYPOINT ["worker/entrypoint.sh"]