# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential=12.12 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==2.3.3 poetry-plugin-export==1.9.0
WORKDIR /app
COPY pyproject.toml poetry.lock README.md ./

# Install into a "pure" directory
RUN poetry export -f requirements.txt --output requirements.txt --with backend --without dev --without-hashes && \
    pip install --no-cache-dir --target=/app/site-packages -r requirements.txt

COPY backend/ backendmbmbnb/
COPY common/ common/
COPY alembic/ alembic/
COPY alembic.ini .

COPY --chown=appuser:appuser backend/ /app/site-packages/backend/
COPY --chown=appuser:appuser common/ /app/site-packages/common/
COPY --chown=appuser:appuser alembic/ /app/site-packages/alembic/

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create user
RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Create necessary directories and ensure appuser ownership
RUN mkdir -p /app/config /app/site-packages && \
    chown -R appuser:appuser /app

# Copy ONLY the site-packages (This folder contains 0 build tools, 0 pip, 0 poetry)
COPY --from=builder /app/site-packages /usr/local/lib/python3.12/site-packages

# Copy code
# 2. Copy ONLY what the backend needs to run
# This excludes 'worker/' and 'frontend/' and '.venv' and logs
COPY --chown=appuser:appuser backend/ backend/
COPY --chown=appuser:appuser common/ common/
COPY --chown=appuser:appuser alembic/ alembic/
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser backend/entrypoint.sh .

# Set PATH so executables in site-packages/bin (like alembic, uvicorn) are found
ENV PATH="/usr/local/lib/python3.12/site-packages/bin:${PATH}"



# Set PYTHONPATH so Python knows to look in /usr/local/lib/python3.12/site-packages
# (Python does this by default, so this is just for safety)
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages

# Make it executable as root
RUN chmod +x backend/entrypoint.sh
# Switch to user
USER appuser

ENTRYPOINT ["backend/entrypoint.sh"]