"""
Message Delivery Module

Handles message delivery across all channels:
- Voice (Eleven Labs)
- Facebook/Instagram (Meta Graph API)
- Twitter (Twitter API)
- Email (SendGrid)
- Chat (Chatwoot)

Also handles document events for Communication Message.
"""

import frappe
from frappe import _
import requests
import json
from datetime import datetime


# Document Event Handlers
def validate_message(doc, method):
	"""
	Validate Communication Message before saving.

	Args:
		doc: Communication Message document
		method: Event method name
	"""
	# Validate content
	if not doc.content or not doc.content.strip():
		frappe.throw(_("Message content cannot be empty"))

	# Trim whitespace
	doc.content = doc.content.strip()

	# Set default timestamp
	if not doc.timestamp:
		doc.timestamp = datetime.now()

	# Validate sender type
	valid_sender_types = ["Customer", "AI", "Agent", "System"]
	if doc.sender_type not in valid_sender_types:
		frappe.throw(_("Invalid sender type: {0}").format(doc.sender_type))

	# Set default delivery status
	if not doc.delivery_status:
		if doc.sender_type == "Customer":
			doc.delivery_status = "Received"
		else:
			doc.delivery_status = "Pending"

	# Initialize retry count
	if doc.retry_count is None:
		doc.retry_count = 0

	# Truncate content for platform limits
	from ai_comms_hub.utils.helpers import get_platform_message_limit
	hub = frappe.get_doc("Communication Hub", doc.communication_hub)
	max_length = get_platform_message_limit(hub.channel)
	if len(doc.content) > max_length:
		doc.content = doc.content[:max_length - 3] + "..."


def on_message_created(doc, method):
	"""
	Handle Communication Message creation.

	Args:
		doc: Communication Message document
		method: Event method name
	"""
	try:
		hub = frappe.get_doc("Communication Hub", doc.communication_hub)

		# Update hub's last activity
		hub.db_set("modified", datetime.now(), update_modified=False)

		# Handle based on sender type
		if doc.sender_type == "Customer":
			handle_customer_message(doc, hub)
		elif doc.sender_type in ["AI", "Agent"]:
			handle_outgoing_message(doc, hub)

		# Send real-time notification
		frappe.publish_realtime(
			event="new_message",
			message={
				"hub_id": hub.name,
				"message_id": doc.name,
				"sender_type": doc.sender_type,
				"content_preview": doc.content[:100] if doc.content else ""
			},
			doctype="Communication Hub",
			docname=hub.name
		)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Message Created Error: {doc.name}")


def handle_customer_message(doc, hub):
	"""Handle incoming customer message"""

	# Update hub status if needed
	if hub.status == "Resolved":
		hub.db_set("status", "Reopened")

	# Trigger AI response if in Autonomous mode
	if hub.ai_mode == "Autonomous":
		frappe.enqueue(
			"ai_comms_hub.api.ai_engine.generate_response",
			hub_id=hub.name,
			message_id=doc.name,
			queue="default",
			enqueue_after_commit=True
		)

	# For HITL mode, notify agents
	elif hub.ai_mode == "HITL":
		notify_agents_new_message(hub, doc)


def handle_outgoing_message(doc, hub):
	"""Handle outgoing AI/Agent message"""

	# Queue for delivery
	frappe.enqueue(
		"ai_comms_hub.api.message.deliver_message",
		message_id=doc.name,
		queue="default",
		enqueue_after_commit=True
	)


def notify_agents_new_message(hub, message):
	"""Notify agents of new customer message requiring attention"""
	from ai_comms_hub.api.communication import get_available_agents

	agents = get_available_agents()

	for agent in agents:
		frappe.publish_realtime(
			event="customer_message",
			message={
				"hub_id": hub.name,
				"message_id": message.name,
				"customer": hub.customer_name or hub.customer,
				"channel": hub.channel,
				"content_preview": message.content[:100] if message.content else ""
			},
			user=agent
		)


