"""
Chatwoot Webhook Handler

Handles incoming webhooks from Chatwoot for:
- New messages from customers
- Conversation status changes
- Agent assignments
- Message reactions
"""

import frappe
from frappe import _
import json
import hmac
import hashlib
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def handle_chatwoot_webhook():
	"""
	Handle Chatwoot webhook events.

	Chatwoot sends POST with JSON payload containing:
	- event: Event type (message_created, conversation_status_changed, etc.)
	- message_type: incoming/outgoing/activity
	- content: Message text
	- conversation: Conversation details
	- sender: Sender information
	- account: Account information

	Webhook signature is in X-Chatwoot-Signature header (HMAC SHA256).
	"""
	try:
		# Verify webhook signature
		if not verify_chatwoot_signature():
			frappe.local.response['http_status_code'] = 403
			return {"status": "error", "message": "Invalid signature"}

		# Get JSON data
		data = frappe.local.form_dict
		if not data:
			data = json.loads(frappe.request.data.decode('utf-8'))

		event_type = data.get("event")

		frappe.logger().info(f"Chatwoot webhook received: {event_type}")

		# Route to appropriate handler
		if event_type == "message_created":
			return handle_message_created(data)
		elif event_type == "message_updated":
			return handle_message_updated(data)
		elif event_type == "conversation_created":
			return handle_conversation_created(data)
		elif event_type == "conversation_status_changed":
			return handle_conversation_status_changed(data)
		elif event_type == "conversation_updated":
			return handle_conversation_updated(data)
		elif event_type == "webwidget_triggered":
			return handle_webwidget_triggered(data)
		else:
			frappe.logger().info(f"Unhandled Chatwoot event: {event_type}")
			return {"status": "success", "message": f"Event {event_type} acknowledged"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Chatwoot Webhook Error")
		return {"status": "error", "message": str(e)}


def verify_chatwoot_signature():
	"""
	Verify Chatwoot webhook signature.

	Chatwoot signs requests using HMAC SHA256 with webhook secret.
	The signature is in the X-Chatwoot-Signature header.

	Returns:
		bool: True if signature is valid
	"""
	settings = frappe.get_single("AI Communications Hub Settings")

	# Skip verification if webhook secret not configured
	if not settings.chatwoot_webhook_secret:
		frappe.logger().warning("Chatwoot Webhook Secret not configured - skipping signature verification")
		return True

	# Get signature from header
	signature = frappe.request.headers.get("X-Chatwoot-Signature", "")
	if not signature:
		frappe.logger().warning("No X-Chatwoot-Signature header found")
		return False

	# Get webhook secret
	try:
		webhook_secret = settings.get_password("chatwoot_webhook_secret")
	except Exception:
		webhook_secret = settings.chatwoot_webhook_secret

	if not webhook_secret:
		return True

	# Compute expected signature
	body = frappe.request.data
	expected_signature = hmac.new(
		webhook_secret.encode('utf-8'),
		body,
		hashlib.sha256
	).hexdigest()

	# Compare signatures
	return hmac.compare_digest(signature, expected_signature)


def handle_message_created(data):
	"""
	Handle new message from Chatwoot.

	Args:
		data (dict): Webhook payload

	Returns:
		dict: Response status
	"""
	try:
		message_type = data.get("message_type")
		content_type = data.get("content_type")

		# Only process incoming messages from customers
		# Skip outgoing messages (from agents/bot) and activity messages
		if message_type != "incoming":
			frappe.logger().info(f"Skipping non-incoming message: {message_type}")
			return {"status": "success", "message": "Skipped non-incoming message"}

		# Extract message details
		message_data = data
		message_id = message_data.get("id")
		content = message_data.get("content", "")
		created_at = message_data.get("created_at")

		# Get conversation details
		conversation = message_data.get("conversation", {})
		conversation_id = conversation.get("id")
		inbox_id = conversation.get("inbox_id")
		account_id = conversation.get("account_id")
		channel = conversation.get("channel", "")

		# Get sender details
		sender = message_data.get("sender", {})
		sender_id = sender.get("id")
		sender_name = sender.get("name", "")
		sender_email = sender.get("email", "")
		sender_phone = sender.get("phone_number", "")
		sender_type = sender.get("type", "contact")  # contact, user, agent_bot

		# Skip if sender is agent or bot
		if sender_type in ["user", "agent_bot"]:
			return {"status": "success", "message": "Skipped agent/bot message"}

		# Check for duplicate message
		if message_already_processed(str(message_id)):
			return {"status": "duplicate", "message_id": message_id}

		# Handle attachments
		attachments = message_data.get("attachments", [])
		if attachments and not content:
			attachment_types = [a.get("file_type", "file") for a in attachments]
			content = f"[Sent {', '.join(attachment_types)}]"

		# Handle empty content
		if not content:
			content = "[No content]"

		# Find or create hub
		hub = get_or_create_chatwoot_hub(
			conversation_id=conversation_id,
			account_id=account_id,
			inbox_id=inbox_id,
			channel=channel,
			sender_id=sender_id,
			sender_name=sender_name,
			sender_email=sender_email,
			sender_phone=sender_phone
		)

		# Create message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub.name,
			"sender_type": "Customer",
			"sender_name": sender_name or f"Chatwoot User",
			"sender_identifier": str(sender_id),
			"content": content,
			"timestamp": parse_timestamp(created_at) if created_at else datetime.now(),
			"platform_message_id": str(message_id),
			"delivery_status": "Received"
		})

		# Store attachments if any
		if attachments:
			msg.attachments_json = json.dumps(attachments)

		msg.insert()
		frappe.db.commit()

		frappe.logger().info(f"Chatwoot message created: {msg.name} from hub {hub.name}")

		# Trigger AI response if in Autonomous mode
		if hub.ai_mode == "Autonomous":
			frappe.enqueue(
				"ai_comms_hub.api.ai_engine.generate_response",
				hub_id=hub.name,
				message_id=msg.name,
				queue="default",
				enqueue_after_commit=True
			)

		return {"status": "success", "message_id": msg.name}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Chatwoot Message Created Error")
		return {"status": "error", "message": str(e)}


