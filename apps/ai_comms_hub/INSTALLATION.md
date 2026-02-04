# AI Communications Hub - Installation Guide

## Prerequisites

Before installing, ensure you have:

- ✅ Frappe/ERPNext v15+ installed
- ✅ Docker and Docker Compose
- ✅ n8n workflow engine[]
- ✅ Qdrant vector database
- ✅ PostgreSQL database

## Quick Start (5 Steps)

### Step 1: Install the App

```bash
# Access ERPNext backend container
docker exec -it erpnext-backend bash
cd /home/frappe/frappe-bench

# Get the app from local path (already in apps/ directory)
bench --site erp.visualgraphx.com install-app ai_comms_hub

# Run migrations
bench --site erp.visualgraphx.com migrate
```

### Step 2: Configure Settings

Go to: **Desk → AI Communications Hub Settings**

**Required Settings:**

1. **LLM Provider (naga.ac)**
   - API URL: `https://api.naga.ac/v1`
   - API Key: `[your-naga-api-key]`
   - Model: `gpt-4o-mini`

2. **Qdrant (Vector Database)**
   - Qdrant URL: `http://qdrant:6333`
   - Collection: `knowledge_base`

**Optional (Configure as needed):**

3. **VAPI (Voice AI)** - If using voice
4. **Facebook/Instagram** - If using social media
5. **Twitter** - If using Twitter DMs
6. **SendGrid** - If using email
7. **Chatwoot** - If using live chat
8. **Twilio** - If using SMS/WhatsApp

### Step 3: Initialize Qdrant Collection

```bash
# Run Qdrant setup script
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && \
  bench --site erp.visualgraphx.com execute ai_comms_hub.api.rag.create_collection_if_not_exists"
```

### Step 4: Sync Knowledge Base

```bash
# Sync ERPNext products to knowledge base
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && \
  bench --site erp.visualgraphx.com execute ai_comms_hub.api.rag.sync_erpnext_knowledge"
```

### Step 5: Test the System

```bash
# Test LLM connection
docker exec erpnext-backend bash -c "cd /home/frappe/frappe-bench && \
  bench --site erp.visualgraphx.com execute ai_comms_hub.scripts.test_integrations.test_llm_connection"
```

## Detailed Installation

### Service Setup

#### 1. naga.ac (LLM Provider)

1. Sign up at https://naga.ac
2. Get API key from dashboard
3. Add to Settings: **AI Communications Hub Settings → LLM Provider**

#### 2. VAPI (Voice AI)

1. Sign up at https://vapi.ai
2. Create assistant with these settings:
   - Model: `gpt-4o-mini`
   - Voice: Choose voice (e.g., "alloy")
   - Functions: Copy from `config/vapi_functions.json`
3. Get:
   - API Key
   - Phone Number
   - Assistant ID
4. Configure webhook:
   - URL: `https://your-domain.com/api/method/ai_comms_hub.webhooks.voice.handle_vapi_webhook`
   - Events: All

#### 3. Facebook Messenger

1. Go to https://developers.facebook.com
2. Create app → Messenger product
3. Get Page Access Token
4. Configure webhook:
   - URL: `https://your-domain.com/api/method/ai_comms_hub.webhooks.social.handle_facebook_webhook`
   - Verify Token: (create random string)
   - Events: `messages`, `messaging_postbacks`
5. Add to Settings

#### 4. Instagram DMs

1. Same as Facebook (uses Meta Graph API)
2. Connect Instagram Business Account
3. Subscribe to `messages` event
4. Add credentials to Settings

#### 5. Twitter/X DMs

**Option A: Polling (Free Tier)**
- No webhook setup needed
- n8n polls every 2 minutes
- Create Twitter App: https://developer.twitter.com
- Get API keys

**Option B: Webhooks (Premium)**
- Create Twitter App
- Register webhook URL
- Configure CRC validation

#### 6. SendGrid (Email)

1. Sign up at https://sendgrid.com
2. Verify sending domain
3. Get API key
4. Configure Inbound Parse:
   - URL: `https://your-domain.com/api/method/ai_comms_hub.webhooks.email_handler.handle_sendgrid_webhook`
   - MX records:
     ```
     support.yourdomain.com → mx.sendgrid.net
     ```
5. Add to Settings

#### 7. Chatwoot (Live Chat)

1. Already installed at `msg.visualgraphx.com`
2. Get API key: Settings → API Access Tokens
3. Get Account ID from URL
4. Add to Settings

### n8n Workflow Setup

**Option 1: Import Pre-built Workflows**

```bash
# Copy workflow templates
docker exec n8n sh -c "mkdir -p /home/node/.n8n/workflows"

# Import each workflow (9 total)
docker cp e:/Docker/Frappe/apps/ai_comms_hub/config/n8n_workflows/*.json n8n:/home/node/.n8n/workflows/

# Restart n8n
docker restart n8n
```

**Option 2: Create Manually**

See [n8n_workflows/README.md](./config/n8n_workflows/README.md) for workflow templates.

### Database Optimization

```sql
-- Run these after installation for better performance
-- Access PostgreSQL
docker exec -it postgres psql -U postgres -d erpnext

-- Add indexes
CREATE INDEX idx_comm_hub_channel ON "tabCommunication Hub"(channel);
CREATE INDEX idx_comm_hub_created ON "tabCommunication Hub"(creation);
CREATE INDEX idx_comm_hub_status ON "tabCommunication Hub"(status);
CREATE INDEX idx_comm_hub_ai_mode ON "tabCommunication Hub"(ai_mode);
CREATE INDEX idx_comm_hub_customer ON "tabCommunication Hub"(customer);

CREATE INDEX idx_comm_msg_hub ON "tabCommunication Message"(communication_hub);
CREATE INDEX idx_comm_msg_created ON "tabCommunication Message"(timestamp);
CREATE INDEX idx_comm_msg_sender ON "tabCommunication Message"(sender_type);

-- Full-text search (optional but recommended)
ALTER TABLE "tabCommunication Message" ADD COLUMN content_tsv tsvector;
CREATE INDEX idx_comm_msg_fts ON "tabCommunication Message" USING gin(content_tsv);
```

