#!/usr/bin/env bash
# ============================================================================
# Generate Secrets
# ============================================================================
# Generates random values for all security-sensitive environment variables.
# Output: KEY=VALUE pairs, one per line (pipe to file or use in scripts).
#
# Usage:
#   ./scripts/generate-secrets.sh              # Print to stdout
#   ./scripts/generate-secrets.sh >> .env       # Append to .env
#   eval "$(./scripts/generate-secrets.sh)"     # Load into current shell
# ============================================================================

set -euo pipefail

echo "JWT_SECRET=$(openssl rand -hex 32)"
echo "JWT_REFRESH_SECRET=$(openssl rand -hex 32)"
echo "CREDS_KEY=$(openssl rand -hex 16)"
echo "CREDS_IV=$(openssl rand -hex 8)"
echo "MEILI_MASTER_KEY=$(openssl rand -hex 16)"
