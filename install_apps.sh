#!/bin/bash

# Custom Apps Installation Script
# Run this after restore.sh completes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="$SCRIPT_DIR/apps"
SITE_NAME="localhost"

echo "=========================================="
echo "Installing Custom Apps"
echo "=========================================="
echo ""

# Copy custom apps to container
echo "[1/4] Copying custom apps to container..."

# Copy ops_ziflow
docker cp "$APPS_DIR/ops_ziflow" erpnext-backend:/home/frappe/frappe-bench/apps/
docker exec erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench/apps/ops_ziflow

# Copy other custom apps if needed
if [ -d "$APPS_DIR/chat_bridge" ]; then
    docker cp "$APPS_DIR/chat_bridge" erpnext-backend:/home/frappe/frappe-bench/apps/
    docker exec erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench/apps/chat_bridge
fi

if [ -d "$APPS_DIR/ai_comms_hub" ]; then
    docker cp "$APPS_DIR/ai_comms_hub" erpnext-backend:/home/frappe/frappe-bench/apps/
    docker exec erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench/apps/ai_comms_hub
fi

if [ -d "$APPS_DIR/chatwoot_bridge" ]; then
    docker cp "$APPS_DIR/chatwoot_bridge" erpnext-backend:/home/frappe/frappe-bench/apps/
    docker exec erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench/apps/chatwoot_bridge
fi

if [ -d "$APPS_DIR/frappe_search" ]; then
    docker cp "$APPS_DIR/frappe_search" erpnext-backend:/home/frappe/frappe-bench/apps/
    docker exec erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench/apps/frappe_search
fi

if [ -d "$APPS_DIR/next_crm" ]; then
    docker cp "$APPS_DIR/next_crm" erpnext-backend:/home/frappe/frappe-bench/apps/
    docker exec erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench/apps/next_crm
fi

echo "  Apps copied!"
echo ""

# Install apps to site
echo "[2/4] Installing apps on site..."

# Install ops_ziflow
echo "  Installing ops_ziflow..."
docker exec erpnext-backend bench --site $SITE_NAME install-app ops_ziflow || echo "  ops_ziflow may already be installed"

echo ""

# Run migrations
echo "[3/4] Running migrations..."
docker exec erpnext-backend bench --site $SITE_NAME migrate
echo ""

# Build assets
echo "[4/4] Building assets..."
docker exec erpnext-backend bench build
echo ""

# Clear cache
docker exec erpnext-backend bench --site $SITE_NAME clear-cache

echo "=========================================="
echo "Custom Apps Installed!"
echo "=========================================="
echo ""
echo "Installed apps:"
docker exec erpnext-backend bench --site $SITE_NAME list-apps
echo ""
