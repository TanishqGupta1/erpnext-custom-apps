# API Reference

Complete API documentation for AI Communications Hub.

## Table of Contents

1. [Authentication](#authentication)
2. [Webhook Endpoints](#webhook-endpoints)
3. [REST API Endpoints](#rest-api-endpoints)
4. [Function Calling API](#function-calling-api)
5. [RAG Query API](#rag-query-api)
6. [Message Sending API](#message-sending-api)
7. [Analytics API](#analytics-api)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)

---

## Authentication

All API endpoints require authentication using one of these methods:

### Method 1: API Key (Recommended for n8n)

Include in request headers:

```http
Authorization: token <api_key>:<api_secret>
```

Generate API keys in Frappe:
1. Go to User list
2. Select user
3. Click "API Access" → "Generate Keys"

### Method 2: Session Authentication

For browser-based requests, use Frappe's session cookies.

### Method 3: OAuth Bearer Token

For external integrations:

```http
Authorization: Bearer <oauth_token>
```

---

## Webhook Endpoints

### Voice (VAPI) Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.voice.handle_vapi_webhook`

**Description:** Receives VAPI voice AI events (call started, function call, speech update, end-of-call).

**Headers:**
```http
Content-Type: application/json
X-VAPI-Secret: <webhook_secret>
```

**Request Body:**

```json
{
  "message": {
    "type": "call.started",
    "call": {
      "id": "call_abc123",
      "phoneNumberId": "phone_xyz789",
      "customer": {
        "number": "+15551234567"
      }
    }
  }
}
```

**Event Types:**
- `call.started` - New call initiated
- `function-call` - AI requests function execution
- `speech-update` - Customer spoke (transcript available)
- `end-of-call-report` - Call ended with summary

**Response:**

```json
{
  "success": true,
  "hub_id": "COMHUB-2025-00001",
  "message": "Call started event processed"
}
```

**Error Response:**

```json
{
  "success": false,
  "error": "Invalid webhook signature"
}
```

---

### Email (SendGrid Inbound Parse) Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.email.handle_sendgrid_inbound`

**Description:** Receives inbound emails via SendGrid Inbound Parse.

**Headers:**
```http
Content-Type: multipart/form-data
```

**Request Body (Form-Encoded):**

```
to=support@yourdomain.com
from=customer@example.com
subject=Question about my order
text=Hello, I need help with order #12345...
html=<p>Hello, I need help with order #12345...</p>
headers=Received: from mail.example.com...
Message-ID: <abc123@example.com>
In-Reply-To: <xyz789@yourdomain.com>
```

**Response:**

```json
{
  "success": true,
  "hub_id": "COMHUB-2025-00002",
  "is_reply": true,
  "intent": "order_inquiry"
}
```

---

### Chat (Chatwoot) Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.chat.handle_chatwoot_webhook`

**Description:** Receives Chatwoot chat events.

**Headers:**
```http
Content-Type: application/json
```

**Request Body:**

```json
{
  "event": "message_created",
  "conversation": {
    "id": 123,
    "inbox_id": 456
  },
  "message": {
    "id": 789,
    "content": "I need help with my account",
    "message_type": "incoming",
    "created_at": 1642944000
  },
  "sender": {
    "id": 101,
    "name": "John Doe",
    "email": "john@example.com",
    "phone_number": "+15551234567"
  }
}
```

**Response:**

```json
{
  "success": true,
  "hub_id": "COMHUB-2025-00003",
  "ai_response": "I'd be happy to help with your account. What do you need assistance with?"
}
```

---

### WhatsApp (Twilio) Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.whatsapp.handle_twilio_webhook`

**Description:** Receives WhatsApp messages via Twilio.

**Headers:**
```http
Content-Type: application/x-www-form-urlencoded
X-Twilio-Signature: <signature>
```

**Request Body (Form-Encoded):**

```
From=whatsapp:+15551234567
To=whatsapp:+14155238886
Body=Hello, can you help me?
MessageSid=SMxxxxxxxxxxxxxx
NumMedia=0
```

**Response (TwiML):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>I'd be happy to help! What do you need assistance with?</Message>
</Response>
```

---

### SMS (Twilio) Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.sms.handle_twilio_webhook`

**Description:** Receives SMS messages via Twilio.

**Headers:**
```http
Content-Type: application/x-www-form-urlencoded
X-Twilio-Signature: <signature>
```

**Request Body (Form-Encoded):**

```
From=+15551234567
To=+14155238886
Body=What's my order status?
MessageSid=SMxxxxxxxxxxxxxx
```

**Response (TwiML):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>Let me check your order status for you.</Message>
</Response>
```

---

### Facebook Messenger Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.facebook.handle_facebook_webhook`

**Description:** Receives Facebook Messenger events.

**Verification (GET):**

```http
GET /api/method/ai_comms_hub.webhooks.facebook.handle_facebook_webhook?hub.mode=subscribe&hub.verify_token=my_verify_token&hub.challenge=challenge_string
```

**Response:** Returns `hub.challenge` value

**Message Event (POST):**

```json
{
  "object": "page",
  "entry": [{
    "messaging": [{
      "sender": {"id": "123456789"},
      "recipient": {"id": "987654321"},
      "timestamp": 1642944000000,
      "message": {
        "mid": "m_abc123",
        "text": "Hi, I have a question"
      }
    }]
  }]
}
```

**Response:**

```json
{
  "success": true,
  "hub_id": "COMHUB-2025-00004"
}
```

---

### Instagram DM Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.instagram.handle_instagram_webhook`

**Description:** Receives Instagram direct messages.

**Structure:** Same as Facebook Messenger (uses Graph API)

**Echo Detection:** Bot's own messages have `is_echo: true` and are ignored.

---

### Twitter/X DM Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.twitter.handle_twitter_webhook`

**Description:** Receives Twitter direct messages (Premium API only).

**Note:** Free tier uses polling via n8n workflow (no webhook needed).

**Request Body:**

```json
{
  "direct_message_events": [{
    "type": "message_create",
    "id": "123456789",
    "created_timestamp": "1642944000000",
    "message_create": {
      "target": {"recipient_id": "987654321"},
      "sender_id": "123456789",
      "message_data": {
        "text": "Question about your services"
      }
    }
  }]
}
```

**Response:**

```json
{
  "success": true,
  "hub_id": "COMHUB-2025-00005"
}
```

---

### LinkedIn Messages Webhook

**Endpoint:** `POST /api/method/ai_comms_hub.webhooks.linkedin.handle_linkedin_webhook`

**Description:** Receives LinkedIn messages.

**Request Body:**

```json
{
  "eventType": "MESSAGE_EVENT",
  "conversationId": "conv_abc123",
  "messageId": "msg_xyz789",
  "from": "urn:li:person:123456",
  "createdAt": 1642944000000,
  "text": {
    "text": "Professional inquiry about your services"
  }
}
```

**Response:**

```json
{
  "success": true,
  "hub_id": "COMHUB-2025-00006"
}
```

---

## REST API Endpoints

### Get Communication Hub

**Endpoint:** `GET /api/resource/Communication Hub/<hub_id>`

**Description:** Retrieve communication hub details.

**Response:**

```json
{
  "data": {
    "name": "COMHUB-2025-00001",
    "channel": "WhatsApp",
    "customer": "John Doe",
    "status": "Open",
    "ai_mode": "Autonomous",
    "sentiment": "Positive",
    "last_message_at": "2025-01-24 15:30:00",
    "messages": [
      {
        "sender_type": "Customer",
        "message_text": "Hello!",
        "timestamp": "2025-01-24 15:00:00"
      },
      {
        "sender_type": "AI Agent",
        "message_text": "Hi! How can I help?",
        "timestamp": "2025-01-24 15:00:05",
        "rag_confidence": 0.92
      }
    ]
  }
}
```

---

### List Communication Hubs

**Endpoint:** `GET /api/resource/Communication Hub`

**Query Parameters:**

```
?filters=[["status","=","Open"]]
&fields=["name","channel","customer","status","creation"]
&limit_page_length=20
&order_by=creation desc
```

**Response:**

```json
{
  "data": [
    {
      "name": "COMHUB-2025-00001",
      "channel": "WhatsApp",
      "customer": "John Doe",
      "status": "Open",
      "creation": "2025-01-24 15:00:00"
    }
  ]
}
```

---

### Create Communication Hub

**Endpoint:** `POST /api/resource/Communication Hub`

**Request Body:**

```json
{
  "channel": "Email",
  "customer": "CUS-2025-00001",
  "email_from": "customer@example.com",
  "ai_mode": "Autonomous",
  "status": "Open"
}
```

**Response:**

```json
{
  "data": {
    "name": "COMHUB-2025-00007",
    "channel": "Email",
    "status": "Open"
  }
}
```

---

### Update Communication Hub

**Endpoint:** `PUT /api/resource/Communication Hub/<hub_id>`

**Request Body:**

```json
{
  "status": "Resolved",
  "resolution_notes": "Issue resolved via email"
}
```

**Response:**

```json
{
  "data": {
    "name": "COMHUB-2025-00007",
    "status": "Resolved"
  }
}
```

---

### Send Message

**Endpoint:** `POST /api/method/ai_comms_hub.api.functions.send_message`

**Description:** Send a message in an existing conversation.

**Request Body:**

```json
{
  "hub_id": "COMHUB-2025-00001",
  "message_text": "Thank you for your patience. Your order has shipped!",
  "sender_type": "Human Agent"
}
```

**Response:**

```json
{
  "message": {
    "success": true,
    "message_id": "MSG-2025-00123",
    "sent_at": "2025-01-24 15:35:00",
    "delivery_status": "sent"
  }
}
```

---

## Function Calling API

### Get Order Status

**Endpoint:** `POST /api/method/ai_comms_hub.api.functions.get_order_status`

**Description:** Retrieve order status for a customer.

**Request Body:**

```json
{
  "order_id": "ORD-2025-00001"
}
```

**Response:**

```json
{
  "message": {
    "order_id": "ORD-2025-00001",
    "status": "Shipped",
    "tracking_number": "1Z999AA10123456784",
    "estimated_delivery": "2025-01-26",
    "items": [
      {
        "item_name": "Product A",
        "quantity": 2,
        "status": "Shipped"
      }
    ]
  }
}
```

---

### Create Quote

**Endpoint:** `POST /api/method/ai_comms_hub.api.functions.create_quote`

**Description:** Create a quotation based on customer requirements.

**Request Body:**

```json
{
  "customer": "CUS-2025-00001",
  "items": [
    {
      "item_code": "PROD-001",
      "qty": 10
    },
    {
      "item_code": "PROD-002",
      "qty": 5
    }
  ],
  "notes": "Bulk order discount requested"
}
```

**Response:**

```json
{
  "message": {
    "quote_id": "QTN-2025-00001",
    "grand_total": 1250.00,
    "valid_till": "2025-02-24",
    "pdf_url": "https://yourdomain.com/api/method/frappe.utils.print_format.download_pdf?doctype=Quotation&name=QTN-2025-00001"
  }
}
```

---

### Search Knowledge Base

**Endpoint:** `POST /api/method/ai_comms_hub.api.functions.search_knowledge_base`

**Description:** Query the RAG knowledge base.

**Request Body:**

```json
{
  "query": "What is your return policy?",
  "top_k": 5,
  "min_score": 0.7
}
```

**Response:**

```json
{
  "message": {
    "results": [
      {
        "title": "Return Policy - Standard Items",
        "content": "We offer 30-day returns on all standard items...",
        "score": 0.94,
        "doc_id": "KB-2025-00012"
      },
      {
        "title": "Return Policy - Electronics",
        "content": "Electronics can be returned within 14 days...",
        "score": 0.88,
        "doc_id": "KB-2025-00034"
      }
    ],
    "query_confidence": 0.91
  }
}
```

---

### Get Product Info

**Endpoint:** `POST /api/method/ai_comms_hub.api.functions.get_product_info`

**Description:** Retrieve product details.

**Request Body:**

```json
{
  "item_code": "PROD-001"
}
```

**Response:**

```json
{
  "message": {
    "item_code": "PROD-001",
    "item_name": "Premium Widget",
    "description": "High-quality widget for professional use",
    "standard_rate": 125.00,
    "stock_qty": 87,
    "image_url": "https://yourdomain.com/files/prod-001.jpg"
  }
}
```

---

### Check Inventory

**Endpoint:** `POST /api/method/ai_comms_hub.api.functions.check_inventory`

**Description:** Check real-time inventory levels.

**Request Body:**

```json
{
  "item_code": "PROD-001",
  "warehouse": "Main Warehouse"
}
```

**Response:**

```json
{
  "message": {
    "item_code": "PROD-001",
    "warehouse": "Main Warehouse",
    "actual_qty": 87,
    "reserved_qty": 12,
    "available_qty": 75,
    "reorder_level": 20,
    "reorder_qty": 100
  }
}
```

---

### Create Support Ticket

**Endpoint:** `POST /api/method/ai_comms_hub.api.functions.create_support_ticket`

**Description:** Create a support ticket/issue.

**Request Body:**

```json
{
  "customer": "CUS-2025-00001",
  "subject": "Product defect - Widget not working",
  "description": "Customer reports widget stopped working after 2 days",
  "priority": "High",
  "hub_id": "COMHUB-2025-00001"
}
```

**Response:**

```json
{
  "message": {
    "issue_id": "ISS-2025-00045",
    "status": "Open",
    "assigned_to": "support@yourdomain.com",
    "expected_resolution": "2025-01-26"
  }
}
```

---

### Escalate to Human

**Endpoint:** `POST /api/method/ai_comms_hub.api.functions.escalate_to_human`

**Description:** Escalate conversation to human agent.

**Request Body:**

```json
{
  "hub_id": "COMHUB-2025-00001",
  "reason": "Negative Sentiment",
  "notes": "Customer is frustrated with shipping delay"
}
```

**Response:**

```json
{
  "message": {
    "escalated": true,
    "assigned_to": "agent@yourdomain.com",
    "escalation_time": "2025-01-24 15:40:00",
    "notification_sent": true
  }
}
```

---

## RAG Query API

### Query Vector Database

**Endpoint:** `POST /api/method/ai_comms_hub.api.rag.query_knowledge_base`

**Description:** Direct query to Qdrant vector database.

**Request Body:**

```json
{
  "query": "shipping international orders",
  "top_k": 10,
  "min_score": 0.6,
  "filters": {
    "category": "shipping"
  }
}
```

**Response:**

```json
{
  "message": {
    "results": [
      {
        "id": "vec_abc123",
        "score": 0.89,
        "payload": {
          "title": "International Shipping Guide",
          "content": "We ship to over 50 countries...",
          "category": "shipping",
          "doc_id": "KB-2025-00056"
        }
      }
    ],
    "total_results": 10,
    "query_time_ms": 45
  }
}
```

---

### Add to Knowledge Base

**Endpoint:** `POST /api/method/ai_comms_hub.api.rag.add_to_knowledge_base`

**Description:** Add new content to vector database.

**Request Body:**

```json
{
  "title": "New Product Launch Information",
  "content": "We are excited to announce the launch of our new premium product line...",
  "category": "products",
  "metadata": {
    "author": "Marketing Team",
    "published_date": "2025-01-24"
  }
}
```

**Response:**

```json
{
  "message": {
    "success": true,
    "doc_id": "KB-2025-00089",
    "vector_id": "vec_xyz789",
    "chunks_created": 3
  }
}
```

---

### Update Knowledge Base Entry

**Endpoint:** `PUT /api/method/ai_comms_hub.api.rag.update_knowledge_base`

**Description:** Update existing knowledge base content.

**Request Body:**

```json
{
  "doc_id": "KB-2025-00089",
  "content": "Updated content with new information...",
  "reindex": true
}
```

**Response:**

```json
{
  "message": {
    "success": true,
    "doc_id": "KB-2025-00089",
    "vectors_updated": 3
  }
}
```

---

### Delete from Knowledge Base

**Endpoint:** `DELETE /api/method/ai_comms_hub.api.rag.delete_from_knowledge_base`

**Description:** Remove content from vector database.

**Request Body:**

```json
{
  "doc_id": "KB-2025-00089"
}
```

**Response:**

```json
{
  "message": {
    "success": true,
    "vectors_deleted": 3
  }
}
```

---

## Message Sending API

### Send Platform-Specific Message

**Endpoint:** `POST /api/method/ai_comms_hub.api.send.send_platform_message`

**Description:** Send message via specific platform (bypasses normal flow).

**Request Body:**

```json
{
  "platform": "WhatsApp",
  "recipient": "+15551234567",
  "message_text": "Your order #12345 has been shipped!",
  "media_url": "https://example.com/tracking-map.jpg"
}
```

**Response:**

```json
{
  "message": {
    "success": true,
    "platform": "WhatsApp",
    "message_id": "wamid.abc123",
    "status": "sent",
    "sent_at": "2025-01-24 16:00:00"
  }
}
```

---

### Bulk Send Messages

**Endpoint:** `POST /api/method/ai_comms_hub.api.send.bulk_send_messages`

**Description:** Send messages to multiple recipients.

**Request Body:**

```json
{
  "platform": "SMS",
  "recipients": [
    "+15551234567",
    "+15559876543",
    "+15555555555"
  ],
  "message_text": "Flash sale: 50% off this weekend only!",
  "schedule_time": "2025-01-25 09:00:00"
}
```

**Response:**

```json
{
  "message": {
    "success": true,
    "total_recipients": 3,
    "queued": 3,
    "scheduled_for": "2025-01-25 09:00:00",
    "batch_id": "BATCH-2025-00001"
  }
}
```

---

## Analytics API

### Get Dashboard Metrics

**Endpoint:** `GET /api/method/ai_comms_hub.api.analytics.get_dashboard_data`

**Query Parameters:**

```
?date_from=2025-01-01&date_to=2025-01-31
```

**Response:**

```json
{
  "message": {
    "total_conversations": 1247,
    "ai_resolved": 892,
    "escalated": 143,
    "ai_resolution_rate": 71.5,
    "avg_response_time": 3.2,
    "escalation_rate": 11.5,
    "by_channel": {
      "WhatsApp": 387,
      "Email": 298,
      "Chat": 245,
      "Voice": 189,
      "SMS": 128
    },
    "by_sentiment": {
      "Positive": 623,
      "Neutral": 487,
      "Negative": 137
    },
    "top_intents": [
      {"intent": "order_inquiry", "count": 412},
      {"intent": "product_inquiry", "count": 298},
      {"intent": "support_request", "count": 187}
    ]
  }
}
```

---

### Get Conversation Analytics

**Endpoint:** `GET /api/method/ai_comms_hub.api.analytics.get_conversation_analytics`

**Query Parameters:**

```
?hub_id=COMHUB-2025-00001
```

**Response:**

```json
{
  "message": {
    "hub_id": "COMHUB-2025-00001",
    "total_messages": 12,
    "duration_minutes": 23,
    "avg_rag_confidence": 0.87,
    "sentiment_progression": [
      {"timestamp": "15:00:00", "sentiment": "Neutral", "score": 0.0},
      {"timestamp": "15:05:00", "sentiment": "Positive", "score": 0.6},
      {"timestamp": "15:10:00", "sentiment": "Positive", "score": 0.8}
    ],
    "intents_detected": ["order_inquiry", "shipping_inquiry"],
    "functions_called": ["get_order_status", "search_knowledge_base"]
  }
}
```

---

### Get Customer Insights

**Endpoint:** `GET /api/method/ai_comms_hub.api.analytics.get_customer_insights`

**Query Parameters:**

```
?customer=CUS-2025-00001
```

**Response:**

```json
{
  "message": {
    "customer": "CUS-2025-00001",
    "total_conversations": 8,
    "preferred_channel": "WhatsApp",
    "avg_sentiment": "Positive",
    "avg_resolution_time_hours": 2.4,
    "ai_resolution_rate": 87.5,
    "lifetime_value": 2450.00,
    "last_interaction": "2025-01-24 15:30:00"
  }
}
```

---

## Error Handling

### Error Response Format

All errors return JSON with this structure:

```json
{
  "exc_type": "ValidationError",
  "exception": "Invalid phone number format",
  "_server_messages": "[\"Error message\"]",
  "exc": "Traceback..."
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Request processed |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal error |
| 503 | Service Unavailable | Maintenance/overload |

### Common Error Messages

**"Invalid API key"**
- Check Authorization header format
- Verify API key is active in Frappe

**"Hub not found"**
- Verify hub_id exists
- Check user has access permission

**"Rate limit exceeded"**
- Wait for cooldown period (60 seconds)
- Reduce request frequency

**"LLM API timeout"**
- Increase timeout setting
- Check naga.ac API status
- Try backup model

**"Vector database connection failed"**
- Verify Qdrant is running
- Check network connectivity
- Verify credentials

---

## Rate Limiting

### Limits

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Webhooks | 1000/min | Per IP |
| REST API | 60/min | Per user |
| Function Calls | 30/min | Per conversation |
| Analytics | 10/min | Per user |

### Rate Limit Headers

Responses include:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642944060
```

### Handling Rate Limits

When limit exceeded (429 response):

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "limit": 60,
  "window": 60
}
```

Wait `retry_after` seconds before retrying.

---

## SDK Examples

### Python

```python
import requests

API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
BASE_URL = "https://yourdomain.com"

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

# Query knowledge base
response = requests.post(
    f"{BASE_URL}/api/method/ai_comms_hub.api.functions.search_knowledge_base",
    headers=headers,
    json={
        "query": "return policy",
        "top_k": 5
    }
)

results = response.json()["message"]["results"]
for result in results:
    print(f"{result['title']}: {result['score']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_KEY = 'your_api_key';
const API_SECRET = 'your_api_secret';
const BASE_URL = 'https://yourdomain.com';

const headers = {
  'Authorization': `token ${API_KEY}:${API_SECRET}`,
  'Content-Type': 'application/json'
};

// Send message
async function sendMessage(hubId, text) {
  const response = await axios.post(
    `${BASE_URL}/api/method/ai_comms_hub.api.functions.send_message`,
    {
      hub_id: hubId,
      message_text: text,
      sender_type: 'Human Agent'
    },
    { headers }
  );
  return response.data.message;
}
```

### cURL

```bash
# Get order status
curl -X POST \
  https://yourdomain.com/api/method/ai_comms_hub.api.functions.get_order_status \
  -H "Authorization: token your_api_key:your_api_secret" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-2025-00001"}'
```

---

## Webhook Testing

### Test with curl

```bash
# Test voice webhook
curl -X POST \
  http://localhost:8000/api/method/ai_comms_hub.webhooks.voice.handle_vapi_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "call.started",
      "call": {
        "id": "test_call_123",
        "customer": {"number": "+15551234567"}
      }
    }
  }'

# Test email webhook
curl -X POST \
  http://localhost:8000/api/method/ai_comms_hub.webhooks.email.handle_sendgrid_inbound \
  -F "to=support@yourdomain.com" \
  -F "from=test@example.com" \
  -F "subject=Test Email" \
  -F "text=This is a test message"
```

### Test from n8n

Use "Execute Workflow" button in n8n editor with sample data.

---

## Versioning

API Version: **v1** (current)

Version is included in endpoint path for future versions:

```
/api/v1/method/ai_comms_hub.webhooks.voice.handle_vapi_webhook
```

Current endpoints without version prefix default to v1.

---

## Support

For API support:
- API Documentation: This file
- Integration Testing: `scripts/test_integrations.py`
- Troubleshooting: [troubleshooting.md](troubleshooting.md)
- GitHub Issues: https://github.com/visualgraphx/ai_comms_hub/issues
