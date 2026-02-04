"""
Webhook handlers for Chat events
Processes incoming webhooks from Chat and syncs data to ERPNext
"""
import frappe
import json
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Optional

from frappe.utils import now_datetime, get_datetime

logger = frappe.logger("chat_webhook")


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
	"""
	Verify webhook signature from Chatwoot

	Args:
		payload: Raw request body
		signature: Signature from X-Chatwoot-Signature header
		secret: Webhook secret from Integration Settings

	Returns:
		True if signature is valid
	"""
	if not secret:
		return False

	expected_signature = hmac.new(
		secret.encode('utf-8'),
		payload.encode('utf-8'),
		hashlib.sha256
	).hexdigest()

	return hmac.compare_digest(expected_signature, signature)


def handle_webhook(webhook_event: str, webhook_payload: Dict) -> Dict:
	"""
	Route webhook events to appropriate handlers

	Args:
		webhook_event: Event type (e.g., 'conversation_created', 'message_created')
		webhook_payload: Webhook payload data

	Returns:
		Response dict
	"""
	try:
		# Normalize event names (Chatwoot uses both formats)
		event = webhook_event.replace('.', '_').lower()

		if event in ('conversation_created', 'conversation_status_changed'):
			handle_conversation_event(webhook_payload)
		elif event == 'conversation_updated':
			handle_conversation_event(webhook_payload)
		elif event == 'message_created':
			handle_message_created(webhook_payload)
		elif event == 'contact_created':
			handle_contact_created(webhook_payload)
		elif event == 'contact_updated':
			handle_contact_updated(webhook_payload)
		elif event in ('conversation_typing_on', 'conversation_typing_off'):
			# Ignore typing events for now
			pass
		else:
			logger.debug(f"[Chatwoot] Unhandled webhook event: {webhook_event}")

		return {"status": "success", "event": webhook_event}
	except Exception as e:
		logger.error(f"[Chatwoot] Error handling webhook event {webhook_event}: {str(e)}")
		frappe.log_error(frappe.get_traceback(), f"Webhook Error: {webhook_event}")
		raise


def _get_settings():
	"""Get Chat Integration Settings with caching"""
	try:
		settings = frappe.get_single("Chat Integration Settings")
		if not settings.get("enabled", 0) or not settings.get("enable_sync", 0):
			return None
		return settings
	except frappe.DoesNotExistError:
		return None


def _map_status(value: Optional[str]) -> str:
	"""Map Chatwoot status to ERPNext status"""
	value = (value or "").strip().lower()
	if value in {"pending", "snoozed", "resolved", "closed"}:
		return value.title()
	return "Open"


def _map_timestamp(value) -> Optional[str]:
	"""Convert Chatwoot timestamp to datetime string"""
	if not value:
		return None
	if isinstance(value, (int, float)):
		try:
			return datetime.utcfromtimestamp(value).isoformat()
		except Exception:
			return None
	try:
		return get_datetime(value).isoformat()
	except Exception:
		return None


def _resolve_assignee(meta: Dict) -> Optional[str]:
	"""Link Chatwoot assignee to ERPNext User via Chat User Token"""
	assignee = meta.get("assignee") if isinstance(meta, dict) else None
	assignee_id = None
	if isinstance(assignee, dict):
		assignee_id = assignee.get("id")
	elif isinstance(meta, dict):
		assignee_id = meta.get("assignee_id")

	if not assignee_id:
		return None

	from frappe.utils import cint
	row = frappe.db.get_value(
		"Chat User Token",
		{"chat_user_id": cint(assignee_id)},
		"user",
	)
	return row