def deliver_message(message_id):
	"""
	Deliver message via appropriate channel.

	Args:
		message_id (str): Communication Message ID
	"""
	try:
		# Get message and hub
		msg = frappe.get_doc("Communication Message", message_id)
		hub = frappe.get_doc("Communication Hub", msg.communication_hub)

		# Route to channel-specific delivery
		if hub.channel == "Voice":
			return deliver_voice_message(msg, hub)
		elif hub.channel == "Facebook":
			return deliver_facebook_message(msg, hub)
		elif hub.channel == "Instagram":
			return deliver_instagram_message(msg, hub)
		elif hub.channel == "Twitter":
			return deliver_twitter_message(msg, hub)
		elif hub.channel == "Email":
			return send_email(hub.name, message_id)
		elif hub.channel == "Chat":
			return deliver_chatwoot_message(msg, hub)
		elif hub.channel == "WhatsApp":
			return deliver_whatsapp_message(msg, hub)
		elif hub.channel == "SMS":
			return deliver_sms_message(msg, hub)
		else:
			frappe.throw(f"Unknown channel: {hub.channel}")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Message Delivery Error: {message_id}")
		msg.mark_as_failed(str(e))


def deliver_voice_message(msg, hub):
	"""Deliver message via Eleven Labs (voice response)"""
	# Eleven Labs handles voice responses automatically during the call
	# Post-call messages are stored but not actively delivered
	# Mark as delivered
	msg.mark_as_delivered()


def deliver_facebook_message(msg, hub):
	"""Deliver message via Facebook Messenger"""
	settings = frappe.get_single("AI Communications Hub Settings")

	try:
		response = requests.post(
			f"https://graph.facebook.com/v18.0/me/messages",
			params={"access_token": settings.facebook_access_token},
			json={
				"recipient": {"id": hub.social_sender_id},
				"message": {"text": msg.content}
			},
			timeout=10
		)

		response.raise_for_status()
		result = response.json()

		msg.mark_as_delivered(result.get("message_id"))

	except Exception as e:
		msg.mark_as_failed(str(e))


def deliver_instagram_message(msg, hub):
	"""Deliver message via Instagram DM"""
	# Same as Facebook (uses Meta Graph API)
	deliver_facebook_message(msg, hub)


def deliver_twitter_message(msg, hub):
	"""Deliver message via Twitter DM"""
	settings = frappe.get_single("AI Communications Hub Settings")

	try:
		# Twitter API v2 DM endpoint
		response = requests.post(
			"https://api.twitter.com/2/dm_conversations/with/{recipient_id}/messages",
			headers={
				"Authorization": f"Bearer {settings.twitter_bearer_token}",
				"Content-Type": "application/json"
			},
			json={
				"text": msg.content
			},
			timeout=10
		)

		response.raise_for_status()
		result = response.json()

		msg.mark_as_delivered(result.get("data", {}).get("dm_event_id"))

	except Exception as e:
		msg.mark_as_failed(str(e))


def send_email(hub_id, message_id):
	"""Send email via SendGrid"""
	msg = frappe.get_doc("Communication Message", message_id)
	hub = frappe.get_doc("Communication Hub", hub_id)

	settings = frappe.get_single("AI Communications Hub Settings")

	try:
		# Build email
		from_email = settings.sendgrid_from_email or "noreply@visualgraphx.com"
		to_email = hub.email_from  # Reply to customer

		# Build subject (Re: original subject)
		subject = hub.email_subject
		if not subject.startswith("Re:"):
			subject = f"Re: {subject}"

		# Get HTML content
		html_content = msg.content if msg.content_type == "html" else convert_text_to_html(msg.content)

		# Build SendGrid payload
		payload = {
			"personalizations": [{
				"to": [{"email": to_email}],
				"subject": subject
			}],
			"from": {
				"email": from_email,
				"name": settings.sendgrid_from_name or "Support Team"
			},
			"content": [{
				"type": "text/html",
				"value": html_content
			}],
			"headers": {
				"In-Reply-To": hub.email_message_id or "",
				"References": hub.email_in_reply_to or ""
			}
		}

		# Send via SendGrid
		response = requests.post(
			"https://api.sendgrid.com/v3/mail/send",
			headers={
				"Authorization": f"Bearer {settings.sendgrid_api_key}",
				"Content-Type": "application/json"
			},
			json=payload,
			timeout=10
		)

		response.raise_for_status()

		msg.mark_as_delivered()

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Email Send Error: {hub_id}")
		msg.mark_as_failed(str(e))


