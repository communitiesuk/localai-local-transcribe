# ==========================================
# Stage 1: Build
# ==========================================
FROM node:26-alpine@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5 AS builder
WORKDIR /app

# Copy dependency configs first
COPY frontend/package.json frontend/package-lock.json ./

# Use a BuildKit cache mount to accelerate iterative runs
RUN --mount=type=cache,target=/root/.npm npm ci

# Copy the application source code
COPY frontend .

# Generate client code before declaring build-time ARGs (preserves layer cache)
RUN npm run generate-client

# Build-time environment variables
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_ENVIRONMENT
ARG NEXT_PUBLIC_PLAUSIBLE_DOMAIN
ARG SENTRY_SECURITY_REPORT_URI
ARG CSP_STORAGE_ORIGIN

# Only export variables required by Next.js client bundle
ENV NEXT_PUBLIC_SENTRY_DSN=$NEXT_PUBLIC_SENTRY_DSN \
    NEXT_PUBLIC_PLAUSIBLE_DOMAIN=$NEXT_PUBLIC_PLAUSIBLE_DOMAIN \
    NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT \
    SENTRY_SECURITY_REPORT_URI=$SENTRY_SECURITY_REPORT_URI \
    CSP_STORAGE_ORIGIN=$CSP_STORAGE_ORIGIN

# SENTRY_AUTH_TOKEN is mounted as a secret during build
RUN --mount=type=secret,id=sentry_auth_token \
    SENTRY_AUTH_TOKEN=$(cat /run/secrets/sentry_auth_token) npm run build && \
    find .next -name "*.map" -delete

# ==========================================
# Stage 2: Runner (Production)
# ==========================================
FROM node:26-alpine@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5 AS runner
WORKDIR /app

ENV NODE_ENV=production \
    PORT=8081 \
    HOSTNAME="0.0.0.0"

# Security: Set up non-root boundaries
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs nextjs

# Copy essential production artifacts with consistent non-root ownership
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Prune default global tooling not needed at runtime
RUN rm -rf /usr/local/lib/node_modules/npm \
    /usr/local/lib/node_modules/corepack \
    /usr/local/bin/npm \
    /usr/local/bin/npx \
    /usr/local/bin/corepack \
    /opt/yarn* \
    /usr/local/bin/yarn* \
    /usr/local/share/man/man1/npm*

USER nextjs

EXPOSE 8081

CMD ["node", "server.js"]