# AI Communications Hub

**AI-First, omnichannel communications platform for ERPNext/Frappe**

## Overview

The AI Communications Hub handles customer conversations across 9 channels with 80% AI automation and 20% human oversight:

### Supported Channels
1. **Voice** - VAPI-powered phone calls
2. **Live Chat** - Chatwoot web widget
3. **WhatsApp** - Via Chatwoot/Twilio
4. **SMS** - Twilio integration
5. **Facebook Messenger** - Meta Graph API
6. **Instagram DMs** - Meta Graph API
7. **Twitter/X DMs** - Twitter API v2
8. **LinkedIn Messages** - LinkedIn API
9. **Email** - SendGrid integration

## Key Features

- **Unified Context Bus**: Single conversation thread across all channels
- **AI-Powered Responses**: 80% automated resolution with naga.ac LLM
- **Human-in-the-Loop (HITL)**: AI requests human guidance when needed
- **Takeover Mode**: Agents can assume full control of conversations
- **Knowledge Base**: RAG-powered responses using Qdrant vector database
- **Function Calling**: AI can lookup orders, create quotes, schedule appointments
- **Platform-Specific AI**: Adapts tone, length, and formatting per platform

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frappe ERP (Brain)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Communication Hub DocType (Master Record)           │  │
│  │  - customer_id, channel, status, ai_mode             │  │
│  │  - context, sentiment, intent                        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Communication Message DocType (Messages)            │  │
│  │  - hub_id, sender, content, timestamp                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                    n8n Workflow Engine                      │
│  - Channel normalization                                    │
│  - Webhook routing                                          │
│  - Message formatting                                       │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                     Channel Integrations                    │
│  VAPI │ Chatwoot │ Twilio │ Meta │ Twitter │ SendGrid      │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Development (Test Site)

```bash
# Access ERPNext container
docker exec -it erpnext-backend bash
cd /home/frappe/frappe-bench

# Install app
bench get-app https://github.com/visualgraphx/ai_comms_hub
bench --site test.localhost install-app ai_comms_hub

# Run migrations
bench --site test.localhost migrate
```

### Production

```bash
# Install on production site
bench --site erp.visualgraphx.com install-app ai_comms_hub
bench --site erp.visualgraphx.com migrate
```

## Configuration

### 1. LLM Provider (naga.ac)

Go to: **AI Communications Hub Settings**
- LLM API URL: `https://api.naga.ac/v1`
- API Key: `[your-naga-api-key]`
- Model: `gpt-4o-mini` (or other)
- Max Tokens: `500`
- Temperature: `0.7`

### 2. Voice AI (VAPI)

- VAPI API Key: `[your-vapi-key]`
- VAPI Phone Number: `[your-number]`
- Assistant ID: `[assistant-id]`

### 3. Qdrant Vector Database

- Qdrant URL: `http://qdrant:6333`
- Collection Name: `knowledge_base`
- Embedding Model: `text-embedding-ada-002`

### 4. Channel Credentials

Set up credentials for each channel:
- Chatwoot: API key, account ID
- Twilio: Account SID, Auth Token
- Meta (Facebook/Instagram): Access token, page ID
- Twitter: API key, API secret, bearer token
- SendGrid: API key, verified sender email

## Usage

### Human-in-the-Loop (HITL) Workspace

Go to: **Desk → HITL Workspace**

View conversations where AI needs guidance:
- Review AI's proposed response
- Provide guidance or corrections
- AI continues conversation with your input

### Takeover Console

Go to: **Desk → Takeover Console**

Fully control conversations:
- View real-time AI interactions
- Take over at any time
- AI becomes your assistant (drafts, lookups, summaries)
- Hand back to AI when ready

### Analytics Dashboard

Go to: **Desk → Communications Analytics**

View metrics:
- AI resolution rate (target: >80%)
- Response time (target: <3 seconds)
- Customer satisfaction (target: >4.0/5.0)
- Channel breakdown
- Cost per conversation

## API Endpoints

### REST API

```python
# Get conversation
GET /api/resource/Communication Hub/{hub_id}

# Send message
POST /api/method/ai_comms_hub.api.send_message
{
  "hub_id": "COMM-HUB-0001",
  "content": "Hello, how can I help?",
  "sender_type": "Agent"
}

# Get conversation history
GET /api/method/ai_comms_hub.api.get_conversation_history?hub_id=COMM-HUB-0001
```

### Webhooks

Register webhooks for real-time events:

```python
# Incoming message
POST /api/method/ai_comms_hub.webhooks.voice.handle_vapi_webhook
POST /api/method/ai_comms_hub.webhooks.social.handle_facebook_webhook
POST /api/method/ai_comms_hub.webhooks.email_handler.handle_sendgrid_webhook
```

## DocTypes

### Communication Hub
Master conversation record across all channels

**Fields**:
- `customer` (Link to Customer)
- `channel` (Select: Voice, Chat, WhatsApp, SMS, Facebook, Instagram, Twitter, LinkedIn, Email)
- `status` (Select: Open, In Progress, Resolved, Closed)
- `ai_mode` (Select: Autonomous, HITL, Takeover, Manual)
- `context` (Long Text: Conversation summary)
- `sentiment` (Select: Positive, Neutral, Negative)
- `intent` (Data: Classified intent)
- `assigned_to` (Link to User)

### Communication Message
Individual messages within conversations

**Fields**:
- `communication_hub` (Link to Communication Hub)
- `sender_type` (Select: Customer, AI, Agent)
- `sender_name` (Data)
- `content` (Long Text)
- `timestamp` (Datetime)
- `is_function_call` (Check)
- `function_name` (Data)
- `function_result` (Long Text)

## Development

### Running Tests

```bash
bench --site test.localhost run-tests --app ai_comms_hub
```

### Code Style

```bash
# Format code
black ai_comms_hub/

# Lint
pylint ai_comms_hub/
```

## Architecture Decisions

1. **Why Frappe as the "Brain"?**
   - Single source of truth for customer data
   - Built-in CRM, order management, products
   - Native workflow engine
   - PostgreSQL for reliable data storage

2. **Why n8n for workflows?**
   - Visual workflow editor
   - 500+ pre-built integrations
   - Self-hosted (no vendor lock-in)
   - Easy to modify without code changes

3. **Why naga.ac instead of OpenAI?**
   - OpenAI-compatible API (drop-in replacement)
   - 50% cost savings
   - Same models (gpt-4o, gpt-4o-mini)
   - Better for production budgets

4. **Why Qdrant for vector search?**
   - Fast similarity search
   - Self-hosted option
   - Production-ready
   - Better than storing embeddings in PostgreSQL

## Roadmap

- **Phase 0**: Foundation & Setup (Week 1-2) ✅
- **Phase 1**: Voice AI (Week 3-4)
- **Phase 2**: HITL & Takeover (Week 5-6)
- **Phase 3**: All 9 Channels (Week 7-10)
- **Phase 4**: Intelligence (Week 11-13)
- **Phase 5**: Advanced Features (Week 14-17)

## Support

- Documentation: [docs/](./docs/)
- Issues: [GitHub Issues](https://github.com/visualgraphx/ai_comms_hub/issues)
- Email: support@visualgraphx.com

## License

MIT License - See [LICENSE](./LICENSE) file

---

**Status**: Phase 0 - Foundation & Setup
**Last Updated**: 2025-01-24
