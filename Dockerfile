# Root Dockerfile — delegates to app/Dockerfile
# Railway auto-detects this file and uses Docker build.
# Context is the repo root so app/Dockerfile can access both librechat/ and app/.

FROM node:20-alpine AS builder

WORKDIR /app

# Copy upstream LibreChat source
COPY librechat/package*.json ./
COPY librechat/ ./

# Install dependencies
RUN npm ci

# Inject theme CSS
COPY app/styles/ /tmp/styles/
RUN if [ -f /tmp/styles/theme.css ]; then cat /tmp/styles/theme.css >> client/src/style.css; fi

# Inject logo
COPY app/public/images/ /tmp/images/
RUN if [ -f /tmp/images/logo.png ]; then cp /tmp/images/logo.png client/public/assets/logo.png 2>/dev/null || true; fi

# Patch HTML metadata
ARG APP_TITLE="My AI Assistant"
RUN sed -i "s|<title>LibreChat</title>|<title>${APP_TITLE}</title>|g" client/index.html || true
RUN sed -i "s|content=\"LibreChat\"|content=\"${APP_TITLE}\"|g" client/index.html || true

# Build frontend
RUN npm run frontend

# Production image
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app ./

EXPOSE 3080
CMD ["npm", "run", "backend"]
