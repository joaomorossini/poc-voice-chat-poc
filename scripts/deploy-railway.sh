#!/usr/bin/env bash
# ============================================================================
# Deploy to Railway — Fully Automated
# ============================================================================
# Deploys a new PoC as a service within an existing Railway project.
# Designed to be called by an AI agent (Archie) or a human operator.
#
# Model: All PoCs live as services in a single Railway project ("arden-archie").
# Shared variables (FUELIX_API_KEY, etc.) are set once in the Railway dashboard.
# Per-PoC secrets are auto-generated and set as service-level variables.
# Code is uploaded directly via `railway up` (no GitHub↔Railway integration needed).
#
# Prerequisites:
#   - gh (GitHub CLI, authenticated)
#   - railway (Railway CLI, logged in via `railway login`)
#   - railway linked to target project from the template dir (`railway link`)
#   - yq (YAML processor)
#
# Usage:
#   ./scripts/deploy-railway.sh \
#     --name "Customer Service Bot" \
#     --slug "cs-bot-acme" \
#     [--description "PoC for ACME Corp customer service"] \
#     [--features "rag,memory,web_search"] \
#     [--no-features "voice,code_interpreter"] \
#     [--primary-model "claude-sonnet-4-6"] \
#     [--prompt-file "/path/to/custom-prompt.md"]
#
# Output (last line): The deployed URL
# ============================================================================

set -euo pipefail

# --- Defaults ---
TEMPLATE_REPO="${TEMPLATE_REPO:-joaomorossini/template-fullstack-chat-agent}"
WORK_DIR="${WORK_DIR:-/tmp/poc-deploys}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[deploy]${NC} $1" >&2; }
warn() { echo -e "${YELLOW}[deploy]${NC} $1" >&2; }
err()  { echo -e "${RED}[deploy]${NC} $1" >&2; exit 1; }
step() { echo -e "${BLUE}[$(( ++STEP_NUM ))/8]${NC} $1" >&2; }

STEP_NUM=0

# --- Parse arguments ---
NAME=""
SLUG=""
DESCRIPTION=""
ENABLE_FEATURES=""
DISABLE_FEATURES=""
PRIMARY_MODEL=""
PROMPT_FILE=""
GITHUB_ORG="${GITHUB_ORG:-joaomorossini}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --name)          NAME="$2"; shift 2 ;;
        --slug)          SLUG="$2"; shift 2 ;;
        --description)   DESCRIPTION="$2"; shift 2 ;;
        --template-repo) TEMPLATE_REPO="$2"; shift 2 ;;
        --features)      ENABLE_FEATURES="$2"; shift 2 ;;
        --no-features)   DISABLE_FEATURES="$2"; shift 2 ;;
        --primary-model) PRIMARY_MODEL="$2"; shift 2 ;;
        --prompt-file)   PROMPT_FILE="$2"; shift 2 ;;
        --github-org)    GITHUB_ORG="$2"; shift 2 ;;
        *) err "Unknown argument: $1" ;;
    esac
done

[[ -z "$NAME" ]] && err "--name is required"
[[ -z "$SLUG" ]] && SLUG=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')

# --- Preflight checks ---
command -v gh &>/dev/null       || err "gh (GitHub CLI) not installed"
command -v railway &>/dev/null  || err "railway (Railway CLI) not installed"
command -v yq &>/dev/null       || err "yq not installed"
command -v openssl &>/dev/null  || err "openssl not installed"

gh auth status &>/dev/null      || err "gh not authenticated — run 'gh auth login'"
railway whoami &>/dev/null      || err "Railway not authenticated — run 'railway login'"

# --- Resolve Railway project context ---
# Railway CLI is CWD-scoped. We run CWD-dependent commands from the template dir.
# `railway up` is the exception — it accepts -p/-s/-e flags and works from anywhere.
rw() { (cd "$TEMPLATE_DIR" && railway "$@"); }

# Verify the template directory is linked to a Railway project
if ! rw status &>/dev/null; then
    err "Template directory not linked to Railway — run 'cd $TEMPLATE_DIR && railway link'"
fi

