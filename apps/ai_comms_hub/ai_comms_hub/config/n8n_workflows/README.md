# n8n Workflow Templates

This directory contains n8n workflow templates for all 9 communication channels supported by AI Communications Hub.

## Available Workflows

1. **voice_workflow.json** - VAPI voice call handler
2. **facebook_workflow.json** - Facebook Messenger handler
3. **instagram_workflow.json** - Instagram DM handler
4. **twitter_workflow.json** - Twitter DM handler (polling-based)
5. **email_workflow.json** - SendGrid Inbound Parse handler
6. **chat_workflow.json** - Chatwoot live chat handler
7. **whatsapp_workflow.json** - Twilio WhatsApp handler
8. **sms_workflow.json** - Twilio SMS handler
9. **linkedin_workflow.json** - LinkedIn Messages handler

## Installation

### Option 1: Import via n8n UI

1. Open n8n interface: `http://localhost:5678`
2. Click **Workflows** → **+ Add Workflow** → **Import from File**
3. Select the workflow JSON file
4. Configure credentials (see below)
5. Activate the workflow

### Option 2: Import via CLI

```bash
# Copy all workflows to n8n container
docker exec n8n sh -c "mkdir -p /home/node/.n8n/workflows"

docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/voice_workflow.json n8n:/home/node/.n8n/workflows/
docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/facebook_workflow.json n8n:/home/node/.n8n/workflows/
docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/instagram_workflow.json n8n:/home/node/.n8n/workflows/
docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/twitter_workflow.json n8n:/home/node/.n8n/workflows/
docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/email_workflow.json n8n:/home/node/.n8n/workflows/
docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/chat_workflow.json n8n:/home/node/.n8n/workflows/
docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/whatsapp_workflow.json n8n:/home/node/.n8n/workflows/
docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/sms_workflow.json n8n:/home/node/.n8n/workflows/
docker cp e:/Docker/Frappe/apps/ai_comms_hub/ai_comms_hub/config/n8n_workflows/linkedin_workflow.json n8n:/home/node/.n8n/workflows/

# Restart n8n
docker restart n8n
```

## Required Credentials

You need to configure the following credentials in n8n:

### 1. Frappe API Key (Required for all workflows)

**Type**: HTTP Header Auth

**Configuration**:
- Header Name: `Authorization`
- Value: `token <api_key>:<api_secret>`

**Getting API Key**:
```bash
# Generate API key in ERPNext
# Go to: User → API Keys → Generate Keys
```

### 2. Twitter OAuth2 (For Twitter workflow)

**Type**: OAuth2 API

**Configuration**:
- Authorization URL: `https://twitter.com/i/oauth2/authorize`
- Access Token URL: `https://api.twitter.com/2/oauth2/token`
- Client ID: Your Twitter App Client ID
- Client Secret: Your Twitter App Client Secret
- Scope: `dm.read dm.write`

### 3. Facebook/Instagram Access Token

**Note**: Facebook and Instagram workflows use direct token authentication in the webhook handler, not n8n credentials.

### 4. SendGrid (Email workflow)

**Note**: SendGrid Inbound Parse sends webhooks directly without authentication. Verify webhook signature in Frappe handler.

### 5. Chatwoot API

**Note**: Chatwoot webhooks are sent without authentication. Verify in Frappe handler.

### 6. Twilio (SMS/WhatsApp workflows)

**Note**: Twilio webhooks use request validation via signature. No n8n credential needed.

### 7. LinkedIn OAuth2

**Type**: OAuth2 API

**Configuration**:
- Authorization URL: `https://www.linkedin.com/oauth/v2/authorization`
- Access Token URL: `https://www.linkedin.com/oauth/v2/accessToken`
- Client ID: Your LinkedIn App Client ID
- Client Secret: Your LinkedIn App Client Secret
- Scope: `r_organization_social w_organization_social`

## Webhook URLs

After importing workflows, configure these webhook URLs in external platforms:

### Voice (VAPI)
```
https://your-n8n-domain.com/webhook/vapi-webhook
```

### Facebook Messenger
```
Webhook URL: https://your-n8n-domain.com/webhook/facebook-webhook
Verify Token: your_verify_token_here
```

### Instagram DMs
```
Webhook URL: https://your-n8n-domain.com/webhook/instagram-webhook
Verify Token: your_verify_token_here
```

### Twitter DMs
**Note**: Twitter workflow uses polling (no webhook URL needed for free tier)

### Email (SendGrid)
```
https://your-n8n-domain.com/webhook/sendgrid-inbound
```

### Chatwoot
```
https://your-n8n-domain.com/webhook/chatwoot-webhook
```

### WhatsApp (Twilio)
```
https://your-n8n-domain.com/webhook/twilio-whatsapp-webhook
```

### SMS (Twilio)
```
https://your-n8n-domain.com/webhook/twilio-sms-webhook
```

### LinkedIn Messages
```
https://your-n8n-domain.com/webhook/linkedin-webhook
```

