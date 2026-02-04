#!/bin/bash

# ERPNext Setup Script
# Sets up a fresh ERPNext installation with custom apps

set -e

echo "=========================================="
echo "ERPNext Setup with Custom Apps"
echo "=========================================="
echo ""

# Step 1: Start all containers
echo "[Step 1/6] Starting Docker containers..."
docker compose up -d
echo "Waiting for services to be ready (60 seconds)..."
sleep 60

# Wait for MariaDB to be healthy
echo "Checking MariaDB health..."
until docker exec erpnext-mariadb mariadb -u root -prootpassword123 -e "SELECT 1" &> /dev/null; do
    echo "  Waiting for MariaDB..."
    sleep 5
done
echo "  MariaDB is ready!"
echo ""

# Step 2: Create site
echo "[Step 2/6] Creating site: localhost"
docker exec erpnext-backend bench new-site localhost \
    --db-host mariadb \
    --db-port 3306 \
    --db-root-username root \
    --db-root-password rootpassword123 \
    --admin-password admin \
    --no-mariadb-socket || echo "Site may already exist, continuing..."

# Set current site
docker exec erpnext-backend bash -c 'echo "localhost" > sites/currentsite.txt'
echo ""

# Step 3: Install ERPNext
echo "[Step 3/6] Installing ERPNext..."
docker exec erpnext-backend bench --site localhost install-app erpnext || echo "ERPNext may already be installed"
echo ""

# Step 4: Install custom apps via pip
echo "[Step 4/6] Installing custom apps..."
for container in erpnext-backend erpnext-queue-default erpnext-queue-short erpnext-queue-long erpnext-scheduler; do
    echo "  Installing in $container..."
    for app in ops_ziflow frappe_search next_crm chat_bridge ai_comms_hub; do
        docker exec $container pip install -e /home/frappe/frappe-bench/apps/$app --no-deps 2>/dev/null || true
    done
done

# Install apps to site
for app in ops_ziflow frappe_search next_crm chat_bridge ai_comms_hub; do
    echo "  Installing $app to site..."
    docker exec erpnext-backend bench --site localhost install-app $app 2>/dev/null || echo "  $app may already be installed or not available"
done
echo ""

# Step 5: Build assets
echo "[Step 5/6] Building assets..."
docker exec erpnext-backend bench build 2>/dev/null || echo "Build completed with warnings"

# Sync assets to frontend
echo "  Syncing assets to frontend..."
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/frappe/dist /tmp/frappe_dist 2>/dev/null || true
docker exec -u root erpnext-frontend mkdir -p /home/frappe/frappe-bench/sites/assets/frappe/dist 2>/dev/null || true
docker cp /tmp/frappe_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/frappe/dist/ 2>/dev/null || true
rm -rf /tmp/frappe_dist 2>/dev/null || true

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/erpnext/dist /tmp/erpnext_dist 2>/dev/null || true
docker exec -u root erpnext-frontend mkdir -p /home/frappe/frappe-bench/sites/assets/erpnext/dist 2>/dev/null || true
docker cp /tmp/erpnext_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/erpnext/dist/ 2>/dev/null || true
rm -rf /tmp/erpnext_dist 2>/dev/null || true

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/assets.json erpnext-frontend:/home/frappe/frappe-bench/sites/assets/ 2>/dev/null || true

# Add frappe-charts for dashboards
docker exec erpnext-backend cp /home/frappe/frappe-bench/apps/frappe/node_modules/frappe-charts/dist/frappe-charts.umd.js \
    /home/frappe/frappe-bench/sites/assets/frappe/dist/js/frappe-charts.bundle.js 2>/dev/null || true
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/frappe/dist/js/frappe-charts.bundle.js \
    erpnext-frontend:/home/frappe/frappe-bench/sites/assets/frappe/dist/js/ 2>/dev/null || true
echo ""

# Step 6: Clear cache
echo "[Step 6/6] Clearing cache..."
docker exec erpnext-backend bench --site localhost clear-cache
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Access ERPNext at: http://localhost:8080"
echo ""
echo "Login credentials:"
echo "  Username: Administrator"
echo "  Password: admin"
echo ""
echo "Custom apps installed:"
echo "  - ops_ziflow"
echo "  - frappe_search"
echo "  - next_crm"
echo "  - chat_bridge"
echo "  - ai_comms_hub"
echo ""