# Read project and environment IDs for railway up (the only CWD-independent command)
RAILWAY_CONFIG="$HOME/.railway/config.json"
PROJECT_ID=$(python3 -c "
import json
cfg = json.load(open('$RAILWAY_CONFIG'))
proj = cfg['projects'].get('$TEMPLATE_DIR', {})
print(proj.get('project', ''))
" 2>/dev/null)
ENV_ID=$(python3 -c "
import json
cfg = json.load(open('$RAILWAY_CONFIG'))
proj = cfg['projects'].get('$TEMPLATE_DIR', {})
print(proj.get('environment', ''))
" 2>/dev/null)

[[ -z "$PROJECT_ID" ]] && err "Could not read Railway project ID from config"
[[ -z "$ENV_ID" ]]     && err "Could not read Railway environment ID from config"

log "Deploying '${NAME}' (${SLUG}) to Railway project ${PROJECT_ID:0:8}..."

# ============================================================================
# Step 1: Create GitHub repo from template
# ============================================================================
step "Creating GitHub repo..."

REPO_FULL="${GITHUB_ORG}/${SLUG}"

if gh repo view "$REPO_FULL" &>/dev/null; then
    warn "Repo $REPO_FULL already exists — using existing"
else
    gh repo create "$REPO_FULL" \
        --template "$TEMPLATE_REPO" \
        --private \
        --description "${DESCRIPTION:-PoC: $NAME}"
    log "Repo created: https://github.com/$REPO_FULL"
fi

# ============================================================================
# Step 2: Clone and customize
# ============================================================================
step "Cloning and customizing..."

mkdir -p "$WORK_DIR"
REPO_DIR="$WORK_DIR/$SLUG"
[[ -d "$REPO_DIR" ]] && rm -rf "$REPO_DIR"

sleep 3  # GitHub template population delay

gh repo clone "$REPO_FULL" "$REPO_DIR"
cd "$REPO_DIR"
git submodule update --init --recursive 2>/dev/null || warn "Submodules not resolved locally (OK — not needed for deploy)"

# Customize project.yaml
yq -i ".project.name = \"$NAME\"" project.yaml
yq -i ".project.slug = \"$SLUG\"" project.yaml
[[ -n "$DESCRIPTION" ]] && yq -i ".project.description = \"$DESCRIPTION\"" project.yaml

if [[ -n "$ENABLE_FEATURES" ]]; then
    IFS=',' read -ra feats <<< "$ENABLE_FEATURES"
    for feat in "${feats[@]}"; do
        yq -i ".features.$(echo "$feat" | xargs) = true" project.yaml
    done
fi
if [[ -n "$DISABLE_FEATURES" ]]; then
    IFS=',' read -ra feats <<< "$DISABLE_FEATURES"
    for feat in "${feats[@]}"; do
        yq -i ".features.$(echo "$feat" | xargs) = false" project.yaml
    done
fi

[[ -n "$PRIMARY_MODEL" ]] && yq -i ".providers.primary.model = \"$PRIMARY_MODEL\"" project.yaml

yq -i '.providers.primary.name = "custom"' project.yaml
yq -i '.providers.primary.base_url = "https://api.fuelix.ai/v1"' project.yaml
yq -i '.providers.primary.api_key_env = "FUELIX_API_KEY"' project.yaml

if [[ -n "$PROMPT_FILE" ]] && [[ -f "$PROMPT_FILE" ]]; then
    cp "$PROMPT_FILE" app/prompts/assistant.md
    log "Custom prompt applied"
fi

log "Customization complete"

# ============================================================================
# Step 3: Generate per-PoC secrets
# ============================================================================
step "Generating secrets..."

JWT_SECRET=$(openssl rand -hex 32)
JWT_REFRESH_SECRET=$(openssl rand -hex 32)
CREDS_KEY=$(openssl rand -hex 16)
CREDS_IV=$(openssl rand -hex 8)
MEILI_MASTER_KEY=$(openssl rand -hex 16)

# ============================================================================
# Step 4: Commit and push to GitHub
# ============================================================================
step "Pushing to GitHub..."

git add -A
git commit -m "Configure PoC: ${NAME}

Automated deployment by D&AI Advisory.
Features: $(yq '.features | to_entries | map(select(.value == true)) | map(.key) | join(", ")' project.yaml)" \
    --author="Archie <noreply@anthropic.com>" \
    2>/dev/null || log "No changes to commit"

git push origin main 2>&1 || err "Failed to push to GitHub"
log "Code pushed: https://github.com/$REPO_FULL"

# ============================================================================
# Step 5: Create empty Railway service
# ============================================================================
step "Creating Railway service..."

rw add --service "$SLUG" 2>&1 || err "Failed to create Railway service '$SLUG'"
log "Service '$SLUG' created in Railway"

# ============================================================================
# Step 6: Set service-level variables
# ============================================================================
step "Setting variables..."

# Shared vars (FUELIX_API_KEY, etc.) are inherited from project-level shared variables.
# Only set per-PoC values here.
set_var() {
    rw variable set "$1=$2" --service "$SLUG" 2>&1 || warn "Failed to set $1"
}

set_var "APP_TITLE" "$NAME"
set_var "PORT" "3080"
set_var "HOST" "0.0.0.0"
set_var "ALLOW_REGISTRATION" "true"
set_var "SEARCH" "$(yq '.features.search' project.yaml)"
set_var "JWT_SECRET" "$JWT_SECRET"
set_var "JWT_REFRESH_SECRET" "$JWT_REFRESH_SECRET"
set_var "CREDS_KEY" "$CREDS_KEY"
set_var "CREDS_IV" "$CREDS_IV"
set_var "MEILI_MASTER_KEY" "$MEILI_MASTER_KEY"
# Railway CLI does not resolve ${{ServiceName.VAR}} reference syntax — read the
# actual MongoDB URL from the MongoDB service's variables and set it directly.
MONGO_URL_RAW=$(rw variable --service "MongoDB" 2>/dev/null | grep -A1 "MONGO_URL" | grep -v "MONGO_URL" | tr -d ' │' | head -1)
if [[ -n "$MONGO_URL_RAW" ]]; then
    set_var "MONGO_URI" "$MONGO_URL_RAW"
    log "MONGO_URI set from MongoDB service"
else
    warn "Could not read MONGO_URL from MongoDB service — set MONGO_URI manually in Railway dashboard"
fi

log "Variables configured"

# ============================================================================
# Step 7: Deploy code via railway up
# ============================================================================
step "Deploying to Railway..."

# railway up is the only command with -p/-s/-e flags — works from any CWD.
# --ci streams build logs and exits when done.
# Deploy from the repo directory (cd into it so railway up uses it as context).
cd "$REPO_DIR"
railway up \
    -p "$PROJECT_ID" \
    -s "$SLUG" \
    -e "$ENV_ID" \
    --ci 2>&1 || err "railway up failed — check build logs above"

log "Deploy complete"

# ============================================================================
# Step 8: Generate domain and verify
# ============================================================================
step "Generating domain and verifying..."

DOMAIN=$(rw domain --service "$SLUG" 2>&1) || DOMAIN=""

if [[ -z "$DOMAIN" || "$DOMAIN" == *"rror"* ]]; then
    DOMAIN=$(rw domain 2>&1) || DOMAIN=""
fi

if [[ -z "$DOMAIN" || "$DOMAIN" == *"rror"* ]]; then
    DOMAIN="(domain generation failed — assign manually in Railway dashboard)"
fi

# Verify the deployment is actually reachable
if [[ "$DOMAIN" == http* ]]; then
    log "Waiting 10s for service to start..."
    sleep 10
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN" --max-time 15 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "000" ]]; then
        warn "URL not reachable yet — service may still be starting. Check: $DOMAIN"
    elif [[ "$HTTP_CODE" -ge 200 && "$HTTP_CODE" -lt 400 ]]; then
        log "VERIFIED: $DOMAIN returned HTTP $HTTP_CODE"
    else
        warn "URL returned HTTP $HTTP_CODE — may need more time to start"
    fi
fi

log ""
log "=============================="
log "  PoC Deployment Complete"
log "=============================="
log ""
log "  Name:   $NAME"
log "  Repo:   https://github.com/$REPO_FULL"
log "  URL:    $DOMAIN"
log "  Slug:   $SLUG"
log ""

echo "$DOMAIN"