def handle_message_updated(data):
	"""
	Handle message update from Chatwoot.

	Args:
		data (dict): Webhook payload
	"""
	try:
		message_id = data.get("id")

		# Find the message by platform_message_id
		message_name = frappe.db.get_value(
			"Communication Message",
			{"platform_message_id": str(message_id)},
			"name"
		)

		if message_name:
			# Update content if changed
			new_content = data.get("content")
			if new_content:
				frappe.db.set_value(
					"Communication Message",
					message_name,
					"content",
					new_content
				)
				frappe.db.commit()

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Chatwoot Message Updated Error")
		return {"status": "error", "message": str(e)}


def handle_conversation_created(data):
	"""
	Handle new conversation from Chatwoot.

	This is triggered when a new conversation is started.

	Args:
		data (dict): Webhook payload
	"""
	try:
		conversation = data.get("conversation", data)
		conversation_id = conversation.get("id")
		account_id = conversation.get("account_id")
		inbox_id = conversation.get("inbox_id")
		channel = conversation.get("channel", "Chat")

		# Get contact details
		meta = conversation.get("meta", {})
		sender = meta.get("sender", {})
		sender_id = sender.get("id")
		sender_name = sender.get("name", "")
		sender_email = sender.get("email", "")
		sender_phone = sender.get("phone_number", "")

		# Create hub if not exists
		hub = get_or_create_chatwoot_hub(
			conversation_id=conversation_id,
			account_id=account_id,
			inbox_id=inbox_id,
			channel=channel,
			sender_id=sender_id,
			sender_name=sender_name,
			sender_email=sender_email,
			sender_phone=sender_phone
		)

		frappe.logger().info(f"Chatwoot conversation created: {hub.name}")

		return {"status": "success", "hub_id": hub.name}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Chatwoot Conversation Created Error")
		return {"status": "error", "message": str(e)}


def handle_conversation_status_changed(data):
	"""
	Handle conversation status change from Chatwoot.

	Chatwoot statuses: open, resolved, pending, snoozed

	Args:
		data (dict): Webhook payload
	"""
	try:
		conversation_id = data.get("id")
		status = data.get("status")
		account_id = data.get("account_id")

		# Find existing hub
		hub_name = frappe.db.get_value(
			"Communication Hub",
			{
				"chatwoot_conversation_id": str(conversation_id),
				"chatwoot_account_id": str(account_id)
			},
			"name"
		)

		if hub_name:
			# Map Chatwoot status to our status
			status_map = {
				"open": "Open",
				"resolved": "Resolved",
				"pending": "Pending",
				"snoozed": "Snoozed"
			}

			new_status = status_map.get(status, "Open")

			frappe.db.set_value(
				"Communication Hub",
				hub_name,
				"status",
				new_status
			)
			frappe.db.commit()

			frappe.logger().info(f"Chatwoot conversation {conversation_id} status changed to {new_status}")

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Chatwoot Status Changed Error")
		return {"status": "error", "message": str(e)}


