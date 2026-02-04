# Final Solution: DocType Import Issue

## Root Cause

The `frappe_search` and `next_crm` apps are breaking ALL bench commands because Frappe tries to load their hooks when running any bench command, and the hooks fail to import with `ModuleNotFoundError`.

**This is a PRE-EXISTING production issue** - not caused by `chat_bridge`.

## Impact

- `bench install-app` fails
- `bench migrate` fails  
- `bench clear-cache` fails
- `bench reload-doctype` fails
- `bench execute` fails

All fail with: `ModuleNotFoundError: No module named 'frappe_search'`

## Solution Per Frappe Documentation

According to [Frappe's official tutorial](https://docs.frappe.io/framework/user/en/tutorial/create-a-doctype), DocTypes should be created via the UI in Developer Mode, which automatically imports them.

### Step 1: Enable Developer Mode

```bash
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com set-config developer_mode 1"
```

### Step 2: Access ERPNext UI

1. Go to: `https://erp.visualgraphx.com`
2. Login as Administrator
3. Open Awesomebar (Ctrl+K) and search for "DocType"
4. Click "New" to create a new DocType

### Step 3: Create DocTypes Manually (or Import JSON)

**Option A: Create via UI** (Recommended per Frappe docs)
- Create each DocType manually in the UI
- Frappe will automatically save the JSON files

**Option B: Import JSON Files**
- Use the "Import" button in DocType List
- Select the JSON files from `apps/chat_bridge/chat_bridge/doctype/`

### Step 4: Fix Pre-Existing Apps

After DocTypes are imported, fix `frappe_search` and `next_crm`:

1. **Install as Python packages:**
```bash
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench/apps/frappe_search && pip install -e ."
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench/apps/next_crm && pip install -e ."
```

2. **Or remove from Installed Applications** if not needed:
```bash
# Via bench console:
installed = frappe.get_single('Installed Applications')
installed.installed_applications = [a for a in installed.installed_applications if a.app_name not in ['frappe_search', 'next_crm']]
installed.save()
frappe.db.commit()
```

## Why This Approach Works

Per Frappe documentation:
- DocTypes created via UI are automatically imported
- No bench commands required for UI creation
- Developer Mode enables boilerplate generation
- This is the standard Frappe workflow

## Files Ready for Import

All DocType JSON files are ready at:
- `apps/chat_bridge/chat_bridge/doctype/chatwoot_integration_settings/chatwoot_integration_settings.json`
- `apps/chat_bridge/chat_bridge/doctype/chatwoot_user_token/chatwoot_user_token.json`
- `apps/chat_bridge/chat_bridge/doctype/chatwoot_contact_mapping/chatwoot_contact_mapping.json`
- `apps/chat_bridge/chat_bridge/doctype/chatwoot_conversation_mapping/chatwoot_conversation_mapping.json`

## Next Steps

1. Enable Developer Mode (command above)
2. Access ERPNext UI
3. Import DocTypes via UI (Import button) or create manually
4. Fix `frappe_search` and `next_crm` to restore bench commands
5. Test Chatwoot Integration Settings access


