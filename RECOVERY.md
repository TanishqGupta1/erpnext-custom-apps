# ERPNext Full Recovery Guide

Complete step-by-step guide to restore every page, doctype, custom script, and sync service from backup.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Backup Contents Overview](#2-backup-contents-overview)
3. [Infrastructure Setup](#3-infrastructure-setup)
4. [Database Restoration](#4-database-restoration)
5. [File Attachments Restoration](#5-file-attachments-restoration)
6. [Custom Apps Installation](#6-custom-apps-installation)
7. [Database Migration](#7-database-migration)
8. [Asset Building](#8-asset-building)
9. [Sync Services Configuration](#9-sync-services-configuration)
10. [Site Configuration](#10-site-configuration)
11. [Verification Checklist](#11-verification-checklist)
12. [Troubleshooting](#12-troubleshooting)
13. [Quick Recovery (Automated)](#13-quick-recovery-automated)

---

## 1. Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4 GB | 8 GB+ |
| Storage | 10 GB | 20 GB+ |
| Docker | v20.10+ | Latest |
| Docker Compose | v2.0+ | Latest |

### Software Dependencies

```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Clone Repository

```bash
git clone <repository-url> erpnext_backup_20260130
cd erpnext_backup_20260130
```

---

## 2. Backup Contents Overview

### Database Backups
Located in `backups/`:

| File | Size | Description |
|------|------|-------------|
| `20260130_075819-erp_visualgraphx_com-database.sql.gz` | 386 MB | Latest database dump (RECOMMENDED) |
| `20260130_044206-erp_visualgraphx_com-database.sql.gz` | 371 MB | Earlier backup |

### File Backups
| File | Description |
|------|-------------|
| `*-private-files.tar` | Private attachments (40 MB) |
| `*-files.tar` | Public files (530 KB) |
| `*-site_config_backup.json` | Site configuration |

### Custom Apps
Located in `apps/`:

| App | Purpose |
|-----|---------|
| `ops_ziflow` | Order Processing System + ZiFlow integration |
| `next_crm` | CRM module |
| `ai_comms_hub` | AI-powered communications |
| `chat_bridge` | Chat integration |
| `chatwoot_bridge` | Chatwoot integration |
| `frappe_search` | Enhanced search |

### What Gets Restored
- All DocTypes (68+ custom doctypes)
- Custom Fields and Property Setters
- Custom Scripts (Client/Server)
- Custom Pages and Reports
- Workspaces and Dashboards
- Print Formats
- Workflows
- Scheduled Jobs
- User Permissions and Roles
- File Attachments
- All transactional data

---

## 3. Infrastructure Setup

### Step 3.1: Start Database Services

```bash
# Start MariaDB and Redis
docker compose up -d mariadb redis-cache redis-queue redis-socketio

# Wait for MariaDB to be healthy (check status)
docker compose ps
```

### Step 3.2: Verify MariaDB is Ready

```bash
# Check if MariaDB accepts connections
docker exec erpnext-mariadb mariadb -u root -prootpassword123 -e "SELECT 1"
```

Expected output: `1`

### Step 3.3: Start Backend Service

```bash
# Start the backend container
docker compose up -d backend

# Wait for initialization (30-60 seconds)
sleep 30

# Verify backend is running
docker logs erpnext-backend --tail 20
```

---

## 4. Database Restoration

### Step 4.1: Create New Site

```bash
docker exec erpnext-backend bench new-site localhost \
    --db-host mariadb \
    --db-port 3306 \
    --db-name erpnext \
    --db-password "ErpNextSecure2024!" \
    --db-root-username root \
    --db-root-password rootpassword123 \
    --admin-password admin \
    --no-mariadb-socket
```

### Step 4.2: Copy Database Backup to Container

```bash
docker cp backups/20260130_075819-erp_visualgraphx_com-database.sql.gz \
    erpnext-backend:/tmp/database.sql.gz
```

### Step 4.3: Restore Database

```bash
docker exec erpnext-backend bench --site localhost restore \
    /tmp/database.sql.gz \
    --db-root-password rootpassword123 \
    --force
```

This restores:
- All tables (62+ OPS-specific tables)
- DocType definitions
- Custom Fields
- User data and permissions
- Transaction history
- System settings

---

## 5. File Attachments Restoration

### Step 5.1: Copy File Archives to Container

```bash
docker cp backups/20260130_075819-erp_visualgraphx_com-private-files.tar \
    erpnext-backend:/tmp/private-files.tar

docker cp backups/20260130_075819-erp_visualgraphx_com-files.tar \
    erpnext-backend:/tmp/public-files.tar
```

### Step 5.2: Extract Private Files

```bash
docker exec erpnext-backend bash -c \
    "cd /home/frappe/frappe-bench/sites/localhost/private && tar -xf /tmp/private-files.tar"
```

### Step 5.3: Extract Public Files

```bash
docker exec erpnext-backend bash -c \
    "cd /home/frappe/frappe-bench/sites/localhost/public && tar -xf /tmp/public-files.tar"
```

### Step 5.4: Fix File Permissions

```bash
docker exec erpnext-backend chown -R frappe:frappe \
    /home/frappe/frappe-bench/sites/localhost
```

---

## 6. Custom Apps Installation

### Step 6.1: Copy Apps to All Containers

The `docker-compose.yml` mounts apps automatically. If not using volume mounts:

```bash
# Copy each custom app
for app in ops_ziflow frappe_search next_crm chat_bridge ai_comms_hub; do
    docker cp apps/$app erpnext-backend:/home/frappe/frappe-bench/apps/
    docker exec erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench/apps/$app
done
```

### Step 6.2: Install Apps via pip (All Containers)

```bash
for container in erpnext-backend erpnext-queue-default erpnext-queue-short erpnext-queue-long erpnext-scheduler; do
    echo "Installing in $container..."
    for app in ops_ziflow frappe_search next_crm chat_bridge ai_comms_hub; do
        docker exec $container pip install -e /home/frappe/frappe-bench/apps/$app --no-deps 2>/dev/null || true
    done
done
```

### Step 6.3: Install Apps to Site

```bash
# Install in correct order (dependencies first)
docker exec erpnext-backend bench --site localhost install-app frappe_search
docker exec erpnext-backend bench --site localhost install-app ops_ziflow
docker exec erpnext-backend bench --site localhost install-app next_crm
docker exec erpnext-backend bench --site localhost install-app chat_bridge
docker exec erpnext-backend bench --site localhost install-app ai_comms_hub
```

### Step 6.4: Verify Installed Apps

```bash
docker exec erpnext-backend bench --site localhost list-apps
```

Expected output:
```
frappe
erpnext
ops_ziflow
frappe_search
next_crm
chat_bridge
ai_comms_hub
```

---

## 7. Database Migration

### Step 7.1: Run Migrations

```bash
docker exec erpnext-backend bench --site localhost migrate
```

This syncs:
- DocType schema changes
- Custom Field updates
- Property Setter changes
- Fixtures from apps

### Step 7.2: Verify Migration

```bash
# Check for any pending migrations
docker exec erpnext-backend bench --site localhost show-pending-patches
```

---

## 8. Asset Building

### Step 8.1: Build Frontend Assets

```bash
docker exec erpnext-backend bench build
```

### Step 8.2: Sync Assets to Frontend Container

```bash
# Sync Frappe assets
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/frappe/dist /tmp/frappe_dist
docker exec -u root erpnext-frontend mkdir -p /home/frappe/frappe-bench/sites/assets/frappe/dist
docker cp /tmp/frappe_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/frappe/dist/
rm -rf /tmp/frappe_dist

# Sync ERPNext assets
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/erpnext/dist /tmp/erpnext_dist
docker exec -u root erpnext-frontend mkdir -p /home/frappe/frappe-bench/sites/assets/erpnext/dist
docker cp /tmp/erpnext_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/erpnext/dist/
rm -rf /tmp/erpnext_dist

# Sync assets manifest
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/assets.json \
    erpnext-frontend:/home/frappe/frappe-bench/sites/assets/
```

### Step 8.3: Start All Services

```bash
docker compose up -d
```

### Step 8.4: Clear Cache

```bash
docker exec erpnext-backend bench --site localhost clear-cache
docker exec erpnext-backend bench --site localhost clear-website-cache
```

---

## 9. Sync Services Configuration

### Scheduled Jobs (Automatic via hooks.py)

These are automatically registered when apps are installed:

| Job | Schedule | App |
|-----|----------|-----|
| Poll ZiFlow Proofs | Every 6 hours | ops_ziflow |
| Poll OnPrintShop Quotes | Every 10 minutes | ops_ziflow |
| Poll OnPrintShop Orders | Every 6 hours | ops_ziflow |
| Sync Chat Conversations | Every 5 minutes | chat_bridge |
| Sync Pending Messages | Hourly | ai_comms_hub |
| Daily Analytics | Daily | ai_comms_hub |

### Step 9.1: Verify Scheduler is Running

```bash
docker logs erpnext-scheduler --tail 50
```

### Step 9.2: Verify Workers are Running

```bash
docker compose ps | grep queue
```

### Step 9.3: Test a Scheduled Job Manually

```bash
docker exec erpnext-backend bench --site localhost execute \
    ops_ziflow.ops_ziflow.doctype.ops_ziflow_settings.ops_ziflow_settings.poll_proofs
```

---

## 10. Site Configuration

### Step 10.1: Update Site Config (if needed)

Reference config is in `backups/*-site_config_backup.json`

Key settings to configure:

```bash
# Enable developer mode (if needed)
docker exec erpnext-backend bench --site localhost set-config developer_mode 1

# Enable server scripts
docker exec erpnext-backend bench --site localhost set-config server_script_enabled 1

# Set encryption key (use original from backup)
docker exec erpnext-backend bench --site localhost set-config encryption_key \
    "e6HMAgRXPT_Reje6pAFfc26cHOqtovTSCT2sO5Ius3Q="
```

### Step 10.2: Configure API Keys

For ZiFlow integration:
```bash
# Via bench
docker exec erpnext-backend bench --site localhost set-config ziflow_api_key \
    "cn1393t8lbb2hb71iq67rkaecu"
```

Or update via ERPNext UI:
1. Go to OPS ZiFlow Settings
2. Enter API credentials

---

## 11. Verification Checklist

### Access ERPNext

```
URL: http://localhost:8080
Username: Administrator
Password: admin (or original password from backup)
```

### Verify Each Component

| Component | How to Verify | Expected |
|-----------|---------------|----------|
| Login | Access http://localhost:8080 | Login page loads |
| Dashboard | Click "Home" | Workspaces visible |
| OPS Order | Search "OPS Order" | DocType accessible |
| Custom Fields | Open any Customer | Custom fields visible |
| File Attachments | Open any record with files | Files load correctly |
| Print Formats | Print any document | Format renders |
| Reports | Run any report | Data displays |
| Scheduler | Check scheduler logs | Jobs executing |

### Run Verification Commands

```bash
# Check site status
docker exec erpnext-backend bench --site localhost doctor

# List all doctypes
docker exec erpnext-backend bench --site localhost list-doctype-names

# Check scheduled jobs
docker exec erpnext-backend bench --site localhost show-scheduler-status
```

---

## 12. Troubleshooting

### Issue: Site Not Loading

```bash
# Check all containers are running
docker compose ps

# Check backend logs
docker logs erpnext-backend --tail 100

# Restart services
docker compose restart
```

### Issue: Database Connection Failed

```bash
# Verify MariaDB is healthy
docker exec erpnext-mariadb mariadb -u erpnext -p'ErpNextSecure2024!' -e "SELECT 1"

# Check site_config.json
docker exec erpnext-backend cat sites/localhost/site_config.json
```

### Issue: Assets Not Loading (404 errors)

```bash
# Rebuild assets
docker exec erpnext-backend bench build --force

# Re-sync to frontend
./post-restart.sh
```

### Issue: Custom App Not Found

```bash
# Verify app is installed
docker exec erpnext-backend pip list | grep ops_ziflow

# Reinstall app
docker exec erpnext-backend pip install -e /home/frappe/frappe-bench/apps/ops_ziflow --no-deps
```

### Issue: Scheduler Jobs Not Running

```bash
# Check scheduler status
docker logs erpnext-scheduler

# Restart scheduler
docker compose restart scheduler

# Enable scheduler
docker exec erpnext-backend bench --site localhost enable-scheduler
```

### Issue: Permission Denied Errors

```bash
# Fix ownership
docker exec -u root erpnext-backend chown -R frappe:frappe /home/frappe/frappe-bench
```

---

## 13. Quick Recovery (Automated)

For a quick full recovery, use the provided scripts in order:

### Option A: Full Restore from Backup

```bash
# Step 1: Restore database and files
./restore.sh

# Step 2: Install custom apps
./install_apps.sh

# Step 3: (After container restart) Re-sync assets
./post-restart.sh
```

### Option B: Fresh Setup

```bash
# Complete fresh setup with all apps
./setup.sh
```

### Option C: Manual Step-by-Step

Follow sections 3-11 above in sequence.

---

## Recovery Complete

After successful recovery, you should have:

- All 68+ custom DocTypes (OPS Order, OPS Quote, etc.)
- All Custom Fields on standard DocTypes
- All Custom Scripts (Client & Server)
- All Custom Pages and Reports
- All Workspaces and Dashboards
- All Print Formats
- All File Attachments
- All Sync Services running
- All User Permissions intact
- All Transaction History preserved

---

## Support

For issues:
1. Check `docker logs <container-name>`
2. Check `sites/localhost/logs/` for error logs
3. Run `bench doctor` for diagnostics