## Configuration

### AI Behavior Settings

Go to: **AI Communications Hub Settings → AI Behavior Settings**

- **Autonomy Level**: 80% (AI handles 80%, escalates 20%)
- **Auto-Escalate on Negative**: ✓ Enabled
- **RAG Confidence Threshold**: 70%
- **Max AI Retries**: 3

### Role Permissions

Assign roles in ERPNext:

1. **Customer Support** role:
   - Access to Communication Hub
   - Access to HITL Workspace
   - Access to Takeover Console

2. **System Manager** role:
   - Full access to all features
   - Settings configuration

## Testing

### Test Voice Call

```bash
# Call VAPI phone number
# AI should answer and engage in conversation
```

### Test Email

```bash
# Send email to: support@yourdomain.com
# Check Communication Hub for new record
# AI should respond within 30 seconds
```

### Test Facebook

```bash
# Send message to Facebook page
# Check Communication Hub
# AI should respond
```

### Test Knowledge Base

```bash
# Ask AI about a product
# Example: "What's the price of [product]?"
# AI should query knowledge base and respond
```

## Monitoring

### Real-Time Dashboard

Go to: **Desk → Communications Analytics**

View:
- Active conversations
- AI resolution rate
- Response times
- Channel breakdown
- Cost per conversation

### Logs

```bash
# View Frappe logs
docker exec erpnext-backend tail -f /home/frappe/frappe-bench/logs/frappe.log

# View n8n logs
docker logs -f n8n

# View Qdrant logs
docker logs -f qdrant
```

## Troubleshooting

### Issue: LLM not responding

**Check:**
1. API key is correct in Settings
2. naga.ac account has credits
3. Check logs: `/home/frappe/frappe-bench/logs/frappe.log`

**Fix:**
```bash
# Test LLM connection
bench --site erp.visualgraphx.com execute ai_comms_hub.scripts.test_integrations.test_llm_connection
```

### Issue: Qdrant connection failed

**Check:**
1. Qdrant container is running: `docker ps | grep qdrant`
2. URL is correct in Settings
3. Collection exists

**Fix:**
```bash
# Recreate collection
bench --site erp.visualgraphx.com execute ai_comms_hub.api.rag.create_collection_if_not_exists
```

### Issue: Webhooks not working

**Check:**
1. Webhook URL is publicly accessible
2. SSL certificate is valid
3. Verify token matches

**Fix:**
```bash
# Test webhook manually
curl -X POST https://your-domain.com/api/method/ai_comms_hub.webhooks.voice.handle_vapi_webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### Issue: Messages not delivering

**Check:**
1. Platform credentials in Settings
2. Message delivery status in Communication Message
3. Frappe background jobs: `bench --site erp.visualgraphx.com doctor`

**Fix:**
```bash
# Retry failed messages
bench --site erp.visualgraphx.com execute ai_comms_hub.api.message.retry_failed_messages
```

## Maintenance

### Daily Tasks

```bash
# Sync knowledge base
bench --site erp.visualgraphx.com execute ai_comms_hub.api.rag.sync_erpnext_knowledge

# Cleanup old conversations (auto-runs via scheduler)
# Check: bench --site erp.visualgraphx.com console
# >>> frappe.enqueue("ai_comms_hub.tasks.daily.cleanup.cleanup_old_conversations")
```

### Weekly Tasks

```bash
# Generate analytics report
bench --site erp.visualgraphx.com execute ai_comms_hub.tasks.weekly.reports.generate_weekly_summary
```

### Backup

```bash
# Backup Frappe database
bench --site erp.visualgraphx.com backup --with-files

# Backup Qdrant collection
curl -X POST http://localhost:6333/collections/knowledge_base/snapshots
```

## Scaling

### Horizontal Scaling

1. **n8n Workers**: Scale to 5-10 workers
   ```yaml
   # docker-compose.yml
   n8n-worker:
     replicas: 5
   ```

2. **Frappe Background Workers**: Increase workers
   ```bash
   # In supervisor config
   [program:frappe-default-worker]
   numprocs=4
   ```

3. **Qdrant**: Use cluster mode for > 1M vectors

### Performance Tuning

1. **Enable caching**:
   - Redis cache for common queries
   - LLM response caching

2. **Database optimization**:
   - Regular VACUUM
   - Index maintenance

3. **Monitor costs**:
   - Set LLM budget alerts in naga.ac
   - Track usage per channel

## Security

### API Key Management

- ✅ All API keys stored encrypted in Settings
- ✅ Password fields in Frappe
- ✅ Never log API keys

### Webhook Security

- ✅ Signature verification for all webhooks
- ✅ HTTPS required for production
- ✅ Rate limiting per IP

### Data Privacy

- ✅ Customer data encrypted at rest
- ✅ Conversations can be deleted
- ✅ GDPR-compliant data export

## Support

- **Documentation**: `/apps/ai_comms_hub/docs/`
- **GitHub Issues**: https://github.com/visualgraphx/ai_comms_hub/issues
- **Email**: support@visualgraphx.com

## Next Steps

1. ✅ Complete installation
2. ⏳ Configure all channels
3. ⏳ Train AI with knowledge base
4. ⏳ Test with pilot users
5. ⏳ Monitor and optimize
6. ⏳ Scale to production

---

**Installation Status**: Ready for Testing
**Last Updated**: 2025-01-24
