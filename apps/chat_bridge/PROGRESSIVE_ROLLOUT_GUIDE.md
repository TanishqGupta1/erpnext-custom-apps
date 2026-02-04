# Chat Bridge Progressive Rollout Guide

**Complete step-by-step instructions for enabling Chat integration safely**

---

## Prerequisites

- ✅ You must be logged in as a **System Manager** user
- ✅ Chat Bridge app is installed (already done)
- ✅ You have access to `https://erp.visualgraphx.com`

---

## Phase 4A: Enable Dashboard Only (Read-Only View)

**Goal:** Enable the embedded Chatwoot dashboard iframe. No API calls or sync will occur.

### Step 1: Log In as System Manager

1. Go to `https://erp.visualgraphx.com`
2. Log in with a user account that has **System Manager** role
3. Verify you're logged in (check top-right corner for your username)

### Step 2: Create Chatwoot Integration Settings

1. **Open Search Bar:**
   - Click the **magnifying glass icon** (🔍) in the top menu bar
   - Or press `Ctrl + K` (Windows) or `Cmd + K` (Mac)

2. **Search for DocType:**
   - Type: `Chatwoot Integration Settings`
   - Select it from the dropdown

3. **Create New Record:**
   - Click the **"New"** button (top right)
   - Or press `Ctrl + N`

4. **Fill in Settings:**
   
   **Feature Flags Section:**
   - ✅ **Enable Integration** - Check this box (master switch)
   - ✅ **Enable Dashboard** - Check this box (for iframe view)
   - ❌ **Enable API Access** - Leave unchecked (for Phase 4B)
   - ❌ **Enable Bidirectional Sync** - Leave unchecked (for Phase 4C)
   
   **Configuration Section:**
   - **Chatwoot Base URL:** `https://msg.visualgraphx.com`
     - (Or your Chatwoot instance URL)
   - **Default Account ID:** `1`
     - (Your Chatwoot account ID - check Chatwoot admin panel if unsure)
   - **Webhook Secret:** Leave empty for now (needed for Phase 4C)

5. **Save:**
   - Click **"Save"** button (top right)
   - Or press `Ctrl + S`

### Step 3: Access the Dashboard

**Method 1: Via Module Menu**
1. Look in the left sidebar
2. You should now see **"Customer Support"** module
3. Click on it
4. Click **"Chatwoot Dashboard"**

**Method 2: Direct URL**
1. Navigate directly to: `https://erp.visualgraphx.com/chatwoot-dashboard`
2. Bookmark this URL for quick access

**Method 3: Search**
1. Press `Ctrl + K` (or `Cmd + K`)
2. Type: `Chatwoot Dashboard`
3. Select it from results

### Step 4: Verify Dashboard Works

**What You Should See:**
- ✅ Chatwoot dashboard embedded in an iframe
- ✅ Full Chatwoot interface visible
- ✅ You can interact with Chatwoot (if logged into Chatwoot)
- ✅ No errors in browser console

**What Should NOT Happen:**
- ❌ No API calls from ERPNext to Chatwoot
- ❌ No webhook activity
- ❌ No data synchronization

**Troubleshooting:**

**If module doesn't appear:**
- Verify you're logged in as System Manager
- Check that `enabled` flag is checked in settings
- Clear browser cache (Ctrl+F5)
- Check ERPNext logs: `docker logs erpnext-frontend --tail 50`

**If dashboard shows error:**
- Verify Chatwoot Base URL is correct
- Check that Chatwoot is accessible from ERPNext server
- Verify Default Account ID is correct
- Check browser console for errors (F12)

**If you see "Permission Denied":**
- Verify your user has System Manager role
- Check User permissions in ERPNext

### Step 5: Test Dashboard Functionality

1. **View Conversations:**
   - Navigate through Chatwoot interface
   - Open conversations
   - View messages

2. **Verify Read-Only:**
   - Try to send a message from ERPNext (should not work - API disabled)
   - Verify no ERPNext data appears in Chatwoot

3. **Test Multiple Users:**
   - Log in as different System Manager users
   - Verify they can all see the dashboard
   - Log in as non-System Manager user
   - Verify they CANNOT see the module

**Success Criteria for Phase 4A:**
- ✅ Dashboard loads and displays Chatwoot interface
- ✅ Only System Managers can access
- ✅ No API or sync activity
- ✅ No errors in logs

**When Ready:** Proceed to Phase 4B after testing dashboard for at least 24 hours.

---

## Phase 4B: Enable API Access (Manual Operations)

**Goal:** Enable API endpoints so ERPNext can make manual API calls to Chatwoot. Sync still disabled.

### Step 1: Edit Integration Settings

1. **Open Settings:**
   - Search for `Chatwoot Integration Settings` (Ctrl+K)
   - Open the existing record (should only be one)

2. **Enable API:**
   - Find **"Enable API Access"** checkbox
   - ✅ **Check it**
   - **Save** the record (Ctrl+S)

### Step 2: Verify API is Enabled

**Check Settings:**
- `enabled` = ✅ Checked
- `enable_dashboard` = ✅ Checked  
- `enable_api` = ✅ Checked (NEW)
- `enable_sync` = ❌ Unchecked

