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
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry --version
COPY pyproject.toml poetry.lock README.md ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --with backend --without dev --no-interaction --no-ansi --no-root
COPY . .
RUN /app/.venv/bin/pip install --no-cache-dir --no-deps .

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create the user first
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Copy the venv from builder and fix ownership
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy your source code (Only need this ONCE)
COPY --chown=appuser:appuser . .

# Set path and permissions
ENV PATH="/app/.venv/bin:$PATH"
RUN chmod +x backend/entrypoint.sh

# Finally switch to the user
USER appuser

EXPOSE 8080
ENTRYPOINT ["backend/entrypoint.sh"]