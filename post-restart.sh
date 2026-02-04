#!/bin/bash

# Run this script after container restart to reinstall custom apps and sync assets

echo "Reinstalling custom apps..."
for container in erpnext-backend erpnext-queue-default erpnext-queue-short erpnext-queue-long erpnext-scheduler; do
    echo "  $container..."
    for app in ops_ziflow frappe_search next_crm chat_bridge ai_comms_hub; do
        docker exec $container pip install -e /home/frappe/frappe-bench/apps/$app --no-deps 2>/dev/null
    done
done

echo ""
echo "Syncing assets to frontend..."
docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/frappe/dist /tmp/frappe_dist 2>/dev/null
docker exec -u root erpnext-frontend rm -rf /home/frappe/frappe-bench/sites/assets/frappe/dist 2>/dev/null
docker exec -u root erpnext-frontend mkdir -p /home/frappe/frappe-bench/sites/assets/frappe/dist
docker cp /tmp/frappe_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/frappe/dist/
rm -rf /tmp/frappe_dist

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/erpnext/dist /tmp/erpnext_dist 2>/dev/null
docker exec -u root erpnext-frontend rm -rf /home/frappe/frappe-bench/sites/assets/erpnext/dist 2>/dev/null
docker exec -u root erpnext-frontend mkdir -p /home/frappe/frappe-bench/sites/assets/erpnext/dist
docker cp /tmp/erpnext_dist/. erpnext-frontend:/home/frappe/frappe-bench/sites/assets/erpnext/dist/
rm -rf /tmp/erpnext_dist

docker cp erpnext-backend:/home/frappe/frappe-bench/sites/assets/assets.json erpnext-frontend:/home/frappe/frappe-bench/sites/assets/

echo ""
echo "Clearing cache..."
docker exec erpnext-backend bench --site localhost clear-cache

echo ""
echo "Done! Access at http://localhost:8080"