### Step 3: Test API Endpoints

**Option 1: Via ERPNext Console (Advanced)**

1. Go to: `https://erp.visualgraphx.com/app/console`
2. Run test command:
```python
import frappe
from chat_bridge.api.rest_api import get_conversations

# Test API call
result = get_conversations()
print(result)
```

**Option 2: Via Browser (Simple)**

1. Open browser developer tools (F12)
2. Go to Network tab
3. Navigate to Chatwoot Dashboard
4. Look for API calls to `/api/method/chat_bridge.api.rest_api.*`
5. Verify they return data (not errors)

**Option 3: Via Custom Script**

Create a custom script in ERPNext that calls the API:
```python
import frappe
from chat_bridge.api.rest_api import get_conversations

# This should work now
conversations = get_conversations()
frappe.msgprint(f"Found {len(conversations.get('data', []))} conversations")
```

### Step 4: Test API Functionality

**Test These Operations:**
1. **Get Conversations:** Should return list of conversations
2. **Get Contacts:** Should return list of contacts
3. **Get Messages:** Should return messages for a conversation

**What Should Work:**
- ✅ API calls from ERPNext to Chatwoot
- ✅ Manual data retrieval
- ✅ Viewing Chatwoot data in ERPNext

**What Should NOT Work:**
- ❌ Automatic sync/webhooks
- ❌ Bidirectional data flow
- ❌ Real-time updates

**Troubleshooting:**

**If API returns "not enabled" error:**
- Verify `enable_api` is checked
- Clear cache: `bench --site erp.visualgraphx.com clear-cache`
- Restart frontend: `docker-compose restart erpnext-frontend`

**If API returns authentication errors:**
- Check Chatwoot User Token records
- Verify API tokens are valid
- Check Chatwoot API credentials

**Success Criteria for Phase 4B:**
- ✅ API endpoints respond successfully
- ✅ Can retrieve Chatwoot data from ERPNext
- ✅ No automatic sync/webhook activity
- ✅ No errors in logs

**When Ready:** Proceed to Phase 4C after testing API for at least 24 hours.

---

## Phase 4C: Enable Full Sync (Bidirectional)

**Goal:** Enable webhooks and automatic bidirectional data synchronization.

### Step 1: Get Webhook Secret from Chatwoot

1. **Log into Chatwoot:**
   - Go to `https://msg.visualgraphx.com` (or your Chatwoot URL)
   - Log in as admin

2. **Navigate to Webhooks:**
   - Go to **Settings** → **Integrations** → **Webhooks**
   - Or go to: `https://msg.visualgraphx.com/app/settings/integrations/webhooks`

3. **Create Webhook (if not exists):**
   - Click **"Add Webhook"**
   - **Webhook URL:** `https://erp.visualgraphx.com/api/method/chat_bridge.webhook.handle`
   - **Events:** Select all events you want to sync:
     - ✅ `conversation.created`
     - ✅ `conversation.updated`
     - ✅ `message.created`
     - ✅ `contact.created`
     - ✅ `contact.updated`
   - **Save** the webhook

