# Chat Bridge for ERPNext

Complete integration of Chatwoot into ERPNext, allowing teams to access all Chatwoot features without leaving ERPNext.

## Features

- Embedded Chatwoot dashboard in ERPNext Desk
- Native CRM integration with Vue components
- Bidirectional data synchronization
- Real-time conversation updates
- Seamless authentication via API tokens

## Installation

### Development (Test Site)

```bash
# Access ERPNext container
docker exec -it erpnext-backend bash
cd /home/frappe/frappe-bench

# Create test site (if not exists)
bench new-site test-chatwoot.localhost

# Install app on test site
bench --site test-chatwoot.localhost install-app chat_bridge
```

### Production

```bash
# Install on production site
bench --site erp.visualgraphx.com install-app chat_bridge
```

## Configuration

1. Go to Desk → Chatwoot Integration Settings
2. Set Chatwoot base URL (e.g., `https://msg.visualgraphx.com`)
3. Set default account ID
4. Configure webhook secret
5. Enable sync flags as needed

## Testing

See `tests/mock_chatwoot_api/README.md` for mock server setup.

## Documentation

- [Integration Plan](../docs/chatwoot-erpnext-integration.plan.md)
- [API Reference](https://www.chatwoot.com/developers/api)

