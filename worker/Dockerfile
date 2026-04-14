# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build tools only if needed for compiled deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==2.3.3 poetry-plugin-export

COPY pyproject.toml poetry.lock README.md ./


RUN poetry export \
      -f requirements.txt \
      --output requirements.txt \
      --with worker \
      --with local-dev \
      --without dev \
      --without-hashes

RUN pip install --no-cache-dir \
      --target=/opt/site-packages \
      -r requirements.txt
COPY common/ common/
COPY worker/ worker/
COPY backend/__init__.py backend/__init__.py

# Add code to site-packages so imports work cleanly
RUN cp -a common /opt/site-packages/common && \
    cp -a worker /opt/site-packages/worker && \
    cp -a backend /opt/site-packages/backend

# Clean unnecessary files to reduce size (safe version)
RUN find /opt/site-packages -type d -name "__pycache__" -prune -exec rm -rf {} + && \
    find /opt/site-packages -type d -name "tests" -prune -exec rm -rf {} +

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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
RUN mkdir -p /app/config /app/logs /app/.whisply_temp && \
    chown -R appuser:appuser /app

# Copy built site-packages from builder
COPY --from=builder /opt/site-packages /usr/local/lib/python3.12/site-packages

# Copy runtime code (assets, scripts, etc.)
COPY --chown=appuser:appuser common/ common/
COPY --chown=appuser:appuser worker/ worker/
COPY --chown=appuser:appuser worker/entrypoint.sh ./entrypoint.sh

# Ensure entrypoint is executable
RUN chmod +x /app/worker/entrypoint.sh

USER appuser

ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages

ENTRYPOINT ["worker/entrypoint.sh"]
