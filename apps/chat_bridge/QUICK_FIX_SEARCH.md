# Quick Fix: DocType Not Showing in Search

If "Chatwoot Integration Settings" doesn't appear when searching, try these steps:

## Option 1: Direct URL Access (Fastest)

1. **Go directly to the DocType:**
   ```
   https://erp.visualgraphx.com/app/chatwoot-integration-settings
   ```

2. **Or use this URL pattern:**
   ```
   https://erp.visualgraphx.com/app/chatwoot-integration-settings/new
   ```

## Option 2: Via List View

1. **Type in search:** `List Chatwoot Integration Settings`
2. **Or go to:** Settings → Custom → Chatwoot Integration Settings

## Option 3: Force Reload DocType

Run these commands to reload the DocType:

```bash
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com reload-doctype 'Chatwoot Integration Settings'"
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com clear-cache"
cd E:\Docker\Frappe && docker-compose restart erpnext-frontend
```

Then refresh your browser (Ctrl+F5) and search again.

## Option 4: Check if DocType Exists

Run this to verify:

```bash
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com console"
```

Then in the console:
```python
import frappe
if frappe.db.exists('DocType', 'Chatwoot Integration Settings'):
    print('DocType exists')
    dt = frappe.get_doc('DocType', 'Chatwoot Integration Settings')
    print(f'Module: {dt.module}')
else:
    print('DocType missing - needs import')
```

## Option 5: Import DocType Manually

If DocType doesn't exist, import it:

```bash
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && python3 apps/chat_bridge/install_doctypes.py"
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com migrate"
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com clear-cache"
cd E:\Docker\Frappe && docker-compose restart erpnext-frontend
```

## Most Likely Solution

**Try Option 1 first** - go directly to:
```
https://erp.visualgraphx.com/app/chatwoot-integration-settings/new
```

This bypasses the search and goes straight to creating a new record.


