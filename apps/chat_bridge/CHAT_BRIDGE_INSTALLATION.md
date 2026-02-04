# Chat Bridge - Installation & Integration Guide

## Overview

**Chat Bridge** is a unified chat integration for ERPNext that connects Support, CRM, and NextCRM modules. It was created by renaming and enhancing the Chatwoot Bridge to provide seamless chat integration across all customer touchpoints.

## What Changed

### Renaming Complete
- ✅ App renamed: `chatwoot_bridge` → `chat_bridge`
- ✅ Module renamed: `chatwoot_bridge` → `chat_bridge`
- ✅ All DocTypes renamed:
  - `Chatwoot Conversation` → `Chat Conversation`
  - `Chatwoot Message` → `Chat Message`
  - `Chatwoot Integration Settings` → `Chat Integration Settings`
  - `Chatwoot Contact Mapping` → `Chat Contact Mapping`
  - `Chatwoot Conversation Mapping` → `Chat Conversation Mapping`
  - `Chatwoot Conversation Label` → `Chat Conversation Label`
  - `Chatwoot User Token` → `Chat User Token`
- ✅ All Python files, classes, and functions updated
- ✅ All JavaScript files updated
- ✅ All JSON, HTML, and CSS files updated

### CRM Integration Added
- ✅ **Customer** field: Link to Customer DocType for order/billing history
- ✅ **Lead** field: Link to Lead DocType for sales pipeline (already existed, enhanced)
- ✅ **Issue** field: Link to Issue DocType for support ticket tracking
- ✅ **Contact** field: Link to Contact DocType (already existed)
- ✅ All links properly configured in DocType JSON

### Support Workspace Integration
- ✅ Chat items added to Support workspace configuration
- ✅ Proper navigation and shortcuts configured
- ✅ Settings integrated into Support module

## Installation Steps

### Step 1: Install the App

```bash
# SSH into ERPNext container
docker exec -it erpnext-backend bash

# Navigate to bench directory
cd /workspace/development

# Install chat_bridge app
bench --site erp.visualgraphx.com install-app chat_bridge

# Restart bench to load new app
supervisorctl restart all
```

### Step 2: Run Migrations

```bash
# Run migrations to create DocTypes
bench --site erp.visualgraphx.com migrate

# Clear cache
bench --site erp.visualgraphx.com clear-cache

# Rebuild search index
bench --site erp.visualgraphx.com build-search-index
```

### Step 3: Configure Chat Integration

1. **Go to**: Support > Settings > Chat Integration Settings

2. **Configure**:
   - ✅ Enable Integration
   - ✅ Enable Dashboard
   - ✅ Enable API Access
   - ✅ Enable Bidirectional Sync
   - Set Chat Base URL: `https://msg.visualgraphx.com`
   - Set Default Account ID: `1`
   - Set Webhook Secret: (get from Chatwoot)

3. **Enable Syncing**:
   - ✅ Enable Contact Sync
   - ✅ Enable Conversation Sync
   - ✅ Enable Message Sync

### Step 4: Access Chat in Support Workspace

1. Go to: **Support Workspace**
2. You'll see new sections:
   - **Conversations** → Chat Conversations
   - **Settings** → Chat Settings
   - **Configuration** → Contact Mappings, Labels, Tokens

## Features

### 1. Unified Chat Conversations

**Path**: Support > Chat Conversations

**Features**:
- View all chat conversations in one place
- Real-time message sync from Chatwoot
- Assign conversations to users
- Set priority (None, Low, Medium, High, Urgent)
- Track status (Open, Pending, Snoozed, Resolved, Closed)

### 2. CRM Integration

**Customer Linking**:
- Link chat conversations to Customers
- View customer order history while chatting
- Access billing and payment information

**Lead Linking**:
- Convert chat visitors to Leads
- Track leads through sales pipeline
- Automatic lead scoring based on engagement

**Issue Creation**:
- Convert chats to support Issues
- Track SLA compliance
- Link to existing Issues for context

**Contact Linking**:
- Sync contacts between ERPNext and Chatwoot
- Maintain single source of truth
- Automatic contact creation from chat

### 3. Support Workspace Integration

**Quick Actions**:
- Create Issue from chat
- Assign to support agent
- Escalate to manager
- Mark as resolved

**Timeline View**:
- See all customer interactions in one place
- Chat messages + emails + calls + issues
- Complete conversation history

### 4. NextCRM Integration (Future)

**Planned Features**:
- Link to NextCRM Deals
- Track conversion from chat → lead → opportunity → deal
- Revenue attribution from chat conversations

## Usage Examples

### Example 1: Convert Chat to Support Issue

1. Open a Chat Conversation
2. Review the conversation
3. In the "CRM Integration" section:
   - Click "Create" next to "Support Issue"
   - Issue is auto-created with chat transcript
   - Issue is linked back to conversation
4. Track issue resolution in Support module

