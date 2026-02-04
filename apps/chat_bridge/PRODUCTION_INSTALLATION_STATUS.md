# Chat Bridge Production Installation Status

**Date:** November 11, 2025  
**Site:** erp.visualgraphx.com  
**Status:** ✅ **Code Complete, Installation Blocked by Pre-Existing Issue**

---

## ✅ Completed Implementation

### Phase 1: Pre-Installation Safety Checks ✅
- ✅ Verified all DocTypes have `"custom": 1` and `"module": "chat_bridge"`
- ✅ Fixed permissions - removed "All" role from Chatwoot User Token (System Manager only)
- ✅ All DocTypes verified with System Manager-only permissions

### Phase 2: Feature Flags & Permission Controls ✅

#### 2.1 Chatwoot Integration Settings DocType ✅
- ✅ Added `enabled` checkbox (master switch, default: 0)
- ✅ Added `enable_dashboard` checkbox (default: 0)
- ✅ Added `enable_api` checkbox (default: 0)
- ✅ Added `enable_sync` checkbox (default: 0)
- ✅ All permissions remain System Manager only

**File:** `chat_bridge/doctype/chatwoot_integration_settings/chatwoot_integration_settings.json`

#### 2.2 Desktop Module Visibility ✅
- ✅ Added permission check for System Manager role
- ✅ Checks `enabled` flag before displaying module
- ✅ Module hidden if user lacks permission or integration disabled

**File:** `chat_bridge/config/desktop.py`

#### 2.3 Web Route Permission Checks ✅
- ✅ Added System Manager permission check
- ✅ Checks `enabled` and `enable_dashboard` flags
- ✅ Returns 403 if unauthorized or disabled

**File:** `chat_bridge/www/chatwoot_dashboard.py`

#### 2.4 API Endpoint Protection ✅
- ✅ All API endpoints check System Manager permission
- ✅ All endpoints check `enabled` and `enable_api` flags
- ✅ Returns error if disabled or unauthorized

**File:** `chat_bridge/api/rest_api.py`

#### 2.5 Webhook Protection ✅
- ✅ Webhook handler checks `enabled` and `enable_sync` flags
- ✅ Returns disabled status if flags not set
- ✅ All webhook handlers check flags before processing

**Files:**
- `chat_bridge/webhook/__init__.py`
- `chat_bridge/webhook/handlers.py`

### Phase 3: Installation Preparation ✅
- ✅ App files copied to container: `/home/frappe/frappe-bench/apps/chat_bridge`
- ✅ Added to production site's `apps.txt`: `sites/erp.visualgraphx.com/apps.txt`
- ✅ Created installation script: `install_doctypes.py`

---

## ⚠️ Installation Blocked

### Issue: Pre-Existing Production Problem
The production site has `frappe_search` and `next_crm` listed in `apps.txt` but these apps are not installed as Python packages. This causes **ALL** bench commands to fail with:

```
ModuleNotFoundError: No module named 'frappe_search'
ModuleNotFoundError: No module named 'next_crm'
```

**Impact:**
- `bench install-app` fails
- `bench migrate` fails
- `bench clear-cache` fails
- `bench reload-doctype` fails

**This is NOT caused by chat_bridge** - it's a pre-existing production issue.

---

## 🔧 Workaround Options

### Option 1: Fix Pre-Existing Apps First (Recommended)
1. Remove `frappe_search` and `next_crm` from `apps.txt` temporarily
2. Install `chat_bridge` using `bench install-app`
3. Restore `apps.txt` with all apps
4. Fix `frappe_search` and `next_crm` installation separately

### Option 2: Manual DocType Installation
Use the provided `install_doctypes.py` script via bench console:
```bash
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com console"
# Then run:
exec(open('/home/frappe/frappe-bench/apps/chat_bridge/install_doctypes.py').read())
```

### Option 3: Direct Database Import
Import DocType JSON files directly into the database (advanced, requires database access)

---

## ✅ Safety Features Implemented

### Multi-Layer Protection:
1. **Permission Layer:** Only System Managers can access
2. **Feature Flag Layer:** Master `enabled` flag controls everything
3. **Granular Flags:** Dashboard, API, and Sync can be enabled independently
4. **Default State:** All features disabled by default (safest)

### Rollback Options:
- **Instant Disable:** Set `enabled = 0` in settings (hides module completely)
- **Remove App:** `bench --site erp.visualgraphx.com remove-app chat_bridge`
- **Full Restore:** Use backup from `E:\Docker\Frappe\backups\erp_visualgraphx_com_pre_chatwoot_20251111\`

---

## 📋 Next Steps

1. **Fix Pre-Existing Issue:** Resolve `frappe_search` and `next_crm` module errors
2. **Complete Installation:** Run `bench install-app chat_bridge` once bench commands work
3. **Test Installation:** Verify DocTypes created and accessible
4. **Progressive Rollout:**
   - Phase 4A: Enable dashboard only (`enabled=1`, `enable_dashboard=1`)
   - Phase 4B: Enable API access (`enable_api=1`)
   - Phase 4C: Enable sync (`enable_sync=1`)

---

## 📁 Files Modified

### Core Files:
1. ✅ `chat_bridge/doctype/chatwoot_integration_settings/chatwoot_integration_settings.json` - Feature flags
2. ✅ `chat_bridge/doctype/chatwoot_user_token/chatwoot_user_token.json` - Permissions fixed
3. ✅ `chat_bridge/config/desktop.py` - Permission checks
4. ✅ `chat_bridge/www/chatwoot_dashboard.py` - Permission + flag checks
5. ✅ `chat_bridge/api/rest_api.py` - Permission + flag checks
6. ✅ `chat_bridge/webhook/__init__.py` - Flag checks
7. ✅ `chat_bridge/webhook/handlers.py` - Flag checks in all handlers

### Installation Files:
- ✅ `install_doctypes.py` - Manual installation script
- ✅ `sites/erp.visualgraphx.com/apps.txt` - App registration

---

## ✅ Verification Checklist

- [x] All feature flags added to DocType
- [x] Permission checks in desktop.py
- [x] Permission checks in web routes
- [x] Permission checks in API endpoints
- [x] Flag checks in webhook handlers
- [x] App files copied to container
- [x] App added to site's apps.txt
- [x] Backup created before changes
- [ ] DocTypes installed in database (blocked)
- [ ] Module visible to System Managers (blocked)
- [ ] Feature flags functional (blocked)

---

## 🎯 Success Criteria

Once installation completes:
- ✅ Production site remains fully functional
- ✅ Only System Managers see Chatwoot module
- ✅ Feature flags work correctly
- ✅ Dashboard accessible when enabled
- ✅ API accessible when enabled
- ✅ Sync disabled by default
- ✅ Can disable entire integration instantly via flag

**Status:** All code complete, waiting for production environment fix to complete installation.