def handle_conversation_updated(data):
	"""
	Handle conversation update from Chatwoot.

	This includes assignee changes, label updates, etc.

	Args:
		data (dict): Webhook payload
	"""
	try:
		conversation_id = data.get("id")
		account_id = data.get("account_id")

		# Find existing hub
		hub_name = frappe.db.get_value(
			"Communication Hub",
			{
				"chatwoot_conversation_id": str(conversation_id),
				"chatwoot_account_id": str(account_id)
			},
			"name"
		)

		if hub_name:
			hub = frappe.get_doc("Communication Hub", hub_name)

			# Update assignee if changed
			assignee = data.get("assignee", {})
			if assignee:
				assignee_email = assignee.get("email")
				if assignee_email:
					# Find matching user in ERPNext
					user = frappe.db.get_value("User", {"email": assignee_email}, "name")
					if user:
						hub.db_set("assigned_to", user)

			# Update labels/tags if present
			labels = data.get("labels", [])
			if labels:
				hub.db_set("chatwoot_labels", json.dumps(labels))

			frappe.db.commit()

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Chatwoot Conversation Updated Error")
		return {"status": "error", "message": str(e)}


def handle_webwidget_triggered(data):
	"""
	Handle web widget trigger from Chatwoot.

	This is triggered when a user interacts with the web widget.

	Args:
		data (dict): Webhook payload
	"""
	# Log for now, can be extended for specific widget events
	frappe.logger().info(f"Chatwoot webwidget triggered: {data}")
	return {"status": "success"}


def message_already_processed(message_id):
	"""
	Check if message has already been processed (idempotency check).

	Args:
		message_id (str): Chatwoot message ID

	Returns:
		bool: True if already processed
	"""
	if not message_id:
		return False

	return frappe.db.exists(
		"Communication Message",
		{"platform_message_id": str(message_id)}
	)


def get_or_create_chatwoot_hub(conversation_id, account_id, inbox_id=None, channel="Chat",
							   sender_id=None, sender_name=None, sender_email=None, sender_phone=None):
	"""
	Find or create Communication Hub for Chatwoot conversation.

	Args:
		conversation_id: Chatwoot conversation ID
		account_id: Chatwoot account ID
		inbox_id: Chatwoot inbox ID
		channel: Channel type (Chat, WhatsApp, etc.)
		sender_id: Sender ID
		sender_name: Sender name
		sender_email: Sender email
		sender_phone: Sender phone

	Returns:
		Document: Communication Hub
	"""
	# Map Chatwoot channel to our channel
	channel_map = {
		"Channel::Api": "Chat",
		"Channel::WebWidget": "Chat",
		"Channel::Whatsapp": "WhatsApp",
		"Channel::Sms": "SMS",
		"Channel::Email": "Email",
		"Channel::FacebookPage": "Facebook",
		"Channel::TwitterProfile": "Twitter",
		"Channel::TelegramChannel": "Telegram"
	}

	mapped_channel = channel_map.get(channel, "Chat")

	# Try to find existing hub
	existing = frappe.db.get_value(
		"Communication Hub",
		{
			"chatwoot_conversation_id": str(conversation_id),
			"chatwoot_account_id": str(account_id),
			"status": ["in", ["Open", "In Progress", "Pending"]]
		},
		"name"
	)

	if existing:
		hub = frappe.get_doc("Communication Hub", existing)
		# Update sender info if we have more now
		if sender_name and not hub.customer_name:
			hub.db_set("customer_name", sender_name)
		return hub

	# Also check for recently resolved conversations (within last hour)
	# to reopen instead of creating new
	recent_resolved = frappe.db.get_value(
		"Communication Hub",
		{
			"chatwoot_conversation_id": str(conversation_id),
			"chatwoot_account_id": str(account_id),
			"status": "Resolved",
			"modified": [">", frappe.utils.add_to_date(None, hours=-1)]
		},
		"name"
	)

	if recent_resolved:
		hub = frappe.get_doc("Communication Hub", recent_resolved)
		hub.db_set("status", "Reopened")
		return hub

	# Find or create customer
	customer = get_or_create_customer_from_chatwoot(
		sender_id=sender_id,
		name=sender_name,
		email=sender_email,
		phone=sender_phone
	)

	# Build display name
	display_name = sender_name or sender_email or sender_phone or f"Chatwoot User {sender_id}"

	# Create new hub
	hub = frappe.get_doc({
		"doctype": "Communication Hub",
		"customer": customer.name if customer else None,
		"customer_name": sender_name,
		"channel": mapped_channel,
		"status": "Open",
		"ai_mode": "Autonomous",
		"chatwoot_conversation_id": str(conversation_id),
		"chatwoot_account_id": str(account_id),
		"chatwoot_inbox_id": str(inbox_id) if inbox_id else None,
		"chatwoot_contact_id": str(sender_id) if sender_id else None,
		"chatwoot_phone_number": sender_phone,
		"subject": f"{mapped_channel} conversation with {display_name}"
	})

	hub.insert()
	frappe.db.commit()

	frappe.logger().info(f"Created new Chatwoot hub: {hub.name} for conversation {conversation_id}")

	return hub


