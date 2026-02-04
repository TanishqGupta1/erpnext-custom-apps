# Configuration Guide

Complete configuration guide for AI Communications Hub.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [LLM Configuration](#llm-configuration)
3. [Vector Database (Qdrant)](#vector-database-qdrant)
4. [Channel Integration Credentials](#channel-integration-credentials)
5. [n8n Middleware Setup](#n8n-middleware-setup)
6. [Business Rules](#business-rules)
7. [AI Behavior Settings](#ai-behavior-settings)
8. [Security Settings](#security-settings)
9. [Performance Tuning](#performance-tuning)

---

## Prerequisites

Before configuring AI Communications Hub, ensure:

- **Frappe v15+** or **ERPNext v15+** installed
- **Qdrant** vector database running (Docker or self-hosted)
- **n8n** workflow automation platform installed
- **naga.ac** API key (or OpenAI-compatible LLM provider)
- Platform-specific credentials for channels you want to enable

---

## LLM Configuration

Navigate to: **AI Communications Hub Settings**

### Basic LLM Settings

```
LLM Provider: naga.ac
API Base URL: https://api.naga.ac/v1
API Key: [Your naga.ac API key]
Model: naga-gpt-4o
Temperature: 0.7
Max Tokens: 1500
```

### Model Selection Guide

| Model | Use Case | Cost | Speed |
|-------|----------|------|-------|
| `naga-gpt-4o` | Production (recommended) | 50% of OpenAI | Fast |
| `naga-gpt-4o-mini` | High-volume/low-cost | 80% lower | Very Fast |
| `gpt-4o` | Fallback/testing | Standard | Fast |
| `gpt-3.5-turbo` | Budget option | Low | Very Fast |

### Temperature Settings

- **0.0-0.3**: Deterministic, factual responses (order status, FAQs)
- **0.5-0.7**: Balanced creativity (general support)
- **0.8-1.0**: Creative responses (marketing, engagement)

**Recommended**: `0.7` for general customer support

### Timeout and Retry

```
Request Timeout: 30 seconds
Max Retries: 3
Retry Delay: 2 seconds
```

### Function Calling

Ensure function calling is enabled for advanced AI features:

```
Enable Function Calling: ✓ Yes
Available Functions:
  - get_order_status
  - create_quote
  - search_knowledge_base
  - get_product_info
  - check_inventory
  - create_support_ticket
  - escalate_to_human
```

---

## Vector Database (Qdrant)

### Connection Settings

Navigate to: **AI Communications Hub Settings > RAG Configuration**

```
Qdrant Host: localhost (or your Qdrant server IP)
Qdrant Port: 6333
Qdrant API Key: [Leave blank for local, or your API key]
Collection Name: ai_comms_knowledge_base
Vector Size: 1536 (OpenAI embedding compatible)
Distance Metric: Cosine
```

### Running Qdrant with Docker

```bash
# Start Qdrant
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# Verify connection
curl http://localhost:6333/collections
```

### Initial Setup

Run the Qdrant setup script:

```bash
cd ~/frappe-bench/apps/ai_comms_hub
python ai_comms_hub/scripts/setup_qdrant.py
```

This will:
1. Check connection to Qdrant
2. Create collection with correct vector dimensions
3. Verify collection configuration
4. Sync initial knowledge base articles

### RAG Query Settings

```
Top K Results: 5
Minimum Similarity Score: 0.7
Context Window: 3000 characters
Reranking Enabled: ✓ Yes
```

**Minimum Score Guide:**
- **0.9+**: Exact matches only (strict)
- **0.7-0.9**: High relevance (recommended)
- **0.5-0.7**: Medium relevance (broader search)
- **<0.5**: Low relevance (too broad, may include noise)

---

## Channel Integration Credentials

### 1. Voice (VAPI)

Navigate to: **AI Communications Hub Settings > Voice Settings**

```
VAPI API Key: [Your VAPI API key]
VAPI Assistant ID: [Your assistant ID]
Phone Number: +1234567890
Webhook URL: https://yourdomain.com/api/method/ai_comms_hub.webhooks.voice.handle_vapi_webhook
Webhook Secret: [Generate a random secret]
```

**Setup Steps:**
1. Sign up at https://vapi.ai
2. Create an assistant in VAPI dashboard
3. Configure function calling endpoints
4. Copy API key and assistant ID
5. Set webhook URL in VAPI dashboard

### 2. Email (SendGrid)

Navigate to: **AI Communications Hub Settings > Email Settings**

```
SendGrid API Key: [Your SendGrid API key]
Inbound Parse Domain: inbound.yourdomain.com
From Email: support@yourdomain.com
From Name: Customer Support
```

**Inbound Parse Setup:**
1. Go to SendGrid Dashboard > Settings > Inbound Parse
2. Add hostname: `inbound.yourdomain.com`
3. Set destination URL: `https://yourdomain.com/api/method/ai_comms_hub.webhooks.email.handle_sendgrid_inbound`
4. Add MX record in DNS:
   ```
   MX 10 mx.sendgrid.net.
   ```

### 3. Chat (Chatwoot)

Navigate to: **AI Communications Hub Settings > Chat Settings**

```
Chatwoot Base URL: https://app.chatwoot.com
Chatwoot Account ID: [Your account ID]
Chatwoot API Access Token: [Your API token]
Chatwoot Inbox ID: [Your inbox ID]
Bot Agent Email: bot@yourdomain.com
```

**Setup Steps:**
1. In Chatwoot, go to Settings > Integrations > API
2. Create access token with `administrator` role
3. Copy account ID from URL (e.g., `/app/accounts/123/`)
4. Copy inbox ID from Inbox Settings
5. Create a bot agent user with email `bot@yourdomain.com`

### 4. WhatsApp (Twilio)

Navigate to: **AI Communications Hub Settings > WhatsApp Settings**

```
Twilio Account SID: [Your SID]
Twilio Auth Token: [Your auth token]
Twilio WhatsApp Number: +14155238886 (or your number)
Webhook URL: https://yourdomain.com/api/method/ai_comms_hub.webhooks.whatsapp.handle_twilio_webhook
```

**Twilio Sandbox Setup (Testing):**
1. Go to Twilio Console > Messaging > Try WhatsApp
2. Send "join [your-code]" to +1 415 523 8886 from your WhatsApp
3. Configure webhook in Twilio Console

**Production Setup:**
1. Request WhatsApp Business API access from Twilio
2. Complete Facebook Business verification
3. Purchase or port a phone number
4. Configure webhook URL

### 5. SMS (Twilio)

Navigate to: **AI Communications Hub Settings > SMS Settings**

```
Twilio Account SID: [Same as WhatsApp]
Twilio Auth Token: [Same as WhatsApp]
Twilio SMS Number: +1234567890
Webhook URL: https://yourdomain.com/api/method/ai_comms_hub.webhooks.sms.handle_twilio_webhook
```

### 6. Facebook Messenger

Navigate to: **AI Communications Hub Settings > Facebook Settings**

```
Facebook Page Access Token: [Your page token]
Facebook Verify Token: [Random string you create]
Facebook App Secret: [Your app secret]
Webhook URL: https://yourdomain.com/api/method/ai_comms_hub.webhooks.facebook.handle_facebook_webhook
```

**Setup Steps:**
1. Create Facebook App at https://developers.facebook.com
2. Add "Messenger" product
3. Generate page access token (Pages > [Your Page] > Generate Token)
4. Subscribe to webhooks:
   - Verify Token: Create a random string (e.g., `my_verify_token_12345`)
   - Callback URL: Your webhook URL
   - Subscribe to: `messages`, `messaging_postbacks`, `message_reads`

### 7. Instagram DMs

Navigate to: **AI Communications Hub Settings > Instagram Settings**

```
Instagram Access Token: [Your token]
Instagram Business Account ID: [Your account ID]
Webhook URL: https://yourdomain.com/api/method/ai_comms_hub.webhooks.instagram.handle_instagram_webhook
Verify Token: [Same as Facebook]
```

**Setup Steps:**
1. Use same Facebook App as Messenger
2. Add "Instagram" product
3. Connect Instagram Business Account
4. Subscribe to webhooks: `messages`, `messaging_postbacks`
5. Generate access token from Graph API Explorer

### 8. Twitter/X DMs

Navigate to: **AI Communications Hub Settings > Twitter Settings**

```
Twitter API Key: [Your API key]
Twitter API Secret: [Your API secret]
Twitter Access Token: [Your access token]
Twitter Access Token Secret: [Your token secret]
Twitter Bearer Token: [Your bearer token]
```

**Setup Options:**

**Option A: Polling (Free Tier)**
- Uses n8n schedule trigger (every 2 minutes)
- No webhook configuration needed
- Limited to recent DMs only

**Option B: Webhooks (Premium Tier)**
- Real-time DM delivery
- Requires Twitter Premium API ($100/month minimum)
- Configure webhook in Twitter Developer Portal

### 9. LinkedIn Messages

Navigate to: **AI Communications Hub Settings > LinkedIn Settings**

```
LinkedIn Client ID: [Your client ID]
LinkedIn Client Secret: [Your client secret]
LinkedIn Access Token: [Your access token]
LinkedIn Organization ID: [Your org ID]
```

**Setup Steps:**
1. Create LinkedIn App at https://www.linkedin.com/developers
2. Request "Messaging" permissions
3. Complete LinkedIn partner verification
4. Generate OAuth 2.0 access token
5. Configure webhook URL in app settings

---

## n8n Middleware Setup

### Installation

All n8n workflow templates are in: `ai_comms_hub/config/n8n_workflows/`

**Import workflows:**

```bash
# Via n8n CLI
n8n import:workflow --input=voice_workflow.json
n8n import:workflow --input=email_workflow.json
# ... repeat for all 9 channels
```

**Or via UI:**
1. Open n8n at http://localhost:5678
2. Go to Workflows > Import from File
3. Select each JSON file from `config/n8n_workflows/`

### Credential Configuration in n8n

For each workflow, configure credentials:

**HTTP Basic Auth (for Frappe API):**
```
Username: [Frappe user email]
Password: [Frappe user password]
```

**Platform Credentials:**
- Create credentials in n8n matching platform requirements
- Reference credential names in workflow nodes

### Webhook URLs

Set these URLs in platform dashboards:

| Channel | Platform Dashboard | Webhook URL |
|---------|-------------------|-------------|
| Voice | VAPI | `https://n8n.yourdomain.com/webhook/vapi-webhook` |
| Email | SendGrid | `https://n8n.yourdomain.com/webhook/sendgrid-inbound` |
| Chat | Chatwoot | `https://n8n.yourdomain.com/webhook/chatwoot-webhook` |
| WhatsApp | Twilio | `https://n8n.yourdomain.com/webhook/twilio-whatsapp` |
| SMS | Twilio | `https://n8n.yourdomain.com/webhook/twilio-sms` |
| Facebook | Facebook | `https://n8n.yourdomain.com/webhook/facebook-messenger` |
| Instagram | Facebook | `https://n8n.yourdomain.com/webhook/instagram-dm` |
| LinkedIn | LinkedIn | `https://n8n.yourdomain.com/webhook/linkedin-messages` |

**Twitter**: No webhook URL (uses polling schedule)

### Activate Workflows

After configuration:
1. Open each workflow in n8n
2. Click "Active" toggle at top right
3. Test webhook with sample payload
4. Monitor execution logs

---

## Business Rules

Navigate to: **AI Communications Hub Settings > Business Rules**

### Business Hours

```
Timezone: America/New_York
Business Hours:
  Monday-Friday: 9:00 AM - 6:00 PM
  Saturday: 10:00 AM - 4:00 PM
  Sunday: Closed

After Hours Behavior: AI Only
After Hours Message: "Our team is currently offline. Our AI assistant will help you, or you can leave a message for our team."
```

### Auto-Response Timing

```
Initial Response Delay: 2 seconds (appear natural)
Typing Indicator Duration: 1 second per 50 characters
Max Response Time: 30 seconds
```

### Conversation Auto-Close

```
Auto-Close After: 24 hours of inactivity
Send Closure Message: ✓ Yes
Closure Message: "This conversation has been automatically closed due to inactivity. Feel free to message us anytime!"
```

### Customer Identification

```
Auto-Create Customer: ✓ Yes (if not found)
Match By: Phone, Email, Social ID
Merge Duplicate Customers: ✓ Yes (manual review)
```

---

## AI Behavior Settings

Navigate to: **AI Communications Hub Settings > AI Behavior**

### AI Mode

```
Default AI Mode: Autonomous
Allow Mode Switching: ✓ Yes
```

**AI Modes:**
- **Autonomous**: AI handles everything, escalates only when needed
- **Human-in-the-Loop**: AI suggests responses, human approves
- **Human Takeover**: Human handles, AI disabled

### Escalation Rules

Configure when AI should escalate to human:

```
Escalation Triggers:
  ✓ Negative Sentiment (score < -0.5)
  ✓ Low Confidence (RAG score < 0.6)
  ✓ Customer Requests Human
  ✓ Refund/Cancellation Request
  ✓ VIP Customer (flagged in system)
  ✓ High Value Order (> $10,000)
  ✓ Repeated Issue (same topic > 3 messages)
  ✓ Complex Technical Issue
```

### Sentiment Analysis

```
Enable Sentiment Analysis: ✓ Yes
Sentiment Provider: LLM-based (no external API)
Negative Threshold: -0.5
Positive Threshold: 0.5
```

### Intent Detection

```
Enable Intent Detection: ✓ Yes
Intent Categories:
  - order_inquiry
  - product_inquiry
  - quote_request
  - support_request
  - complaint
  - refund_request
  - shipping_inquiry
  - general_question
```

### Response Style

```
Tone: Professional and Friendly
Formality: Medium
Emoji Usage: Minimal (chat/social only)
Length Preference: Concise (2-3 sentences)
```

### Platform-Specific Adjustments

| Platform | Tone | Max Length | Emoji |
|----------|------|------------|-------|
| Voice | Conversational | 2-3 sentences | None |
| Email | Formal | 3-5 paragraphs | None |
| WhatsApp | Casual | 1000 chars | Yes |
| SMS | Very concise | 160 chars | No |
| Twitter | Direct | 280 chars | Sometimes |
| Facebook | Friendly | 2000 chars | Yes |
| Instagram | Engaging | 1000 chars | Yes |
| LinkedIn | Professional | 1300 chars | No |
| Chat | Quick | 200-500 chars | Sometimes |

---

## Security Settings

Navigate to: **AI Communications Hub Settings > Security**

### API Security

```
Enable API Key Authentication: ✓ Yes
API Key: [Auto-generated, copy to n8n]
Rotate API Keys: Every 90 days
```

### Webhook Verification

```
Verify Webhook Signatures: ✓ Yes
Enable IP Whitelist: ✓ Yes (for n8n server)
Allowed IPs: 192.168.1.100, 10.0.0.50
```

### Data Privacy

```
Mask Sensitive Data: ✓ Yes
Sensitive Patterns:
  - Credit Card Numbers (regex: \d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})
  - SSN (regex: \d{3}-\d{2}-\d{4})
  - Email Addresses (in certain contexts)

PII Retention: 90 days (after conversation closed)
GDPR Compliance: ✓ Enabled
```

### Rate Limiting

```
Max Requests per Customer: 60 per minute
Max Requests per IP: 100 per minute
Cooldown Period: 60 seconds
```

---

## Performance Tuning

### Caching

```
Enable Response Caching: ✓ Yes
Cache TTL: 300 seconds (5 minutes)
Cache Similar Queries: ✓ Yes (90% similarity threshold)
```

### Database Optimization

```
Enable Query Caching: ✓ Yes
Index Optimization: Run weekly (automated task)
Archive Old Conversations: ✓ After 90 days
```

### LLM Optimization

```
Enable Streaming: ✓ Yes (for chat/email)
Batch Small Requests: ✓ Yes
Request Timeout: 30 seconds
```

### Vector Database

```
Qdrant Memory Limit: 2 GB
On-Disk Payload: ✓ Yes (save RAM)
Reindex Frequency: Weekly
```

### Monitoring

```
Enable Performance Monitoring: ✓ Yes
Log Level: INFO (ERROR for production)
Alert on API Failures: ✓ Yes
Alert Email: admin@yourdomain.com
```

---

## Testing Configuration

After completing setup, run integration tests:

```bash
cd ~/frappe-bench/apps/ai_comms_hub
python ai_comms_hub/scripts/test_integrations.py
```

This will test:
- LLM API connection
- Qdrant vector database
- All 9 channel integrations
- Webhook endpoints
- Function calling
- RAG queries

Expected output:
```
✓ LLM API: Connected (naga-gpt-4o)
✓ Qdrant: Connected (ai_comms_knowledge_base)
✓ Voice (VAPI): Webhook responding
✓ Email (SendGrid): API valid
✓ Chat (Chatwoot): Connected
✓ WhatsApp (Twilio): Number verified
✓ SMS (Twilio): Number verified
✓ Facebook: Page token valid
✓ Instagram: Access token valid
✓ Twitter: Bearer token valid
✓ LinkedIn: OAuth valid

All systems operational!
```

---

## Common Configuration Issues

### Issue: LLM requests timing out

**Solution:**
- Increase timeout to 60 seconds
- Reduce max_tokens to 1000
- Check naga.ac API status
- Switch to backup model

### Issue: Qdrant not connecting

**Solution:**
- Verify Docker container is running: `docker ps | grep qdrant`
- Check port 6333 is accessible
- Verify firewall rules
- Check Qdrant logs: `docker logs qdrant`

### Issue: Webhooks not receiving data

**Solution:**
- Verify n8n workflows are active
- Check webhook URLs match in platform dashboards
- Test with curl: `curl -X POST https://n8n.yourdomain.com/webhook/test -d '{"test": true}'`
- Check n8n execution logs

### Issue: High API costs

**Solution:**
- Enable response caching
- Reduce temperature (less creative = cheaper)
- Use naga-gpt-4o-mini for simple queries
- Implement smart routing (simple questions → mini model, complex → full model)

---

## Support

For configuration help:
- Documentation: `ai_comms_hub/docs/`
- Troubleshooting: See [troubleshooting.md](troubleshooting.md)
- GitHub Issues: https://github.com/visualgraphx/ai_comms_hub/issues
