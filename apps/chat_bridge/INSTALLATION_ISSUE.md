# Installation Issue - Python Module Import

## Problem
The `chat_bridge` app cannot be installed because Python cannot import the module:
```
ModuleNotFoundError: No module named 'chat_bridge'
```

## What We've Tried
1. ✅ Copied app files to `/home/frappe/frappe-bench/apps/chat_bridge/`
2. ✅ Fixed file permissions (chown to frappe:frappe)
3. ✅ Created `hooks.py` at root level
4. ✅ Added app to `apps.txt`
5. ✅ Restarted containers
6. ❌ `pip install -e .` failed due to permissions
7. ❌ `bench get-app` doesn't work with local file paths

## Current Status
- App files are in correct location: `/home/frappe/frappe-bench/apps/chat_bridge/`
- App structure matches Frappe conventions
- `hooks.py` exists at `chat_bridge/hooks.py`
- App is listed in `apps.txt`
- Python still cannot import the module

## Possible Solutions

### Option 1: Install as Python Package (Recommended)
```bash
docker exec -u root erpnext-backend bash -c "cd /home/frappe/frappe-bench/apps/chat_bridge && pip install -e ."
```

### Option 2: Use bench new-app and Copy Files
```bash
# Create app with bench
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench new-app chat_bridge"
# Then copy our files over the generated structure
```

### Option 3: Check Python Path Configuration
Verify that `/home/frappe/frappe-bench/apps` is in Python's sys.path when Frappe runs.

### Option 4: Manual Database Registration
Manually add the app to the `tabInstalled Application` table in the database, then run migrations.

## Next Steps
1. Try Option 1 (install as package with root user)
2. If that fails, try Option 2 (use bench new-app)
3. Verify Python can import the module after installation
4. Complete app installation with `bench --site test-chatwoot.localhost install-app chat_bridge`