def handle_conversation_event(payload: Dict):
	"""Handle conversation created/updated/status_changed webhooks"""
	settings = _get_settings()
	if not settings or not settings.sync_conversations:
		return

	conversation = payload.get('conversation', payload)
	if not conversation:
		return

	cw_id = conversation.get('id')
	if not cw_id:
		return

	# Check if conversation exists
	existing = frappe.db.get_value("Chat Conversation", {"chat_conversation_id": str(cw_id)}, "name")

	if existing:
		# Update existing conversation
		doc = frappe.get_doc("Chat Conversation", existing)
	else:
		# Create new conversation
		doc = frappe.new_doc("Chat Conversation")
		doc.chat_conversation_id = str(cw_id)

	# Map fields
	doc.account_id = conversation.get("account_id") or settings.default_account_id
	doc.inbox_id = conversation.get("inbox_id")
	doc.status = _map_status(conversation.get("status"))
	doc.channel = conversation.get("channel")

	meta = conversation.get("meta") or {}
	doc.assigned_to = _resolve_assignee(meta)

	# Handle contact
	sender = meta.get("sender") or meta.get("contact") or {}
	contact_id = sender.get("id") or conversation.get("contact_id")

	if contact_id and not doc.contact:
		# Try to find existing contact mapping
		mapping = frappe.db.get_value(
			"Chat Contact Mapping",
			{"chat_contact_id": contact_id, "chat_account_id": doc.account_id},
			["name", "erpnext_contact"],
			as_dict=True
		)
		if mapping and mapping.erpnext_contact:
			doc.contact = mapping.erpnext_contact

	# Contact display name
	for key in ("available_name", "name", "email", "identifier"):
		if sender.get(key):
			doc.contact_display = sender.get(key)
			break

	# Last message preview
	messages = conversation.get("messages", [])
	if messages:
		last_msg = messages[-1] if isinstance(messages, list) else messages
		if isinstance(last_msg, dict):
			doc.last_message_preview = last_msg.get("content", "")[:200]

	doc.last_message_at = _map_timestamp(conversation.get("last_activity_at"))
	doc.external_url = f"{settings.chat_base_url.rstrip('/')}/app/accounts/{doc.account_id}/conversations/{cw_id}"

	doc.last_synced = now_datetime()
	doc.save(ignore_permissions=True)

	logger.info(f"[Chatwoot] {'Created' if not existing else 'Updated'} conversation {doc.name} from webhook")
	frappe.db.commit()


def handle_message_created(payload: Dict):
	"""Handle message.created webhook"""
	settings = _get_settings()
	if not settings or not settings.sync_messages:
		return

	message = payload.get('message', {})
	conversation = payload.get('conversation', {})
	cw_id = conversation.get('id')

	if not cw_id or not message:
		return

	# Find the Chat Conversation
	conv_name = frappe.db.get_value("Chat Conversation", {"chat_conversation_id": str(cw_id)}, "name")

	if not conv_name:
		# Conversation doesn't exist yet - create it first
		handle_conversation_event(payload)
		conv_name = frappe.db.get_value("Chat Conversation", {"chat_conversation_id": str(cw_id)}, "name")
		if not conv_name:
			logger.warning(f"[Chatwoot] Could not find/create conversation {cw_id} for message")
			return

	doc = frappe.get_doc("Chat Conversation", conv_name)

	# Check if message already exists
	message_id = str(message.get("id", ""))
	existing_messages = {m.message_id: m for m in (doc.get("messages") or []) if m.message_id}

	if message_id and message_id not in existing_messages:
		# Add new message
		sender = message.get("sender") or {}
		sender_name = sender.get("available_name") or sender.get("name") or sender.get("email")

		direction = "Incoming"
		if message.get("private"):
			direction = "Private"
		elif (message.get("sender_type") or "").lower() in {"user", "agent"} or message.get("message_type") == 1:
			direction = "Outgoing"

		doc.append("messages", {
			"message_id": message_id,
			"sent_at": _map_timestamp(message.get("created_at")),
			"sender_name": sender_name,
			"sender_type": message.get("sender_type"),
			"direction": direction,
			"content": message.get("content") or "",
			"is_private": 1 if message.get("private") else 0,
		})

		# Update preview
		if not message.get("private"):
			doc.last_message_preview = (message.get("content") or "")[:200]

		doc.last_message_at = _map_timestamp(message.get("created_at"))
		doc.last_synced = now_datetime()
		doc.save(ignore_permissions=True)

		logger.info(f"[Chatwoot] Added message {message_id} to conversation {conv_name}")
		frappe.db.commit()


