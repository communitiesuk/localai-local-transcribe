# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1



# Install Poetry and ensure it's in the PATH
RUN pip install --no-cache-dir poetry==2.3.3
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Tell Poetry to create the virtualenv inside the project directory (/app/.venv)
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Copy dependency files first
COPY pyproject.toml poetry.lock README.md ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --with worker --without dev --no-interaction --no-ansi --no-root

# Copy application code
COPY common common
COPY backend/__init__.py backend/__init__.py
COPY worker worker

# Install again to include the root project
RUN /app/.venv/bin/pip install --no-cache-dir --no-deps .

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.12-slim

ENV RAY_ROTATION_MAX_BYTES=10485760
ENV RAY_ROTATION_BACKUP_COUNT=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Pinned to 7:7.1.3-0+deb13u1 for Debian 13 (Trixie)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg=7:7.1.3-0+deb13u1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Copy the fully built virtual environment from the builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Put the virtual environment on the path
ENV PATH="/app/.venv/bin:$PATH"

# Copy specific directories instead of '.' to avoid overwriting permissions and bloat
COPY --chown=appuser:appuser common common
COPY --chown=appuser:appuser worker worker

RUN chmod +x worker/entrypoint.sh
USER appuser


CMD ["worker/entrypoint.sh"]