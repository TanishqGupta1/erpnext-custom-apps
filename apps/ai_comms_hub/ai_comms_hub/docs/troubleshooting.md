# Troubleshooting Guide

Common issues and solutions for AI Communications Hub.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [LLM API Issues](#llm-api-issues)
3. [Vector Database Issues](#vector-database-issues)
4. [Channel Integration Issues](#channel-integration-issues)
5. [Webhook Issues](#webhook-issues)
6. [n8n Workflow Issues](#n8n-workflow-issues)
7. [Message Delivery Issues](#message-delivery-issues)
8. [AI Behavior Issues](#ai-behavior-issues)
9. [Performance Issues](#performance-issues)
10. [Data Issues](#data-issues)

---

## Installation Issues

### Issue: "Requires Frappe v15 or higher"

**Symptom:** Installation fails with version error

**Cause:** Running on older Frappe version

**Solution:**

```bash
# Check current version
cd ~/frappe-bench
bench version

# Upgrade to v15 (if on v14)
bench update --upgrade

# Or fresh install
bench init frappe-bench --frappe-branch version-15
```

---

### Issue: "Custom fields creation failed"

**Symptom:** Error during `after_install()` hook

**Cause:** Permission issues or Customer doctype not found

**Solution:**

```bash
# Run as Administrator
bench --site <site-name> console

# In console
frappe.set_user("Administrator")
from ai_comms_hub.setup.install import create_customer_custom_fields
create_customer_custom_fields()
frappe.db.commit()
```

---

### Issue: "Module not found: ai_comms_hub"

**Symptom:** Import errors after installation

**Cause:** App not added to sites/apps.txt

**Solution:**

```bash
# Add app to site
bench --site <site-name> install-app ai_comms_hub

# Rebuild
bench build

# Restart
bench restart
```

---

## LLM API Issues

### Issue: "Connection timeout to naga.ac"

**Symptom:** Requests to LLM hang and timeout

**Cause:** Network issues, API down, or slow response

**Solution:**

1. **Check API status:**
   ```bash
   curl -I https://api.naga.ac/v1/health
   ```

2. **Test with simple request:**
   ```bash
   curl https://api.naga.ac/v1/chat/completions \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "naga-gpt-4o-mini",
       "messages": [{"role": "user", "content": "test"}],
       "max_tokens": 10
     }'
   ```

3. **Increase timeout in settings:**
   - Go to AI Communications Hub Settings
   - Set Request Timeout to 60 seconds
   - Enable retries

4. **Use backup model:**
   - Change model to `gpt-3.5-turbo` temporarily
   - Update API Base URL to OpenAI if needed

---

### Issue: "Invalid API key"

**Symptom:** 401 Unauthorized errors

**Cause:** Wrong API key or expired key

**Solution:**

1. **Verify API key:**
   - Log in to naga.ac dashboard
   - Check API keys section
   - Regenerate if needed

2. **Update in Frappe:**
   - Go to AI Communications Hub Settings
   - Paste new API key
   - Save settings

3. **Test connection:**
   ```bash
   cd ~/frappe-bench/apps/ai_comms_hub
   python ai_comms_hub/scripts/test_integrations.py test_llm
   ```

---

### Issue: "Rate limit exceeded"

**Symptom:** 429 errors from LLM API

**Cause:** Too many requests in short time

**Solution:**

1. **Enable caching:**
   ```
   Settings > Performance > Enable Response Caching: Yes
   Cache TTL: 300 seconds
   ```

2. **Reduce concurrent requests:**
   ```
   Settings > Performance > Max Concurrent LLM Requests: 5
   ```

3. **Upgrade API plan:**
   - Check usage in naga.ac dashboard
   - Upgrade to higher tier if needed

---

### Issue: "Function calling not working"

**Symptom:** AI doesn't call functions (get_order_status, etc.)

**Cause:** Function schemas incorrect or model doesn't support function calling

**Solution:**

1. **Verify model supports function calling:**
   - Use `naga-gpt-4o` or `gpt-4o` (not mini versions)

2. **Check function schemas:**
   ```python
   # In Frappe console
   from ai_comms_hub.api.llm import get_available_functions
   functions = get_available_functions()
   print(functions)  # Should show all function schemas
   ```

3. **Test specific function:**
   ```python
   from ai_comms_hub.api.functions import get_order_status
   result = get_order_status(order_id="ORD-2025-00001")
   print(result)
   ```

---

## Vector Database Issues

### Issue: "Cannot connect to Qdrant"

**Symptom:** "Connection refused" errors

**Cause:** Qdrant not running or wrong host/port

**Solution:**

1. **Check if Qdrant is running:**
   ```bash
   docker ps | grep qdrant
   ```

2. **Start Qdrant if not running:**
   ```bash
   docker start qdrant

   # Or create new container
   docker run -d \
     --name qdrant \
     -p 6333:6333 \
     -v $(pwd)/qdrant_storage:/qdrant/storage \
     qdrant/qdrant:latest
   ```

3. **Verify connection:**
   ```bash
   curl http://localhost:6333/collections
   ```

4. **Check settings:**
   - AI Communications Hub Settings > RAG Configuration
   - Qdrant Host: localhost (or correct IP)
   - Qdrant Port: 6333

---

### Issue: "Collection not found"

**Symptom:** "Collection 'ai_comms_knowledge_base' does not exist"

**Cause:** Collection not created during setup

**Solution:**

```bash
# Run setup script
cd ~/frappe-bench/apps/ai_comms_hub
python ai_comms_hub/scripts/setup_qdrant.py

# Or create manually
curl -X PUT http://localhost:6333/collections/ai_comms_knowledge_base \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'
```

---

### Issue: "Low RAG confidence scores"

**Symptom:** All RAG queries return scores < 0.5

**Cause:** Poor knowledge base content or wrong embeddings

**Solution:**

1. **Check embedding model:**
   ```python
   # In Frappe console
   from ai_comms_hub.api.rag import generate_embedding
   text = "test product description"
   embedding = generate_embedding(text)
   print(len(embedding))  # Should be 1536
   ```

2. **Verify knowledge base content:**
   - Check Knowledge Base doctype
   - Ensure articles are well-written and comprehensive
   - Add more relevant articles

3. **Reindex knowledge base:**
   ```bash
   bench --site <site-name> console
   ```
   ```python
   from ai_comms_hub.api.rag import reindex_knowledge_base
   reindex_knowledge_base()
   ```

4. **Lower minimum score threshold:**
   - Settings > RAG Configuration
   - Minimum Similarity Score: 0.5 (from 0.7)

---

### Issue: "Vector database out of memory"

**Symptom:** Qdrant crashes or slow queries

**Cause:** Too many vectors in memory

**Solution:**

1. **Enable on-disk payload:**
   ```python
   # Update collection config
   import requests
   requests.patch(
     "http://localhost:6333/collections/ai_comms_knowledge_base",
     json={"on_disk_payload": True}
   )
   ```

2. **Increase Docker memory limit:**
   ```bash
   docker update --memory=4g qdrant
   docker restart qdrant
   ```

3. **Archive old vectors:**
   ```python
   # Run cleanup task manually
   from ai_comms_hub.tasks.daily.cleanup import cleanup_vector_database
   cleanup_vector_database()
   ```

---

## Channel Integration Issues

### Issue: "VAPI webhook not responding"

**Symptom:** Voice calls not creating conversations

**Cause:** Webhook URL incorrect or n8n workflow not active

**Solution:**

1. **Verify webhook URL in VAPI:**
   - Log in to VAPI dashboard
   - Check Assistant settings
   - Webhook URL should be: `https://n8n.yourdomain.com/webhook/vapi-webhook`

2. **Check n8n workflow:**
   ```bash
   # Access n8n
   curl http://localhost:5678/rest/workflows
   ```
   - Ensure "VAPI Voice Call Handler" workflow is Active

3. **Test webhook manually:**
   ```bash
   curl -X POST https://n8n.yourdomain.com/webhook/vapi-webhook \
     -H "Content-Type: application/json" \
     -d '{"message": {"type": "call.started", "call": {"id": "test"}}}'
   ```

4. **Check n8n logs:**
   ```bash
   docker logs n8n
   ```

---

### Issue: "SendGrid inbound emails not working"

**Symptom:** Emails sent to support@ don't create conversations

**Cause:** DNS MX record not set or Inbound Parse not configured

**Solution:**

1. **Verify MX record:**
   ```bash
   nslookup -type=MX inbound.yourdomain.com
   # Should show: mx.sendgrid.net
   ```

2. **Check Inbound Parse settings:**
   - Log in to SendGrid
   - Settings > Inbound Parse
   - Verify hostname and destination URL

3. **Test with email:**
   - Send test email to: support@inbound.yourdomain.com
   - Check n8n execution logs
   - Check SendGrid activity feed

4. **Verify Frappe endpoint:**
   ```bash
   curl -X POST https://yourdomain.com/api/method/ai_comms_hub.webhooks.email.handle_sendgrid_inbound \
     -F "to=support@yourdomain.com" \
     -F "from=test@example.com" \
     -F "text=test message"
   ```

---

### Issue: "Chatwoot messages not syncing"

**Symptom:** Chat messages don't appear in Communication Hub

**Cause:** Webhook not configured or API token invalid

**Solution:**

1. **Verify Chatwoot webhook:**
   - Chatwoot > Settings > Integrations > Webhooks
   - Add webhook: `https://n8n.yourdomain.com/webhook/chatwoot-webhook`
   - Subscribe to: `message_created`, `conversation_status_changed`

2. **Check API token:**
   ```bash
   curl https://app.chatwoot.com/api/v1/accounts/<account_id> \
     -H "api_access_token: <your_token>"
   ```

3. **Test webhook:**
   - Send test message in Chatwoot
   - Check n8n execution logs
   - Verify conversation created in Frappe

---

### Issue: "Twilio WhatsApp/SMS not sending"

**Symptom:** Outbound messages fail with 404 or 401 errors

**Cause:** Wrong Account SID, Auth Token, or phone number

**Solution:**

1. **Verify credentials:**
   ```bash
   curl -X GET "https://api.twilio.com/2010-04-01/Accounts/<SID>.json" \
     -u "<SID>:<AUTH_TOKEN>"
   ```

2. **Check phone number ownership:**
   - Twilio Console > Phone Numbers
   - Verify number is active and supports SMS/WhatsApp

3. **Test send:**
   ```bash
   curl -X POST "https://api.twilio.com/2010-04-01/Accounts/<SID>/Messages.json" \
     -u "<SID>:<AUTH_TOKEN>" \
     -d "From=+1234567890" \
     -d "To=+1555555555" \
     -d "Body=Test message"
   ```

4. **Update settings in Frappe:**
   - Settings > WhatsApp/SMS Settings
   - Paste correct SID and Auth Token
   - Save and test

---

### Issue: "Facebook/Instagram webhook verification failed"

**Symptom:** "The URL couldn't be validated" error in Facebook

**Cause:** Verify token mismatch or n8n workflow not responding to GET requests

**Solution:**

1. **Check n8n workflow handles GET:**
   - Open workflow in n8n editor
   - Webhook node should handle both GET and POST
   - GET should return `hub.challenge` parameter

2. **Test verification manually:**
   ```bash
   curl "https://n8n.yourdomain.com/webhook/facebook-messenger?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=CHALLENGE_STRING"
   # Should return: CHALLENGE_STRING
   ```

3. **Verify token match:**
   - Check token in Facebook App settings
   - Check token in n8n workflow Code node
   - Must be exact match (case-sensitive)

---

### Issue: "Twitter DMs not polling"

**Symptom:** No Twitter messages being received

**Cause:** n8n schedule trigger not active or API credentials invalid

**Solution:**

1. **Check n8n workflow active:**
   - Open "Twitter DM Poller" workflow
   - Ensure toggle is ON

2. **Verify Bearer Token:**
   ```bash
   curl -X GET "https://api.twitter.com/2/tweets/search/recent?query=test" \
     -H "Authorization: Bearer <YOUR_BEARER_TOKEN>"
   # Should return 200 OK
   ```

3. **Check polling frequency:**
   - n8n workflow Schedule Trigger
   - Should be every 2 minutes
   - Don't set too frequent (rate limits)

4. **Manually trigger:**
   - Click "Execute Workflow" in n8n editor
   - Check execution log for errors

---

## Webhook Issues

### Issue: "Webhook signature validation failed"

**Symptom:** 403 Forbidden errors on webhook endpoints

**Cause:** Incorrect webhook secret or signature algorithm

**Solution:**

1. **For Twilio webhooks:**
   ```python
   # In Frappe console
   from ai_comms_hub.utils.validators import validate_twilio_signature

   # Test validation
   signature = "provided_signature"
   url = "https://yourdomain.com/webhook"
   params = {"From": "+1234567890", "Body": "test"}

   is_valid = validate_twilio_signature(signature, url, params)
   print(is_valid)
   ```

2. **Disable validation temporarily (testing only):**
   - Settings > Security
   - Verify Webhook Signatures: No
   - Save and test
   - Re-enable after testing!

3. **Check webhook secret:**
   - Verify secret in platform dashboard matches Frappe settings
   - Regenerate secret if needed

---

### Issue: "Webhooks timing out"

**Symptom:** Platform shows webhook failures, timeout errors

**Cause:** Frappe processing takes too long (> 15 seconds)

**Solution:**

1. **Use background jobs for heavy processing:**
   ```python
   # In webhook handler
   @frappe.whitelist(allow_guest=True)
   def handle_webhook(**kwargs):
       # Quick validation
       if not validate_payload(kwargs):
           return {"error": "Invalid"}

       # Enqueue processing
       frappe.enqueue(
           "ai_comms_hub.webhooks.process_webhook",
           **kwargs,
           queue="short"
       )

       # Return immediately
       return {"success": True, "queued": True}
   ```

2. **Optimize LLM requests:**
   - Reduce max_tokens
   - Use faster model (naga-gpt-4o-mini)
   - Enable caching

3. **Increase timeout in platform:**
   - Some platforms allow webhook timeout configuration
   - Set to 30 seconds if possible

---

## n8n Workflow Issues

### Issue: "Workflow execution failed"

**Symptom:** Red error icon in n8n execution log

**Cause:** Various - check error message

**Solution:**

1. **Check execution details:**
   - Click on failed execution
   - Read error message
   - Check which node failed

2. **Common issues:**

   **"Connection refused" to Frappe:**
   ```bash
   # Check Frappe is running
   curl http://localhost:8000/api/method/ping

   # Check n8n can reach Frappe
   docker exec n8n curl http://host.docker.internal:8000/api/method/ping
   ```

   **"Invalid credentials":**
   - Check HTTP Basic Auth credential in n8n
   - Username should be full email (admin@example.com)
   - Password should be user's password

   **"Unexpected token" in Code node:**
   - Check JavaScript syntax
   - Use console.log() for debugging
   - Test code outside n8n first

3. **Test workflow step by step:**
   - Click "Execute Node" on each node individually
   - Verify data passes correctly between nodes

---

### Issue: "Workflow not triggering on webhook"

**Symptom:** Platform sends webhook but workflow doesn't execute

**Cause:** Webhook URL incorrect or workflow not active

**Solution:**

1. **Copy correct webhook URL:**
   - Open workflow in n8n
   - Click on Webhook node
   - Copy "Test URL" or "Production URL"
   - Use Production URL for live traffic

2. **Activate workflow:**
   - Toggle "Active" switch in top-right
   - Should be blue/green when active

3. **Check webhook history:**
   - Some platforms show webhook delivery history
   - Check if requests are reaching n8n
   - Look for 404 or 5xx errors

4. **Test with curl:**
   ```bash
   curl -X POST <webhook_url> \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

---

### Issue: "Data not mapping correctly"

**Symptom:** Wrong data sent to Frappe or missing fields

**Cause:** Incorrect expressions in Set nodes

**Solution:**

1. **Check node expressions:**
   - Use `{{$json.field_name}}` for current node output
   - Use `{{$node["Node Name"].json.field_name}}` for specific node

2. **Debug data structure:**
   - Add Set node before problematic node
   - Log full JSON: `{{JSON.stringify($json, null, 2)}}`
   - Execute and inspect output

3. **Use test mode:**
   - Click "Execute Workflow" with sample data
   - Inspect data at each node
   - Verify transformations are correct

---

## Message Delivery Issues

### Issue: "Messages not being sent"

**Symptom:** AI generates response but customer doesn't receive it

**Cause:** Platform API error or credentials issue

**Solution:**

1. **Check Communication Message records:**
   ```python
   # In Frappe console
   messages = frappe.get_all(
       "Communication Message",
       filters={"delivery_status": "Failed"},
       fields=["*"],
       limit=10
   )
   for msg in messages:
       print(f"{msg.name}: {msg.error_message}")
   ```

2. **Test platform API directly:**
   - Use platform's API testing tool
   - Send test message manually
   - Verify credentials work

3. **Check error logs:**
   ```bash
   # Frappe error log
   tail -f ~/frappe-bench/logs/error.log

   # n8n logs
   docker logs n8n -f
   ```

4. **Retry failed messages:**
   ```python
   # In Frappe console
   from ai_comms_hub.api.send import retry_failed_messages
   retry_failed_messages()
   ```

---

### Issue: "Messages delayed by several minutes"

**Symptom:** Customers receive responses 3-5 minutes late

**Cause:** Queue backlog or slow LLM response

**Solution:**

1. **Check queue length:**
   ```bash
   # In Frappe console
   from frappe.utils.background_jobs import get_queue_length
   print(get_queue_length("short"))
   print(get_queue_length("default"))
   ```

2. **Increase workers:**
   ```bash
   # In Procfile or supervisor config
   worker_short: bench worker --queue short --num-workers 4
   ```

3. **Optimize LLM settings:**
   - Reduce max_tokens to 500
   - Use streaming responses
   - Enable response caching

4. **Use faster model:**
   - Switch to naga-gpt-4o-mini for simple queries
   - Implement smart routing (simple → mini, complex → full)

---

### Issue: "Duplicate messages being sent"

**Symptom:** Customer receives same message 2-3 times

**Cause:** Webhook retry or n8n execution retry

**Solution:**

1. **Implement idempotency:**
   ```python
   # In webhook handler
   message_id = kwargs.get("message_id")
   if frappe.db.exists("Communication Message", {"external_message_id": message_id}):
       return {"success": True, "duplicate": True}
   ```

2. **Check webhook retry settings:**
   - Some platforms retry on timeout
   - Ensure webhook returns 200 OK quickly

3. **Use unique message IDs:**
   - Store external_message_id for deduplication
   - Check before processing each message

---

## AI Behavior Issues

### Issue: "AI giving wrong information"

**Symptom:** AI provides incorrect product info, prices, etc.

**Cause:** Outdated knowledge base or hallucination

**Solution:**

1. **Update knowledge base:**
   - Go to Knowledge Base doctype
   - Update relevant articles
   - Save to trigger reindexing

2. **Verify RAG is being used:**
   ```python
   # Check message RAG confidence
   msg = frappe.get_doc("Communication Message", "MSG-2025-00123")
   print(f"RAG Confidence: {msg.rag_confidence}")
   print(f"RAG Used: {msg.rag_query}")
   ```

3. **Increase RAG weight:**
   - Settings > AI Behavior
   - RAG Weight: 0.8 (higher = more reliance on knowledge base)

4. **Add system prompt constraints:**
   ```
   "If you are not certain about product information or pricing,
   say 'Let me check with our team' and escalate."
   ```

---

### Issue: "AI not escalating when it should"

**Symptom:** AI handles complex issues it shouldn't

**Cause:** Escalation rules too strict or sentiment detection failing

**Solution:**

1. **Check escalation rules:**
   - Settings > AI Behavior > Escalation Rules
   - Lower thresholds:
     - Negative Sentiment: -0.3 (from -0.5)
     - Low Confidence: 0.7 (from 0.6)

2. **Add keyword triggers:**
   ```python
   # In escalation logic
   escalation_keywords = [
       "speak to manager",
       "this is ridiculous",
       "cancel my order",
       "lawyer",
       "complaint"
   ]
   ```

3. **Review missed escalations:**
   ```python
   # Find low confidence conversations
   convs = frappe.db.sql("""
       SELECT name, avg_rag_confidence, sentiment
       FROM `tabCommunication Hub`
       WHERE ai_mode = 'Autonomous'
         AND (avg_rag_confidence < 0.6 OR sentiment = 'Negative')
         AND status != 'Escalated'
   """, as_dict=True)
   ```

---

### Issue: "AI responses too long/short"

**Symptom:** Responses don't match platform constraints

**Cause:** Platform-specific prompts not configured

**Solution:**

1. **Check platform prompts:**
   - Settings > AI Behavior > Platform Prompts
   - Verify length constraints for each platform

2. **Adjust prompt:**
   ```
   SMS: "Keep responses under 160 characters. Be extremely concise."
   Twitter: "Maximum 280 characters. Be direct and brief."
   Email: "Provide detailed, well-structured responses."
   ```

3. **Implement post-processing:**
   ```python
   def truncate_for_platform(text, platform):
       limits = get_platform_limits(platform)
       max_chars = limits["max_chars"]
       if len(text) > max_chars:
           return text[:max_chars-3] + "..."
       return text
   ```

---

### Issue: "AI tone doesn't match brand"

**Symptom:** Responses too formal, casual, or generic

**Cause:** System prompt not customized

**Solution:**

1. **Customize system prompt:**
   - Settings > AI Behavior > System Prompt
   - Add brand voice guidelines:
   ```
   You are a friendly, helpful assistant for [Brand Name].

   Voice:
   - Professional but warm
   - Use simple language (avoid jargon)
   - Be empathetic and patient
   - End with a helpful question

   Never:
   - Use slang or emojis (except WhatsApp/Instagram)
   - Make promises we can't keep
   - Discuss competitor products
   ```

2. **Add examples:**
   ```
   Good: "I'd be happy to help you with that! Let me check your order status."
   Bad: "Checking your order now..."
   ```

3. **Test and iterate:**
   - Review recent conversations
   - Adjust prompt based on feedback
   - A/B test different versions

---

## Performance Issues

### Issue: "Slow response times"

**Symptom:** Conversations have 10+ second delays

**Cause:** LLM latency, database queries, or RAG overhead

**Solution:**

1. **Profile slow requests:**
   ```python
   # Add timing to webhook handler
   import time
   start = time.time()

   # ... process webhook ...

   llm_time = time.time() - start
   frappe.log_error(f"LLM took {llm_time}s", "Performance")
   ```

2. **Enable caching:**
   - Settings > Performance
   - Enable Response Caching: Yes
   - Cache Similar Queries: Yes (90% threshold)

3. **Optimize RAG queries:**
   - Reduce top_k to 3 (from 5)
   - Increase min_score to 0.8 (fewer results)
   - Use on-disk payload in Qdrant

4. **Use streaming responses:**
   ```python
   # For chat/email only
   response = generate_completion(
       messages,
       stream=True
   )
   # Send partial responses as they arrive
   ```

5. **Optimize database:**
   ```bash
   # Run database optimization
   bench --site <site-name> mariadb
   ```
   ```sql
   ANALYZE TABLE `tabCommunication Hub`;
   ANALYZE TABLE `tabCommunication Message`;
   OPTIMIZE TABLE `tabCommunication Hub`;
   ```

---

### Issue: "High memory usage"

**Symptom:** Server running out of RAM, swapping

**Cause:** Too many concurrent LLM requests or vector database

**Solution:**

1. **Limit concurrent LLM requests:**
   - Settings > Performance
   - Max Concurrent Requests: 5

2. **Configure Qdrant memory:**
   ```bash
   # Update Qdrant config
   docker update --memory=2g qdrant
   ```

   Enable on-disk payload:
   ```python
   import requests
   requests.patch(
     "http://localhost:6333/collections/ai_comms_knowledge_base",
     json={"on_disk_payload": True}
   )
   ```

3. **Increase server RAM:**
   - Minimum: 4 GB
   - Recommended: 8 GB for production
   - With heavy traffic: 16 GB

4. **Archive old data:**
   ```bash
   # Run monthly archive task
   bench --site <site-name> execute ai_comms_hub.tasks.monthly.archive.archive_old_conversations
   ```

---

### Issue: "High API costs"

**Symptom:** Monthly bill higher than expected

**Cause:** Too many LLM calls or expensive model

**Solution:**

1. **Audit token usage:**
   ```python
   # Check average tokens per conversation
   result = frappe.db.sql("""
       SELECT
         AVG(total_tokens_used) as avg_tokens,
         COUNT(*) as total_convs,
         SUM(total_tokens_used) as total_tokens
       FROM `tabCommunication Hub`
       WHERE DATE(creation) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
   """, as_dict=True)
   print(result)
   ```

2. **Reduce token usage:**
   - Lower max_tokens to 500 (from 1500)
   - Use shorter system prompts
   - Reduce RAG context window

3. **Use cheaper model:**
   - Switch to naga-gpt-4o-mini (80% cost savings)
   - Or gpt-3.5-turbo for simple queries

4. **Implement smart routing:**
   ```python
   def choose_model(query_complexity):
       if query_complexity < 0.5:
           return "naga-gpt-4o-mini"  # Cheap
       else:
           return "naga-gpt-4o"  # Full model
   ```

5. **Enable aggressive caching:**
   - Cache TTL: 600 seconds (10 minutes)
   - Cache similar queries at 85% threshold

---

## Data Issues

### Issue: "Conversations not linking to customers"

**Symptom:** Communication Hub shows "Guest" instead of customer name

**Cause:** Customer identifier not found or matching logic failed

**Solution:**

1. **Check customer custom fields:**
   ```python
   # Verify fields exist
   custom_fields = frappe.get_meta("Customer").fields
   social_fields = [f.fieldname for f in custom_fields if "facebook" in f.fieldname or "instagram" in f.fieldname]
   print(social_fields)
   ```

2. **Update customer with social IDs:**
   ```python
   customer = frappe.get_doc("Customer", "CUS-2025-00001")
   customer.facebook_psid = "123456789"
   customer.phone = "+15551234567"
   customer.save()
   ```

3. **Run backfill script:**
   ```bash
   cd ~/frappe-bench/apps/ai_comms_hub
   python ai_comms_hub/scripts/migrate_data.py backfill_social_ids
   ```

4. **Enable auto-create customers:**
   - Settings > Business Rules
   - Auto-Create Customer: Yes
   - Match By: Phone, Email, Social ID

---

### Issue: "Message thread not showing"

**Symptom:** Communication Hub exists but messages list is empty

**Cause:** Child table data not loading

**Solution:**

1. **Check message records:**
   ```python
   hub = frappe.get_doc("Communication Hub", "COMHUB-2025-00001")
   print(f"Messages: {len(hub.messages)}")

   # Query directly
   messages = frappe.get_all(
       "Communication Message",
       filters={"parent": hub.name},
       fields=["*"]
   )
   print(f"Found {len(messages)} messages")
   ```

2. **Reload document:**
   ```python
   hub.reload()
   hub.load_from_db()
   ```

3. **Check permissions:**
   ```python
   # Ensure user can read Communication Message
   has_perm = frappe.has_permission("Communication Message", "read")
   print(f"Can read messages: {has_perm}")
   ```

---

### Issue: "Data inconsistencies after migration"

**Symptom:** Chatwoot conversations exist but not in Frappe

**Cause:** Migration script didn't complete

**Solution:**

1. **Run migration script:**
   ```bash
   cd ~/frappe-bench/apps/ai_comms_hub
   python ai_comms_hub/scripts/migrate_data.py migrate_chatwoot
   ```

2. **Check migration log:**
   ```python
   # View migration errors
   errors = frappe.get_all(
       "Error Log",
       filters={"method": ["like", "%migrate%"]},
       fields=["*"],
       order_by="creation desc",
       limit=10
   )
   ```

3. **Manual sync specific conversation:**
   ```python
   from ai_comms_hub.scripts.migrate_data import sync_chatwoot_conversation
   sync_chatwoot_conversation(chatwoot_conv_id=123)
   ```

---

### Issue: "Analytics showing zero values"

**Symptom:** Dashboard metrics all show 0

**Cause:** Analytics not calculated or cron jobs not running

**Solution:**

1. **Run analytics manually:**
   ```bash
   bench --site <site-name> execute ai_comms_hub.tasks.daily.analytics.calculate_daily_metrics
   ```

2. **Check scheduled jobs:**
   ```bash
   # List scheduled jobs
   bench --site <site-name> doctor

   # Enable scheduler if disabled
   bench --site <site-name> enable-scheduler
   ```

3. **Verify data exists:**
   ```python
   # Check if conversations exist
   count = frappe.db.count("Communication Hub")
   print(f"Total conversations: {count}")
   ```

4. **Clear cache:**
   ```bash
   bench --site <site-name> clear-cache
   ```

---

## Getting Help

### Log Files

Check these log files for detailed error information:

```bash
# Frappe error log
~/frappe-bench/logs/error.log

# Web server log
~/frappe-bench/logs/web.log

# Scheduler log
~/frappe-bench/logs/scheduler.log

# n8n logs
docker logs n8n

# Qdrant logs
docker logs qdrant
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In site_config.json
{
  "developer_mode": 1,
  "logging": 2
}
```

Restart bench after changes:
```bash
bench restart
```

### Community Support

- **GitHub Issues**: https://github.com/visualgraphx/ai_comms_hub/issues
- **Frappe Forum**: https://discuss.frappe.io
- **Documentation**: `ai_comms_hub/docs/`

### Professional Support

For priority support:
- Email: support@visualgraphx.com
- Slack: Join #ai-comms-hub channel

---

## Common Commands

### Restart Services

```bash
# Restart Frappe
bench restart

# Restart specific service
bench restart web
bench restart worker

# Restart n8n
docker restart n8n

# Restart Qdrant
docker restart qdrant
```

### Clear Cache

```bash
# Clear Frappe cache
bench --site <site-name> clear-cache

# Clear website cache
bench --site <site-name> clear-website-cache

# Rebuild assets
bench build
```

### Database Operations

```bash
# Database backup
bench --site <site-name> backup

# Restore backup
bench --site <site-name> restore /path/to/backup.sql.gz

# Optimize database
bench --site <site-name> mariadb
ANALYZE TABLE `tabCommunication Hub`;
OPTIMIZE TABLE `tabCommunication Hub`;
```

### Debugging

```bash
# Frappe console
bench --site <site-name> console

# Execute Python file
bench --site <site-name> execute path.to.function

# Watch logs in real-time
tail -f ~/frappe-bench/logs/error.log
```

---

Still having issues? [Open a GitHub issue](https://github.com/visualgraphx/ai_comms_hub/issues/new) with:
1. Error message (full traceback)
2. Steps to reproduce
3. Relevant log files
4. Environment details (Frappe version, OS, etc.)