4. **Copy Webhook Secret:**
   - After creating webhook, Chatwoot will show a **secret key**
   - Copy this secret (you'll need it in next step)

### Step 2: Configure ERPNext Settings

1. **Edit Integration Settings:**
   - Search for `Chatwoot Integration Settings` (Ctrl+K)
   - Open the record

2. **Enable Sync:**
   - ✅ **Enable Bidirectional Sync** - Check this box
   - **Webhook Secret:** Paste the secret from Chatwoot
   - **Save** the record

3. **Configure Sync Options:**
   - ✅ **Enable Contact Sync** - Check if you want contacts synced
   - ✅ **Enable Conversation Sync** - Check if you want conversations synced
   - ✅ **Enable Message Sync** - Check if you want messages synced

### Step 3: Verify Webhook Endpoint

**Test Webhook URL:**
1. Open browser
2. Go to: `https://erp.visualgraphx.com/api/method/chat_bridge.webhook.handle`
3. Should see: `{"status": "disabled", "message": "..."}` (if sync not enabled) or webhook form

**Verify Endpoint is Accessible:**
- Webhook must be accessible from internet (not just localhost)
- If behind firewall, ensure port 443 is open
- Check ERPNext logs for webhook attempts

### Step 4: Test Webhook Reception

**Method 1: Manual Test (from Chatwoot)**

1. In Chatwoot, create a test conversation
2. Check ERPNext logs:
   ```bash
   docker logs erpnext-backend --tail 50 | grep webhook
   ```
3. Should see webhook received message

**Method 2: Check ERPNext Records**

1. After webhook fires, check:
   - **Chatwoot Contact Mapping** - Should see new contacts
   - **Chatwoot Conversation Mapping** - Should see new conversations
   - **Communication** records - Should see messages (if enabled)

**Method 3: Monitor Logs**

```bash
# Watch webhook logs in real-time
docker logs -f erpnext-backend | grep -i chatwoot
```

### Step 5: Verify Sync is Working

**Test Scenarios:**

1. **Create Contact in Chatwoot:**
   - Create new contact in Chatwoot
   - Check ERPNext → **Chatwoot Contact Mapping**
   - Should see new mapping record

2. **Create Conversation in Chatwoot:**
   - Start new conversation in Chatwoot
   - Check ERPNext → **Chatwoot Conversation Mapping**
   - Should see new mapping record

3. **Send Message in Chatwoot:**
   - Send message in Chatwoot conversation
   - Check ERPNext → **Communication** records
   - Should see new communication (if message sync enabled)

4. **Update Contact in Chatwoot:**
   - Update contact details in Chatwoot
   - Check ERPNext → **Contact** records
   - Should see updated data (if contact sync enabled)

### Step 6: Monitor Sync Activity

**Check Sync Status:**

1. **View Mapping Records:**
   - Go to **Chatwoot Contact Mapping** list
   - Check `last_synced` timestamps
   - Verify records are updating

2. **Check Logs:**
   ```bash
   # View recent sync activity
   docker logs erpnext-backend --tail 100 | grep -i "chatwoot\|sync"
   ```

3. **Monitor Errors:**
   - Check ERPNext error logs
   - Look for webhook failures
   - Verify API authentication

**Troubleshooting:**

**If webhooks not received:**
- Verify webhook URL is correct and accessible
- Check webhook secret matches
- Verify Chatwoot can reach ERPNext server
- Check ERPNext firewall/nginx configuration

**If sync not working:**
- Verify `enable_sync` is checked
- Check individual sync flags (contacts/conversations/messages)
- Verify webhook secret is correct
- Check ERPNext logs for errors

**If duplicate records:**
- Check sync direction settings
- Verify deduplication logic
- Review mapping records

**Success Criteria for Phase 4C:**
- ✅ Webhooks received successfully
- ✅ Contacts syncing (if enabled)
- ✅ Conversations syncing (if enabled)
- ✅ Messages syncing (if enabled)
- ✅ No duplicate records
- ✅ No errors in logs

---

## Rollback Procedures

### Instant Disable (Safest)

1. **Edit Chatwoot Integration Settings**
2. **Uncheck "Enable Integration"**
3. **Save**
4. Module disappears immediately, all features disabled

### Disable Specific Feature

- **Disable Dashboard:** Uncheck `enable_dashboard`
- **Disable API:** Uncheck `enable_api`
- **Disable Sync:** Uncheck `enable_sync`

### Complete Removal

```bash
# Remove app completely
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com remove-app chat_bridge"

# Restore from backup if needed
# See: E:\Docker\Frappe\backups\erp_visualgraphx_com_pre_chatwoot_20251111\RECOVERY_GUIDE.md
```

---

## Quick Reference

### Settings Location
- **DocType:** Chatwoot Integration Settings
- **Search:** `Ctrl+K` → "Chatwoot Integration Settings"

### Dashboard URL
- **Direct:** `https://erp.visualgraphx.com/chatwoot-dashboard`
- **Via Menu:** Customer Support → Chatwoot Dashboard

### Webhook URL
- **Endpoint:** `https://erp.visualgraphx.com/api/method/chat_bridge.webhook.handle`
- **Method:** POST
- **Events:** conversation.created, message.created, contact.created, etc.

### Feature Flags
- `enabled` - Master switch (must be on for anything to work)
- `enable_dashboard` - Show iframe dashboard
- `enable_api` - Allow API calls
- `enable_sync` - Enable webhooks and sync

### Permissions
- **Required Role:** System Manager
- **DocTypes:** All System Manager only
- **Module:** Only visible to System Managers

---

## Support & Troubleshooting

### Check Logs
```bash
# ERPNext backend logs
docker logs erpnext-backend --tail 100

# ERPNext frontend logs  
docker logs erpnext-frontend --tail 100

# Filter for Chatwoot
docker logs erpnext-backend | grep -i chatwoot
```

### Clear Cache
```bash
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com clear-cache"
```

### Restart Services
```bash
cd E:\Docker\Frappe
docker-compose restart erpnext-backend erpnext-frontend
```

### Verify Installation
```bash
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && bench --site erp.visualgraphx.com console" << 'PYEOF'
import frappe
doctypes = frappe.get_all('DocType', filters={'module': 'chat_bridge'}, fields=['name'])
print(f'Found {len(doctypes)} DocTypes:')
for dt in doctypes:
    print(f'  - {dt.name}')
PYEOF
```

---

## Success Checklist

### Phase 4A Complete When:
- [ ] Dashboard loads successfully
- [ ] Only System Managers can access
- [ ] No API/sync activity
- [ ] Tested for 24+ hours

### Phase 4B Complete When:
- [ ] API endpoints working
- [ ] Can retrieve Chatwoot data
- [ ] No sync/webhook activity
- [ ] Tested for 24+ hours

### Phase 4C Complete When:
- [ ] Webhooks received successfully
- [ ] Data syncing correctly
- [ ] No duplicate records
- [ ] No errors in logs
- [ ] Tested for 48+ hours

---

**Ready to start? Begin with Phase 4A!**