def get_or_create_customer_from_chatwoot(sender_id=None, name=None, email=None, phone=None):
	"""
	Find or create customer from Chatwoot contact.

	Args:
		sender_id: Chatwoot contact ID
		name: Contact name
		email: Contact email
		phone: Contact phone

	Returns:
		Document: Customer or None
	"""
	# Try to find by email first
	if email:
		customer_name = frappe.db.get_value(
			"Customer",
			{"email_id": email},
			"name"
		)
		if customer_name:
			return frappe.get_doc("Customer", customer_name)

	# Try to find by phone
	if phone:
		clean_phone = phone.replace("+", "").replace("-", "").replace(" ", "")
		customer_name = frappe.db.get_value(
			"Customer",
			{"mobile_no": ["like", f"%{clean_phone[-10:]}%"]},
			"name"
		)
		if customer_name:
			return frappe.get_doc("Customer", customer_name)

	# Try to find by Chatwoot contact ID (custom field)
	if sender_id and frappe.db.has_column("Customer", "chatwoot_contact_id"):
		customer_name = frappe.db.get_value(
			"Customer",
			{"chatwoot_contact_id": str(sender_id)},
			"name"
		)
		if customer_name:
			return frappe.get_doc("Customer", customer_name)

	# Create new customer
	display_name = name or email or phone or f"Chatwoot Contact {sender_id}"

	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": display_name[:140],  # ERPNext limit
		"customer_type": "Individual",
		"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual",
		"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"
	})

	# Set optional fields
	if email:
		customer.email_id = email
	if phone:
		customer.mobile_no = phone

	# Set chatwoot contact ID if field exists
	if sender_id and frappe.db.has_column("Customer", "chatwoot_contact_id"):
		customer.chatwoot_contact_id = str(sender_id)

	customer.insert(ignore_permissions=True)
	frappe.db.commit()

	frappe.logger().info(f"Created customer from Chatwoot: {customer.name}")

	return customer


def parse_timestamp(timestamp):
	"""
	Parse Chatwoot timestamp to datetime.

	Args:
		timestamp: Unix timestamp or ISO string

	Returns:
		datetime: Parsed datetime
	"""
	if not timestamp:
		return datetime.now()

	try:
		if isinstance(timestamp, (int, float)):
			return datetime.fromtimestamp(timestamp)
		elif isinstance(timestamp, str):
			# Try ISO format
			if "T" in timestamp:
				return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
			# Try Unix timestamp string
			return datetime.fromtimestamp(float(timestamp))
	except Exception:
		pass

	return datetime.now()


@frappe.whitelist(allow_guest=True)
def handle_chatwoot_agent_bot():
	"""
	Handle Chatwoot Agent Bot webhook.

	Chatwoot Agent Bots can be configured to forward messages to external services.
	This endpoint handles incoming messages and returns bot responses.
	"""
	try:
		data = frappe.local.form_dict
		if not data:
			data = json.loads(frappe.request.data.decode('utf-8'))

		event = data.get("event")
		content = data.get("content", "")
		conversation_id = data.get("conversation", {}).get("id")
		account_id = data.get("account", {}).get("id")

		if event != "message_created":
			return {"status": "success", "message": "Event acknowledged"}

		# Only process incoming messages
		if data.get("message_type") != "incoming":
			return {"status": "success", "message": "Skipped non-incoming"}

		# Find the hub
		hub_name = frappe.db.get_value(
			"Communication Hub",
			{
				"chatwoot_conversation_id": str(conversation_id),
				"chatwoot_account_id": str(account_id)
			},
			"name"
		)

		if hub_name:
			hub = frappe.get_doc("Communication Hub", hub_name)

			# Generate AI response synchronously for agent bot
			if hub.ai_mode in ["Autonomous", "HITL"]:
				from ai_comms_hub.api.ai_engine import generate_ai_response

				response = generate_ai_response(hub.name, content)

				if response:
					return {
						"status": "success",
						"response": response
					}

		return {"status": "success", "message": "No response generated"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Chatwoot Agent Bot Error")
		return {"status": "error", "message": str(e)}
