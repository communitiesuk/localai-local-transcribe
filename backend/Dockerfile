# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential=12.12 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==2.4.1 poetry-plugin-export==1.9.0
WORKDIR /app
COPY pyproject.toml README.md ./

# Install packages, strip debug symbols, and clean up pip/setuptools directly in Stage 1
RUN poetry export -f requirements.txt --output requirements.txt --with backend --without dev --without-hashes && \
    pip install --no-cache-dir --target=/app/site-packages -r requirements.txt && \
    # 1. Strip binary debug symbols from compiled extensions to save space
    find /app/site-packages -name "*.so" -exec strip --strip-unneeded {} + && \
    # 2. Purge pip, setuptools, wheels, and standard pycaches
    rm -rf /app/site-packages/pip* \
           /app/site-packages/setuptools* \
           /app/site-packages/wheel* \
    && find /app/site-packages -type d -name "__pycache__" -prune -exec rm -rf {} +

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Create necessary directories and ensure appuser ownership
RUN mkdir -p /app/config && \
    chown -R appuser:appuser /app

# Copy only the site-packages from the builder stage to the runner stage
COPY --from=builder /app/site-packages /usr/local/lib/python3.12/site-packages

# Copy only what the backend needs to run directly to /app
COPY --chown=appuser:appuser backend/ backend/
COPY --chown=appuser:appuser common/ common/
COPY --chown=appuser:appuser alembic/ alembic/
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser backend/entrypoint.sh .

# Ensure entrypoint is executable
RUN chmod +x backend/entrypoint.sh

# Set PATH so executables in site-packages/bin (like alembic, uvicorn) are found.
# site-packages now lives at the default interpreter path
# (/usr/local/lib/python3.12/site-packages), so PYTHONPATH no longer needs to
# point there - Python finds it automatically. PYTHONPATH=/app is what makes
# our own backend/common/alembic source importable.
ENV PATH="/usr/local/lib/python3.12/site-packages/bin:${PATH}" \
    PYTHONPATH=/app

USER appuser

ENTRYPOINT ["backend/entrypoint.sh"]
