#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/opt/kweekkast/kweekkast-pi"
APP_DIR="$REPO_DIR/core"
SERVICE="kweekkast-core"

echo "Stopping service..."
sudo systemctl stop "$SERVICE"

echo "Pulling latest code..."
sudo -u kweek git -C "$REPO_DIR" pull

echo "Syncing UV..."
sudo -u kweek bash -lc "cd '$APP_DIR' && ~/.local/bin/uv sync --no-dev"

echo "Starting service..."
sudo systemctl start "$SERVICE"

echo "Service status:"
sudo systemctl status "$SERVICE" --no-pager

echo "Following logs..."
sudo journalctl -u "$SERVICE" -f