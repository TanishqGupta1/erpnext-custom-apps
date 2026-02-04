# Solution: DocType Import Issue

## Root Cause

The `frappe_search` and `next_crm` apps are causing bench commands to fail because Frappe tries to load their hooks when running any bench command, and the hooks fail to import.

## Immediate Workaround

**Try accessing the DocType directly via URL:**
```
https://erp.visualgraphx.com/app/chatwoot-integration-settings/new
```

Even if search doesn't work, the DocType might be accessible via direct URL.

## Proper Fix Needed

The `frappe_search` and `next_crm` apps need to be fixed so their hooks don't break bench commands. This is a pre-existing production issue that needs to be resolved.

## Alternative: Manual Database Import

If the URL doesn't work, we can import the DocTypes directly into the database using SQL, bypassing Frappe's validation entirely. This is a last resort but will work.

Let me know if the direct URL works, or if you want me to proceed with the SQL import method.


