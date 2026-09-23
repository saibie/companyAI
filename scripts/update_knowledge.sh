#!/usr/bin/env bash
set -e

# ==============================================================================
# update_knowledge.sh
# Synchronizes Graphify AST Knowledge Graph & Validates OKF Bundle
# ==============================================================================

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKSPACE_DIR"

echo "=== [1/2] Updating Graphify AST Knowledge Graph ==="
if ! command -v graphify &> /dev/null; then
    echo "graphify CLI not found in PATH. Attempting to run via uvx graphifyy..."
    uvx graphifyy extract . --code-only
    uvx graphifyy cluster-only .
else
    echo "Running graphify extract..."
    graphify extract . --code-only
    echo "Updating clusters and reports..."
    graphify cluster-only .
fi

echo "=== [2/2] Validating OKF (Open Knowledge Format) Bundle ==="
if [ -d "$WORKSPACE_DIR/okf" ]; then
    DOC_COUNT=$(find "$WORKSPACE_DIR/okf" -name "*.md" | wc -l)
    echo "Found OKF bundle at okf/ with $DOC_COUNT documents."
    if [ -f "$WORKSPACE_DIR/okf/index.md" ]; then
        echo "OKF Master Index (okf/index.md) exists."
    else
        echo "WARNING: okf/index.md is missing!"
    fi
else
    echo "WARNING: okf/ directory does not exist!"
fi

echo "=== Knowledge Graph & OKF Sync Complete ==="