def deliver_chatwoot_message(msg, hub):
	"""Deliver message via Chatwoot"""
	settings = frappe.get_single("AI Communications Hub Settings")

	try:
		response = requests.post(
			f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/conversations/{hub.chatwoot_conversation_id}/messages",
			headers={
				"api_access_token": settings.chatwoot_api_key,
				"Content-Type": "application/json"
			},
			json={
				"content": msg.content,
				"message_type": "outgoing",
				"private": False
			},
			timeout=10
		)

		response.raise_for_status()
		result = response.json()

		msg.mark_as_delivered(result.get("id"))

	except Exception as e:
		msg.mark_as_failed(str(e))


def deliver_whatsapp_message(msg, hub):
	"""Deliver message via WhatsApp (through Chatwoot/Twilio)"""
	# WhatsApp messages go through Chatwoot
	deliver_chatwoot_message(msg, hub)


def deliver_sms_message(msg, hub):
	"""Deliver SMS via Twilio"""
	settings = frappe.get_single("AI Communications Hub Settings")

	try:
		from twilio.rest import Client

		client = Client(
			settings.twilio_account_sid,
			settings.twilio_auth_token
		)

		message = client.messages.create(
			body=msg.content,
			from_=settings.twilio_phone_number,
			to=hub.sms_phone_number
		)

		msg.mark_as_delivered(message.sid)

	except Exception as e:
		msg.mark_as_failed(str(e))


def convert_text_to_html(text):
	"""Convert plain text to simple HTML"""
	paragraphs = text.split('\n\n')
	html = '<div style="font-family: Arial, sans-serif;">'

	for para in paragraphs:
		if para.strip():
			html += f'<p>{para}</p>'

	html += '</div>'
	return html


@frappe.whitelist()
def send_message_to_hub(hub_id, content, sender_type="Agent"):
	"""
	API endpoint to send message to hub.

	Args:
		hub_id (str): Communication Hub ID
		content (str): Message content
		sender_type (str): Agent, AI, or System

	Returns:
		dict: Created message
	"""
	try:
		# Create message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub_id,
			"sender_type": sender_type,
			"sender_name": frappe.session.user_fullname if sender_type == "Agent" else sender_type,
			"content": content,
			"timestamp": frappe.utils.now_datetime()
		})
		msg.insert()
		frappe.db.commit()

		return {
			"success": True,
			"message_id": msg.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Send Message Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def send_agent_message(hub_id, content, sender_name=None):
	"""
	Send agent message with delivery.

	Args:
		hub_id (str): Communication Hub ID
		content (str): Message content
		sender_name (str, optional): Agent name

	Returns:
		dict: Result
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)

		# Format content for platform
		from ai_comms_hub.api.ai_engine import format_for_platform
		formatted_content = format_for_platform(content, hub.channel)

		# Create message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub_id,
			"sender_type": "Agent",
			"sender_name": sender_name or frappe.utils.get_fullname() or frappe.session.user,
			"content": formatted_content,
			"timestamp": frappe.utils.now_datetime(),
			"delivery_status": "Pending"
		})
		msg.insert()

		# Update hub
		hub.db_set("status", "In Progress")
		hub.db_set("agent_messages", (hub.agent_messages or 0) + 1)
		hub.db_set("total_messages", (hub.total_messages or 0) + 1)

		frappe.db.commit()

		return {
			"success": True,
			"message_id": msg.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Send Agent Message Error: {hub_id}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_conversation_messages(hub_id, limit=50):
	"""
	Get messages for a conversation.

	Args:
		hub_id (str): Communication Hub ID
		limit (int): Number of messages to retrieve

	Returns:
		list: Messages
	"""
	messages = frappe.get_all(
		"Communication Message",
		filters={"communication_hub": hub_id},
		fields=[
			"name", "sender_type", "sender_name", "content",
			"timestamp", "delivery_status", "is_function_call", "function_name"
		],
		order_by="timestamp asc",
		limit=limit
	)

	return messages
