#!/usr/bin/env bash
set -e

WORKSPACE="/workspaces/xmplaylist"
echo "Workspace path detected: $WORKSPACE"

# Fix permissions for visibility (even if noexec won't allow exec)
sudo chown -R vscode:vscode "$WORKSPACE/scripts" || true
sudo chmod -R +x "$WORKSPACE/scripts" || true

# Run explicitly with bash (bypass exec permission)
bash "$WORKSPACE/scripts/setup"

