# ERPNext Custom Apps Setup

ERPNext v16 Docker setup with custom applications for OPS (Order Processing System) and ZiFlow proofing integration.

## Custom Apps Included

| App | Description |
|-----|-------------|
| **ops_ziflow** | Order/Quote management with ZiFlow proofing integration, dashboards, and custom doctypes |
| **frappe_search** | Enhanced search functionality |
| **next_crm** | CRM enhancements and integrations |
| **chat_bridge** | Chat integration capabilities |
| **ai_comms_hub** | AI-powered communications hub |

## Prerequisites

- Docker Desktop (v20.10+)
- Docker Compose (v2.0+)
- Git
- 8GB+ RAM recommended

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/TanishqGupta1/erpnext-custom-apps.git
cd erpnext-custom-apps
```

### 2. Start Docker Containers

```bash
docker compose up -d
```

Wait for all containers to be healthy (2-3 minutes):

```bash
docker compose ps
```

### 3. Create Site and Install Apps

```bash
# Create a new site
docker exec -it erpnext-backend bench new-site localhost \
  --mariadb-root-password 123 \
  --admin-password admin \
  --no-mariadb-socket

# Set as current site
docker exec -it erpnext-backend bash -c 'echo "localhost" > sites/currentsite.txt'

# Install ERPNext
docker exec -it erpnext-backend bench --site localhost install-app erpnext
```

### 4. Install Custom Apps

```bash
# Install custom apps via pip (required after every container restart)
for app in ops_ziflow frappe_search next_crm chat_bridge ai_comms_hub; do
  docker exec erpnext-backend pip install -e /home/frappe/frappe-bench/apps/$app --no-deps
done

# Install apps to site
docker exec erpnext-backend bench --site localhost install-app ops_ziflow
docker exec erpnext-backend bench --site localhost install-app frappe_search
docker exec erpnext-backend bench --site localhost install-app next_crm
docker exec erpnext-backend bench --site localhost install-app chat_bridge
docker exec erpnext-backend bench --site localhost install-app ai_comms_hub
```

### 5. Build Assets

```bash
# Build frontend assets
docker exec erpnext-backend bench build

# Sync assets to frontend container
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/frappe/dist /tmp/frappe_dist
docker exec -u root erpnext-frontend mkdir -p /home/frappe/frappe-bench/sites/assets/frappe/dist
docker cp /tmp/frappe_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/frappe/dist/
rm -rf /tmp/frappe_dist

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/erpnext/dist /tmp/erpnext_dist
docker exec -u root erpnext-frontend mkdir -p /home/frappe/frappe-bench/sites/assets/erpnext/dist
docker cp /tmp/erpnext_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/erpnext/dist/
rm -rf /tmp/erpnext_dist

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/assets.json erpnext-frontend:/home/frappe/frappe-bench/sites/assets/

# Clear cache
docker exec erpnext-backend bench --site localhost clear-cache
```

### 6. Access the Application

Open in browser: **http://localhost:8080**

- **Username:** Administrator
- **Password:** admin (or what you set during site creation)

## Restoring from Backup

If you have a database backup to restore:

### 1. Place Backup Files

Place your backup files in the project directory:
- `*-database.sql.gz` - Database backup
- `*-files.tar` - Public files (optional)
- `*-private-files.tar` - Private files (optional)

### 2. Run Restore

```bash
# Restore database (adjust filename as needed)
docker exec -it erpnext-backend bench --site localhost restore \
  /path/to/database-backup.sql.gz \
  --force

# Migrate database
docker exec -it erpnext-backend bench --site localhost migrate

# Clear cache
docker exec -it erpnext-backend bench --site localhost clear-cache
```

## After Container Restart

Custom apps installed via `pip install -e` are lost when containers restart. Re-run:

```bash
# Reinstall custom apps in all containers
for container in erpnext-backend erpnext-queue-default erpnext-queue-short erpnext-queue-long erpnext-scheduler; do
  for app in ops_ziflow frappe_search next_crm chat_bridge ai_comms_hub; do
    docker exec $container pip install -e /home/frappe/frappe-bench/apps/$app --no-deps 2>/dev/null
  done