## Workflow Details

### 1. Voice Workflow (VAPI)

**Trigger**: Webhook (POST)

**Events Handled**:
- `call.started` - New call initiated
- `function-call` - AI requests function execution
- `speech-update` - Real-time transcript updates
- `end-of-call-report` - Call summary with transcript

**Data Flow**:
1. Receive VAPI webhook
2. Switch on event type
3. Normalize event data
4. Forward to Frappe API
5. Return 200 OK response

**Configuration**:
- No special credentials needed (VAPI validates on their end)
- Ensure webhook URL is publicly accessible

### 2. Facebook Workflow

**Trigger**: Webhook (GET/POST)

**Events Handled**:
- Webhook verification (GET request)
- Message received
- Postback button clicks

**Data Flow**:
1. Check if verification request (GET)
   - If yes: Validate token and return challenge
   - If no: Process message
2. Parse entry.messaging array
3. Extract message or postback data
4. Forward to Frappe API
5. Return 200 OK response

**Configuration**:
- Update verify token in workflow code
- Subscribe to `messages` and `messaging_postbacks` events in Facebook App

### 3. Instagram Workflow

**Trigger**: Webhook (GET/POST)

**Events Handled**:
- Webhook verification (GET request)
- Message received
- Postback interactions
- Reply messages

**Data Flow**:
1. Check if verification request
2. Parse messaging events
3. Filter out echo messages (sent by bot)
4. Process message or postback
5. Forward to Frappe API

**Configuration**:
- Update verify token in workflow code
- Connect Instagram Business Account to Facebook App
- Subscribe to `messages` event

### 4. Twitter Workflow (Polling)

**Trigger**: Schedule (Every 2 minutes)

**Events Handled**:
- New direct messages

**Data Flow**:
1. Schedule trigger fires every 2 minutes
2. Call Twitter API v2 to get DMs
3. Filter out already-processed messages (using staticData)
4. Process new messages
5. Update last processed ID
6. Forward to Frappe API

**Configuration**:
- Configure Twitter OAuth2 credentials
- Adjust polling interval if needed (default: 2 minutes)
- For webhook-based (premium): Replace schedule trigger with webhook trigger

### 5. Email Workflow (SendGrid)

**Trigger**: Webhook (POST)

**Events Handled**:
- Inbound emails via SendGrid Inbound Parse

**Data Flow**:
1. Receive SendGrid webhook
2. Parse form-encoded email data
3. Extract headers (Message-ID, In-Reply-To, References)
4. Clean email content (remove quoted replies, signatures)
5. Classify intent (order, product, quote, support, complaint)
6. Forward to Frappe API

**Configuration**:
- Configure Inbound Parse in SendGrid
- Point MX records to SendGrid
- No authentication required (validate in Frappe)

### 6. Chat Workflow (Chatwoot)

**Trigger**: Webhook (POST)

**Events Handled**:
- `message_created` - New message in conversation

**Data Flow**:
1. Receive Chatwoot webhook
2. Parse conversation and message data
3. Filter for `message_created` events only
4. Filter for incoming messages only (skip outgoing)
5. Forward to Frappe API

**Configuration**:
- Configure webhook in Chatwoot settings
- Subscribe to `message_created` event
- Specify webhook URL

### 7. WhatsApp Workflow (Twilio)

**Trigger**: Webhook (POST)

**Events Handled**:
- Incoming WhatsApp messages
- Media attachments (MMS)

**Data Flow**:
1. Receive Twilio webhook
2. Parse form-encoded data
3. Extract phone numbers (remove `whatsapp:` prefix)
4. Parse media attachments (if any)
5. Forward to Frappe API
6. Return TwiML response

**Configuration**:
- Configure WhatsApp webhook in Twilio console
- Point to n8n webhook URL
- Returns empty TwiML `<Response></Response>` (Frappe handles replies)

### 8. SMS Workflow (Twilio)

**Trigger**: Webhook (POST)

**Events Handled**:
- Incoming SMS messages
- MMS with media attachments
- Opt-out/Opt-in keywords (STOP, START, etc.)

**Data Flow**:
1. Receive Twilio webhook
2. Parse form-encoded data
3. Check for opt-out keywords (STOP, STOPALL, UNSUBSCRIBE, etc.)
4. Check for opt-in keywords (START, YES, UNSTOP)
5. Forward to Frappe API with opt-out/opt-in flags
6. Return TwiML response

**Configuration**:
- Configure SMS webhook in Twilio console
- Point to n8n webhook URL
- Returns empty TwiML (Frappe handles replies)

### 9. LinkedIn Workflow

**Trigger**: Webhook (POST)

**Events Handled**:
- `MESSAGE_CREATED` - New message in conversation

**Data Flow**:
1. Receive LinkedIn webhook
2. Parse message data
3. Filter for `MESSAGE_CREATED` events only
4. Validate message has content
5. Forward to Frappe API

