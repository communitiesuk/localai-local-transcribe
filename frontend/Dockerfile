# ==========================================
# Stage 1: Build
# ==========================================
FROM node:24-alpine AS builder
WORKDIR /app

# Copy dependency configs first
COPY frontend/package.json frontend/package-lock.json ./

# Use a BuildKit cache mount to accelerate iterative runs
RUN --mount=type=cache,target=/root/.npm npm ci

# Copy the application source code
COPY frontend .

# Build-time environment variables (placed right before build to protect dependency layer cache)
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_POSTHOG_API_KEY
ARG SENTRY_AUTH_TOKEN
ENV NEXT_PUBLIC_SENTRY_DSN=$NEXT_PUBLIC_SENTRY_DSN \
    NEXT_PUBLIC_POSTHOG_API_KEY=$NEXT_PUBLIC_POSTHOG_API_KEY \
    SENTRY_AUTH_TOKEN=$SENTRY_AUTH_TOKEN

# Compile the application
RUN npm run build && \
    # Clean up sourcemaps after Sentry has uploaded them to keep the production image secure & lightweight
    find .next -name "*.map" -delete

# ==========================================
# Stage 2: Runner (Production)
# ==========================================
FROM node:24-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    PORT=8081 \
    HOSTNAME="0.0.0.0"

# Security: Set up non-root boundaries
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy essential production artifacts with consistent non-root ownership
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Prune default global tooling we don't need at runtime
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