### Example 2: Link Chat to Existing Customer

1. Open a Chat Conversation
2. In "CRM Integration" section:
   - Select Customer from dropdown
   - System links conversation to customer
3. Click on customer link to view:
   - Order history
   - Outstanding invoices
   - Previous conversations

### Example 3: Convert Visitor to Lead

1. Customer starts chat (not logged in)
2. Agent qualifies them as potential lead
3. In "CRM Integration" section:
   - Click "Create" next to "Lead"
   - Lead is created with contact info from chat
   - Chat conversation is linked to lead
4. Sales team takes over in CRM module

## Architecture

### Data Flow

```
Chatwoot (External)
       ↓
   Webhooks
       ↓
Chat Bridge (chat_bridge)
       ↓
    ┌──────┼──────┐
    ↓      ↓      ↓
 Contact Customer Lead
    ↓      ↓      ↓
Communication  Issue
```

### Sync Strategy

**From Chatwoot → ERPNext**:
- Conversations synced every 5 minutes (scheduler)
- Messages synced in real-time (webhooks)
- Contacts created/updated automatically

**From ERPNext → Chatwoot**:
- Manual sync via "Sync to Chatwoot" button
- Automatic on Contact/Customer update (if enabled)

### Database Schema

**Chat Conversation** (Master DocType):
- chat_conversation_id (unique)
- account_id, inbox_id
- status, priority, assigned_to
- contact (Link to Contact)
- customer (Link to Customer)
- lead (Link to Lead)
- issue (Link to Issue)
- messages (Table: Chat Message)
- labels (Table: Chat Conversation Label)

## Permissions

### Default Roles

**System Manager**:
- Full access to all Chat DocTypes
- Configure integration settings
- Manage user tokens

**Support Team** (needs to be added):
- Read/Write Chat Conversations
- Create Issues from chats
- Assign conversations

**Sales Team** (needs to be added):
- Read Chat Conversations
- Link to Leads/Customers
- View chat history

### Adding Permissions

```bash
# In ERPNext
bench --site erp.visualgraphx.com console

# Add permissions
frappe.get_doc("DocType", "Chat Conversation").add_permission(
    role="Support Team",
    permlevel=0,
    read=1,
    write=1,
    create=1
)
frappe.db.commit()
```

## Troubleshooting

### Issue: Conversations not syncing

**Check**:
1. Is integration enabled? (Chat Integration Settings)
2. Is sync enabled? (Chat Integration Settings > Sync Settings)
3. Check scheduler: `bench doctor` (should show chat_conversation.sync)
4. Check logs: `bench --site erp.visualgraphx.com logs`

**Fix**:
```bash
# Manually trigger sync
bench --site erp.visualgraphx.com console

import frappe
from chat_bridge.customer_support.doctype.chat_conversation.sync import sync_chat_conversations
sync_chat_conversations()
```

### Issue: Webhooks not working

**Check**:
1. Webhook secret configured?
2. Chatwoot webhook endpoint: `https://erp.visualgraphx.com/api/method/chat_bridge.webhook.handlers.receive_webhook`
3. Check Chatwoot webhook logs

**Test**:
```bash
curl -X POST https://erp.visualgraphx.com/api/method/chat_bridge.webhook.handlers.receive_webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "conversation_created", "data": {}}'
```

### Issue: Permissions denied

**Fix**:
1. Go to: Setup > Permissions > Chat Conversation
2. Add role permissions for Support Team, Sales Team
3. Clear cache: `bench clear-cache`

## API Documentation

### Get Chat Conversations

```python
import frappe

# Get all open conversations
conversations = frappe.get_all(
    "Chat Conversation",
    filters={"status": "Open"},
    fields=["name", "contact_display", "last_message_at", "priority"]
)
```

### Create Issue from Chat

```python
# Get conversation
chat = frappe.get_doc("Chat Conversation", "CHAT-001")

# Create issue
issue = frappe.get_doc({
    "doctype": "Issue",
    "subject": f"Support request from {chat.contact_display}",
    "customer": chat.customer,
    "description": "Chat transcript:\n\n" + chat.get_transcript(),
    "priority": chat.priority
})
issue.insert()

# Link back to chat
chat.issue = issue.name
chat.save()
```

## Next Steps

1. **Configure Roles**: Add Support Team and Sales Team roles
2. **Set Permissions**: Grant appropriate access to Chat DocTypes
3. **Create Workspace Shortcuts**: Add Chat to Support Workspace homepage
4. **Train Users**: Show support team how to use Chat integration
5. **Monitor Performance**: Track conversion rates (chat → lead → customer)

## Support

For issues or questions:
- **Documentation**: `/apps/chat_bridge/README.md`
- **Logs**: `bench --site erp.visualgraphx.com logs`
- **GitHub**: Report issues on your internal repository

---

**Version**: 1.0.0
**Last Updated**: 2025-11-19
**Author**: VisualGraphX Development Team
