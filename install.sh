#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
echo "Installing Antigravity Pure HUD..."
agy plugin install "$SCRIPT_DIR"
echo "Done! In AGY CLI, enable statusline with:"
echo "/statusline $SCRIPT_DIR/hooks/status-line.sh"