def handle_contact_created(payload: Dict):
	"""Handle contact.created webhook"""
	settings = _get_settings()
	if not settings or not settings.sync_contacts:
		return

	contact = payload.get('contact', {})
	account_id = payload.get('account_id') or settings.default_account_id
	contact_id = contact.get('id')

	if not contact_id:
		return

	# Check if mapping already exists
	existing = frappe.db.exists("Chat Contact Mapping", {
		"chat_contact_id": contact_id,
		"chat_account_id": account_id
	})

	if existing:
		return

	# Find or create ERPNext Contact
	erpnext_contact = _find_or_create_contact(contact)

	if erpnext_contact:
		# Create contact mapping
		mapping = frappe.get_doc({
			"doctype": "Chat Contact Mapping",
			"erpnext_contact": erpnext_contact,
			"chat_contact_id": contact_id,
			"chat_account_id": account_id,
		})
		mapping.insert(ignore_permissions=True)
		logger.info(f"[Chatwoot] Created contact mapping for {contact_id} -> {erpnext_contact}")
		frappe.db.commit()


def handle_contact_updated(payload: Dict):
	"""Handle contact.updated webhook"""
	settings = _get_settings()
	if not settings or not settings.sync_contacts:
		return

	contact = payload.get('contact', {})
	contact_id = contact.get('id')
	account_id = payload.get('account_id') or settings.default_account_id

	if not contact_id:
		return

	# Find contact mapping
	mapping = frappe.db.get_value(
		"Chat Contact Mapping",
		{"chat_contact_id": contact_id, "chat_account_id": account_id},
		["name", "erpnext_contact"],
		as_dict=True
	)

	if not mapping or not mapping.erpnext_contact:
		return

	# Update ERPNext Contact
	_update_contact_from_chatwoot(mapping.erpnext_contact, contact)
	logger.info(f"[Chatwoot] Updated contact {mapping.erpnext_contact} from webhook")


def _find_or_create_contact(chat_contact: Dict) -> Optional[str]:
	"""Find existing ERPNext Contact or create new one"""
	email = chat_contact.get('email')
	phone = chat_contact.get('phone_number')
	name = chat_contact.get('name', '') or chat_contact.get('available_name', '')

	# Try to find by email
	if email:
		existing = frappe.db.get_value("Contact", {"email_id": email}, "name")
		if existing:
			return existing

	# Try to find by phone
	if phone:
		existing = frappe.db.get_value("Contact", {"mobile_no": phone}, "name")
		if existing:
			return existing

	# Create new contact
	name_parts = name.split(" ", 1) if name else ["Chat Contact"]
	first_name = name_parts[0] if name_parts else "Chat"
	last_name = name_parts[1] if len(name_parts) > 1 else ""

	contact = frappe.get_doc({
		"doctype": "Contact",
		"first_name": first_name,
		"last_name": last_name,
		"email_id": email,
		"mobile_no": phone
	})
	contact.insert(ignore_permissions=True)
	return contact.name


def _update_contact_from_chatwoot(contact_name: str, chat_contact: Dict):
	"""Update ERPNext Contact with Chatwoot data"""
	if not contact_name:
		return

	doc = frappe.get_doc("Contact", contact_name)
	updated = False

	name = chat_contact.get('name') or chat_contact.get('available_name')
	if name:
		parts = name.split(" ", 1)
		first_name = parts[0]
		last_name = parts[1] if len(parts) > 1 else ""
		if doc.first_name != first_name:
			doc.first_name = first_name
			updated = True
		if doc.last_name != last_name:
			doc.last_name = last_name
			updated = True

	if chat_contact.get('email') and doc.email_id != chat_contact['email']:
		doc.email_id = chat_contact['email']
		updated = True

	if chat_contact.get('phone_number') and doc.mobile_no != chat_contact['phone_number']:
		doc.mobile_no = chat_contact['phone_number']
		updated = True

	if updated:
		doc.save(ignore_permissions=True)
		frappe.db.commit()