done

# Re-sync assets to frontend
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/frappe/dist /tmp/frappe_dist
docker cp /tmp/frappe_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/frappe/dist/
rm -rf /tmp/frappe_dist

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/erpnext/dist /tmp/erpnext_dist
docker cp /tmp/erpnext_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/erpnext/dist/
rm -rf /tmp/erpnext_dist

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/assets.json erpnext-frontend:/home/frappe/frappe-bench/sites/assets/
```

## Container Architecture

| Container | Purpose |
|-----------|---------|
| erpnext-backend | Frappe/ERPNext application server |
| erpnext-frontend | Nginx web server |
| erpnext-websocket | Real-time updates via Socket.IO |
| erpnext-queue-default | Background job worker (default queue) |
| erpnext-queue-short | Background job worker (short queue) |
| erpnext-queue-long | Background job worker (long queue) |
| erpnext-scheduler | Scheduled task runner |
| erpnext-mariadb | MariaDB database |
| erpnext-redis-cache | Redis for caching |
| erpnext-redis-queue | Redis for job queues |
| erpnext-redis-socketio | Redis for Socket.IO |

## OPS Custom Doctypes

The ops_ziflow app includes these custom doctypes:

- **OPS Order** - Order management
- **OPS Quote** - Quote management
- **OPS Customer** - Customer records
- **OPS Product** - Product catalog
- **OPS ZiFlow Proof** - ZiFlow proofing integration
- **OPS Department** - Department management
- **OPS Store** - Store locations
- **OPS Master Option** - Configurable options

## Dashboards

Access custom dashboards at:
- `/app/ops-orders-dashboard` - Orders Dashboard
- `/app/ops-quotes-dashboard` - Quotes Dashboard
- `/app/ziflow-dashboard` - ZiFlow Proofing Dashboard
- `/app/ops-cluster-dashboard` - OPS Cluster Dashboard

## Troubleshooting

### Blank Pages / CSS Not Loading

Re-sync assets from backend to frontend:

```bash
docker exec -u root erpnext-frontend rm -rf /home/frappe/frappe-bench/sites/assets/frappe/dist
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/frappe/dist /tmp/frappe_dist
docker cp /tmp/frappe_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/frappe/dist/
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/assets.json erpnext-frontend:/home/frappe/frappe-bench/sites/assets/
docker exec erpnext-backend bench --site localhost clear-cache
```

### "Module not found" Errors

Reinstall custom apps:

```bash
for app in ops_ziflow frappe_search next_crm chat_bridge ai_comms_hub; do
  docker exec erpnext-backend pip install -e /home/frappe/frappe-bench/apps/$app --no-deps
done
```

### Dashboard Charts Not Loading

Add frappe-charts bundle:

```bash
docker exec erpnext-backend cp /home/frappe/frappe-bench/apps/frappe/node_modules/frappe-charts/dist/frappe-charts.umd.js \
  /home/frappe/frappe-bench/sites/assets/frappe/dist/js/frappe-charts.bundle.js

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/frappe/dist/js/frappe-charts.bundle.js \
  erpnext-frontend:/home/frappe/frappe-bench/sites/assets/frappe/dist/js/
```

### Redis Connection Errors

Check Redis containers are running:

```bash
docker compose ps | grep redis
docker compose restart redis-cache redis-queue redis-socketio
```

## Stopping the Environment

```bash
# Stop containers (preserves data)
docker compose stop

# Stop and remove containers (preserves volumes)
docker compose down

# Remove everything including data
docker compose down -v
```

## License

Custom apps are proprietary. Frappe and ERPNext are licensed under GNU GPLv3.
