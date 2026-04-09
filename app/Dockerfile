# ============================================================================
# LibreChat + Overlay Dockerfile
# ============================================================================
# Builds LibreChat from the upstream submodule with project-specific overrides:
#   - Theme CSS injection
#   - Logo replacement
#   - HTML metadata patching (title, description, PWA manifest)
#   - Optional component injection (voice FAB, etc.)
#
# Context must be the repo root (not app/) so we can access both librechat/ and app/.
# ============================================================================

FROM node:20-alpine AS builder

WORKDIR /app

# --- Copy upstream LibreChat source ---
COPY librechat/package*.json ./
COPY librechat/ ./

# --- Install dependencies ---
RUN npm ci

# --- Inject theme CSS ---
# Append project theme to LibreChat's global styles
COPY app/styles/theme.css /tmp/theme.css
RUN cat /tmp/theme.css >> client/src/style.css

# --- Inject logo ---
COPY app/public/images/ /tmp/images/
RUN if [ -f /tmp/images/logo.png ]; then \
        cp /tmp/images/logo.png client/public/assets/logo.png; \
    fi

# --- Patch HTML metadata ---
# These sed commands update branding. They target specific strings in the upstream source.
# If upstream changes these files, the build will still succeed but patches may not apply.
# Run `scripts/validate-overlay.sh` after submodule updates to verify.
ARG APP_TITLE="My AI Assistant"
RUN sed -i "s|<title>LibreChat</title>|<title>${APP_TITLE}</title>|g" client/index.html || true
RUN sed -i "s|content=\"LibreChat\"|content=\"${APP_TITLE}\"|g" client/index.html || true

# --- Optional: Inject custom components ---
# Uncomment and modify when adding custom React components (e.g., voice button):
# COPY app/components/ /tmp/components/
# RUN cp -r /tmp/components/pipecat/ client/src/components/Pipecat/ 2>/dev/null || true
# RUN if [ -d client/src/components/Pipecat ]; then \
#         sed -i '/^import.*ChatForm/a import { VoiceFAB } from "~/components/Pipecat/VoiceFAB";' \
#             client/src/components/Chat/Input/ChatForm.tsx || true; \
#     fi

# --- Build ---
RUN npm run frontend

# --- Production image ---
FROM node:20-alpine

WORKDIR /app
COPY --from=builder /app ./

EXPOSE 3080
CMD ["npm", "run", "backend"]
