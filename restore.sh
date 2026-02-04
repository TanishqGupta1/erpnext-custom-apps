2#!/bin/bash

# ERPNext Backup Restoration Script
# This script restores the ERPNext backup to a fresh Docker installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
SITE_NAME="localhost"
DB_BACKUP="20260130_075819-erp_visualgraphx_com-database.sql.gz"
PRIVATE_FILES="20260130_075819-erp_visualgraphx_com-private-files.tar"
PUBLIC_FILES="20260130_075819-erp_visualgraphx_com-files.tar"

echo "=========================================="
echo "ERPNext Backup Restoration"
echo "=========================================="
echo ""

# Step 1: Start infrastructure services
echo "[Step 1/8] Starting MariaDB and Redis services..."
docker compose up -d mariadb redis-cache redis-queue redis-socketio
echo "Waiting for MariaDB to be healthy..."
sleep 10

# Wait for MariaDB to be ready
until docker exec erpnext-mariadb mariadb -u root -prootpassword123 -e "SELECT 1" &> /dev/null; do
    echo "  Waiting for MariaDB..."
    sleep 5
done
echo "  MariaDB is ready!"
echo ""

# Step 2: Start backend to initialize bench
echo "[Step 2/8] Starting backend service..."
docker compose up -d backend
sleep 15
echo ""

# Step 3: Create new site
echo "[Step 3/8] Creating new site: $SITE_NAME"
docker exec erpnext-backend bench new-site $SITE_NAME \
    --db-host mariadb \
    --db-port 3306 \
    --db-name erpnext \
    --db-password "ErpNextSecure2024!" \
    --db-root-username root \
    --db-root-password rootpassword123 \
    --admin-password admin \
    --no-mariadb-socket || echo "Site may already exist, continuing..."
echo ""

# Step 4: Copy database backup to container
echo "[Step 4/8] Copying database backup to container..."
docker cp "$BACKUP_DIR/$DB_BACKUP" erpnext-backend:/tmp/
echo ""

# Step 5: Restore database
echo "[Step 5/8] Restoring database (this may take several minutes)..."
docker exec erpnext-backend bench --site $SITE_NAME restore /tmp/$DB_BACKUP --db-root-password rootpassword123 --force
echo "  Database restored!"
echo ""

# Step 6: Copy and restore files
echo "[Step 6/8] Restoring private and public files..."
docker cp "$BACKUP_DIR/$PRIVATE_FILES" erpnext-backend:/tmp/
docker cp "$BACKUP_DIR/$PUBLIC_FILES" erpnext-backend:/tmp/

# Extract private files
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench/sites/$SITE_NAME/private && tar -xf /tmp/$PRIVATE_FILES"

# Extract public files
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench/sites/$SITE_NAME/public && tar -xf /tmp/$PUBLIC_FILES"

# Fix permissions
docker exec erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench/sites/$SITE_NAME
echo "  Files restored!"
echo ""

# Step 7: Run migrations
echo "[Step 7/8] Running database migrations..."
docker exec erpnext-backend bench --site $SITE_NAME migrate || echo "Migration completed with warnings"
echo ""

# Step 8: Start all services
echo "[Step 8/8] Starting all services..."
docker compose up -d
echo ""

# Clear cache
echo "Clearing cache..."
docker exec erpnext-backend bench --site $SITE_NAME clear-cache
docker exec erpnext-backend bench --site $SITE_NAME clear-website-cache

echo ""
echo "=========================================="
echo "Restoration Complete!"
echo "=========================================="
echo ""
echo "Access ERPNext at: http://localhost:8080"
echo ""
echo "Default login:"
echo "  Username: Administrator"
echo "  Password: admin (or your original password)"
echo ""
echo "Note: Custom apps (ops_ziflow, etc.) need to be"
echo "installed separately. Run install_apps.sh for that."
echo ""