**Configuration**:
- Configure webhook in LinkedIn App
- Subscribe to messaging events
- Requires LinkedIn organization page

## Testing Workflows

### Test Voice Workflow
```bash
curl -X POST http://localhost:5678/webhook/vapi-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "call.started",
      "call": {
        "id": "test-call-123",
        "customer": {"number": "+1234567890"},
        "assistantId": "assistant-123"
      },
      "timestamp": "2025-01-24T12:00:00Z"
    }
  }'
```

### Test Facebook Workflow (Verification)
```bash
curl -X GET "http://localhost:5678/webhook/facebook-webhook?hub.mode=subscribe&hub.verify_token=your_verify_token_here&hub.challenge=test_challenge"
```

### Test Email Workflow
```bash
curl -X POST http://localhost:5678/webhook/sendgrid-inbound \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "from=customer@example.com&to=support@yourcompany.com&subject=Order%20Inquiry&text=Hello%2C%20I%20need%20help%20with%20my%20order"
```

## Monitoring

### View Workflow Executions

1. Go to n8n UI: `http://localhost:5678`
2. Click **Executions** in sidebar
3. Filter by workflow name
4. View execution details, input/output data, and errors

### Enable Execution Logging

In each workflow's settings:
- **Save Data Error Execution**: All
- **Save Data Success Execution**: All (or "On error")
- **Save Manual Executions**: Yes

### Check Logs

```bash
# View n8n logs
docker logs -f n8n

# View n8n worker logs
docker logs -f n8n-worker-1
docker logs -f n8n-worker-2
docker logs -f n8n-worker-3
```

## Troubleshooting

### Workflow not triggering

**Check**:
1. Workflow is activated (toggle in UI)
2. Webhook URL is publicly accessible
3. External platform is sending webhooks correctly
4. Check n8n logs for errors

**Fix**:
```bash
# Restart n8n
docker restart n8n

# Check webhook registrations
curl http://localhost:5678/webhook-test/vapi-webhook
```

### Credentials not working

**Check**:
1. Credentials are correctly configured in n8n
2. API keys are valid and not expired
3. Credentials have correct permissions/scopes

**Fix**:
1. Go to n8n UI → Settings → Credentials
2. Edit credential
3. Test connection
4. Save and re-test workflow

### Messages not reaching Frappe

**Check**:
1. Frappe backend is running: `docker ps | grep erpnext`
2. Frappe API endpoint is correct: `http://erpnext-backend:8000`
3. API authentication is working

**Fix**:
```bash
# Test Frappe API connection
docker exec n8n curl -X POST http://erpnext-backend:8000/api/method/ping \
  -H "Authorization: token <api_key>:<api_secret>"
```

### Twitter polling not working

**Check**:
1. OAuth2 credentials are valid
2. Schedule trigger is enabled
3. Static data context is being saved

**Fix**:
1. Re-authenticate Twitter OAuth2
2. Clear static data and restart workflow
3. Check Twitter API rate limits

### Webhook verification failing (Facebook/Instagram)

**Check**:
1. Verify token in workflow matches token in Facebook App
2. Webhook URL is correct
3. SSL certificate is valid (HTTPS required)

**Fix**:
1. Update verify token in workflow code
2. Re-save workflow
3. Re-verify webhook in Facebook App

## Performance Optimization

### Use n8n Workers

For high-volume workflows, use n8n worker mode:

```yaml
# docker-compose.yml
n8n-worker-1:
  image: n8nio/n8n
  environment:
    - EXECUTIONS_MODE=queue
    - QUEUE_BULL_REDIS_HOST=redis
  command: worker
```

### Batch Processing

For Twitter polling, enable batching:
- **Batch Size**: 10 messages
- **Batch Interval**: 1 second

### Reduce Logging

For production, reduce execution logging:
- **Save Data Error Execution**: All
- **Save Data Success Execution**: On error only

## Maintenance

### Update Workflows

1. Export current workflow as backup
2. Import updated workflow JSON
3. Re-configure credentials if needed
4. Test before activating

### Backup Workflows

```bash
# Export all workflows
docker exec n8n sh -c "tar -czf /tmp/n8n-workflows-backup.tar.gz /home/node/.n8n/workflows"
docker cp n8n:/tmp/n8n-workflows-backup.tar.gz ./n8n-workflows-backup.tar.gz
```

### Restore Workflows

```bash
# Restore workflows
docker cp ./n8n-workflows-backup.tar.gz n8n:/tmp/
docker exec n8n sh -c "cd /home/node/.n8n && tar -xzf /tmp/n8n-workflows-backup.tar.gz"
docker restart n8n
```

## Support

For issues or questions:
- Check n8n documentation: https://docs.n8n.io
- Check AI Communications Hub docs: `/apps/ai_comms_hub/docs/`
- Create GitHub issue: https://github.com/visualgraphx/ai_comms_hub/issues

---

**Status**: All 9 workflow templates ready for import
**Last Updated**: 2025-01-24
