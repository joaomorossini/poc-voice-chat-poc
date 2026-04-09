#!/usr/bin/env bash
# ============================================================================
# DigitalOcean Droplet Setup
# ============================================================================
# Run this on a fresh Ubuntu 22.04+ droplet to deploy the project.
#
# Usage:
#   1. Create a droplet ($6/mo minimum, 1GB RAM recommended: $12/mo)
#   2. SSH in: ssh root@your-droplet-ip
#   3. Clone your repo: git clone --recursive https://github.com/you/your-project.git
#   4. Run: cd your-project && bash deploy/digitalocean/setup.sh
# ============================================================================

set -euo pipefail

echo "=== Installing Docker ==="
curl -fsSL https://get.docker.com | sh

echo "=== Installing Docker Compose ==="
apt-get install -y docker-compose-plugin

echo "=== Installing yq ==="
snap install yq

echo "=== Running bootstrap ==="
./scripts/bootstrap.sh

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env and replace all CHANGE_ME values"
echo "  2. Run: make up"
echo "  3. (Optional) Set up a domain with: deploy/digitalocean/nginx.conf"
echo ""
