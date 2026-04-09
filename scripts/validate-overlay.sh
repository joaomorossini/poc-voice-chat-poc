#!/usr/bin/env bash
# ============================================================================
# Validate Overlay Targets
# ============================================================================
# Checks that all sed targets in app/Dockerfile still exist in the LibreChat
# submodule. Run this after `git submodule update` to catch silent breakage.
# ============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIBRECHAT_DIR="$ROOT_DIR/librechat"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check() {
    local file="$1"
    local pattern="$2"
    local desc="$3"

    if [[ ! -f "$LIBRECHAT_DIR/$file" ]]; then
        echo -e "  ${RED}FAIL${NC} $desc — file not found: $file"
        ((FAIL++))
        return
    fi

    if grep -q "$pattern" "$LIBRECHAT_DIR/$file"; then
        echo -e "  ${GREEN}PASS${NC} $desc"
        ((PASS++))
    else
        echo -e "  ${YELLOW}WARN${NC} $desc — pattern not found in $file"
        ((WARN++))
    fi
}

echo "Validating overlay targets against librechat/ submodule..."
echo ""

# HTML metadata targets
check "client/index.html" "<title>LibreChat</title>" "HTML title tag"
check "client/index.html" 'content="LibreChat"' "HTML meta content"

# CSS entry point (for theme injection)
check "client/src/style.css" "" "CSS entry point exists" # Just check file exists

# Logo target directory
if [[ -d "$LIBRECHAT_DIR/client/public/assets" ]]; then
    echo -e "  ${GREEN}PASS${NC} Logo target directory exists"
    ((PASS++))
else
    echo -e "  ${RED}FAIL${NC} Logo target directory missing: client/public/assets"
    ((FAIL++))
fi

echo ""
echo "Results: ${PASS} passed, ${WARN} warnings, ${FAIL} failures"

if [[ $FAIL -gt 0 ]]; then
    echo -e "${RED}Overlay targets have breaking changes. Update app/Dockerfile before building.${NC}"
    exit 1
elif [[ $WARN -gt 0 ]]; then
    echo -e "${YELLOW}Some targets may have changed. Build may succeed but patches might not apply.${NC}"
    exit 0
else
    echo -e "${GREEN}All overlay targets verified.${NC}"
    exit 0
fi
