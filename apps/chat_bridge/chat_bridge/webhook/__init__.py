"""
Webhook endpoint for Chat events
"""
import frappe
from frappe import _
from .handlers import handle_webhook, verify_webhook_signature

@frappe.whitelist(allow_guest=True, methods=['POST'])
def handle():
	"""
	Webhook endpoint for Chat events
	URL: /api/method/chat_bridge.webhook.handle

	Supports two authentication methods:
	1. URL token parameter: ?token=xxx (modern Chatwoot)
	2. X-Chatwoot-Signature header (legacy Chatwoot)
	"""
	try:
		# Check if sync is enabled
		try:
			settings = frappe.get_single("Chat Integration Settings")
			if not settings.get("enabled", 0):
				return {"status": "disabled", "message": "Integration is not enabled"}
			if not settings.get("enable_sync", 0):
				return {"status": "disabled", "message": "Sync is not enabled"}
		except frappe.DoesNotExistError:
			return {"status": "disabled", "message": "Integration settings not found"}

		# Get webhook secret from settings
		webhook_secret = None
		try:
			# Check if webhook_secret field has a value (check raw db value to avoid decryption errors)
			secret_value = frappe.db.get_value("Chat Integration Settings", "Chat Integration Settings", "webhook_secret")
			if secret_value:
				webhook_secret = settings.get_password('webhook_secret')
		except Exception as e:
			# Fallback if password retrieval fails (field might not be set or encrypted properly)
			frappe.logger().warning(f"Could not retrieve webhook_secret: {str(e)}")
			webhook_secret = None

		# Method 1: Check URL token parameter (modern Chatwoot)
		url_token = frappe.form_dict.get('token')
		if url_token:
			# Verify token matches webhook secret
			if webhook_secret and url_token != webhook_secret:
				frappe.log_error("Webhook authentication failed: Invalid URL token", "Chat Webhook")
				return {"status": "error", "message": "Invalid webhook token"}

		# Method 2: Check signature header (legacy Chatwoot)
		elif webhook_secret:
			# Get raw payload for signature verification
			raw_payload = frappe.request.get_data(as_text=True)
			signature = frappe.request.headers.get('X-Chatwoot-Signature', '')

			if signature:
				# Legacy signature-based auth
				if not verify_webhook_signature(raw_payload, signature, webhook_secret):
					frappe.log_error("Webhook authentication failed: Invalid signature", "Chat Webhook")
					return {"status": "error", "message": "Invalid webhook signature"}
			# If no signature and no URL token, allow through (for testing)
			# In production, you might want to enforce authentication

		# Get raw payload
		raw_payload = frappe.request.get_data(as_text=True)
		
		# Parse JSON payload
		payload = frappe.parse_json(raw_payload)
		
		# Extract event type
		event = frappe.request.headers.get('X-Chatwoot-Event', '')
		if not event:
			# Try to get from payload
			event = payload.get('event', '')
		
		if not event:
			frappe.log_error("Missing event type in webhook payload", "Chat Webhook")
			return {"status": "error", "message": "Missing event type in webhook"}

		# Log webhook for debugging
		frappe.logger().info(f"Chat webhook received: {event}")

		# Process webhook asynchronously to avoid timeout
		# Note: 'event' is a reserved parameter in frappe.enqueue, so use 'webhook_event'
		frappe.enqueue(
			method='chat_bridge.webhook.handlers.handle_webhook',
			webhook_event=event,
			webhook_payload=payload,
			queue='long',
			timeout=300
		)

		return {"status": "success", "message": "Webhook received and queued"}

	except Exception as e:
		frappe.logger().error(f"Webhook error: {str(e)}")
		# Don't throw error back to Chat to avoid retry loops
		return {"status": "error", "message": str(e)}
