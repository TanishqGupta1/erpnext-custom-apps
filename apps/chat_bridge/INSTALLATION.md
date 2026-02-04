# Chat Bridge Installation Guide

## Prerequisites

- ERPNext v15 running in Docker
- Access to ERPNext backend container
- Chatwoot instance running (production or test)

## Installation Steps

### 1. Access ERPNext Container

```bash
docker exec -it erpnext-backend bash
cd /home/frappe/frappe-bench
```

### 2. Create Test Site (Optional - for testing)

```bash
bench new-site test-chatwoot.localhost
```

### 3. Install App on Site

For test site:
```bash
bench --site test-chatwoot.localhost install-app chat_bridge
```

For production site:
```bash
bench --site erp.visualgraphx.com install-app chat_bridge
```

### 4. Migrate Database

```bash
bench --site [site-name] migrate
```

### 5. Configure Integration Settings

1. Go to Desk → Chatwoot Integration Settings
2. Set Chatwoot Base URL (e.g., `https://msg.visualgraphx.com`)
3. Set Default Account ID (usually `1`)
4. Set Webhook Secret (generate in Chatwoot admin panel)
5. Enable sync flags as needed

### 6. Add User API Tokens

For each ERPNext user who needs Chatwoot access:

1. Generate API token in Chatwoot (Profile Settings → API Access Token)
2. Create "Chatwoot User Token" record:
   - User: Select ERPNext user
   - Chatwoot User ID: User ID from Chatwoot
   - API Access Token: Paste token
   - Account ID: Chatwoot account ID

### 7. Configure Chatwoot Webhooks (Optional - for sync)

In Chatwoot admin panel:
1. Go to Settings → Integrations → Webhooks
2. Add webhook URL: `https://erp.visualgraphx.com/api/method/chat_bridge.webhook.handle`
3. Select events: conversation.created, conversation.updated, message.created, contact.created, contact.updated
4. Set webhook secret (must match Integration Settings)

### 8. Access Chatwoot Dashboard

1. Go to Desk → Customer Support → Chatwoot Dashboard
2. Dashboard should load with Chatwoot iframe

## Testing with Mock API

For isolated testing without touching production Chatwoot:

1. Start mock server:
```bash
cd E:\Docker\Frappe\apps\chat_bridge\tests\mock_chatwoot_api
pip install -r requirements.txt
python mock_server.py
```

2. Configure Integration Settings:
   - Base URL: `http://host.docker.internal:3001` (from Docker container)
   - Or `http://localhost:3001` (from host)

3. Use any API token (mock accepts all tokens)

## Verification

1. Check Desk page loads: Desk → Customer Support → Chatwoot Dashboard
2. Test API calls: Use REST API endpoints via browser console or Postman
3. Test webhooks: Send test webhook from Chatwoot (or mock server)

## Troubleshooting

### App not showing in Desk
- Clear browser cache (Ctrl+F5)
- Restart ERPNext containers: `docker-compose restart`

### API errors
- Verify API token is correct
- Check Chatwoot base URL is accessible
- Check account ID matches Chatwoot account

### Webhook not receiving events
- Verify webhook URL is correct
- Check webhook secret matches
- Check ERPNext logs: `bench --site [site-name] logs`

## Uninstallation

```bash
bench --site [site-name] uninstall-app chat_bridge
```

This removes the app but keeps data. To remove data:
```bash
bench --site [site-name] drop-site  # Only for test sites!
```

