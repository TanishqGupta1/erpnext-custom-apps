import json
from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Tuple

import frappe
from frappe.utils import cint, get_datetime, now_datetime

from chat_bridge.api.chat import ChatwootAPI, ChatwootAPIError

logger = frappe.logger("chat_sync")


def _get_service_api() -> Optional[ChatwootAPI]:
	"""
	Returns a ChatwootAPI instance using the most recently updated Chat User Token.
	We reuse the ChatwootAPI.get_api_for_user helper but fall back gracefully if no tokens exist.
	"""
	token_row = frappe.db.get_value(
		"Chat User Token",
		{},
		["user"],
		order_by="modified desc",
		as_dict=True,
	)
	if not token_row:
		logger.warning("[Chatwoot] No Chat User Token found. Cannot sync conversations.")
		return None

	try:
		return ChatwootAPI.get_api_for_user(token_row.user)
	except frappe.ValidationError:
		logger.warning("[Chatwoot] Token lookup failed for user %s", token_row.user)
		return None


def _extract_conversation_list(response: Any) -> Iterable[Dict[str, Any]]:
	"""Chat API returns payloads in a couple of shapes - normalise to a flat list."""

	def _seek_list(candidate: Any) -> Optional[Iterable[Dict[str, Any]]]:
		if isinstance(candidate, list):
			return candidate

		if isinstance(candidate, dict):
			for key in ("payload", "data", "items", "results"):
				if key not in candidate:
					continue
				result = _seek_list(candidate[key])
				if result:
					return result
		return None

	result = _seek_list(response)
	if result:
		return result

	logger.warning("[Chatwoot] Unable to locate conversations in payload: %s", str(response)[:500])
	return []


def _ensure_contact_link(conversation: Dict[str, Any], account_id: int) -> Tuple[Optional[str], Optional[str]]:
	"""Map the Chat contact to an ERPNext Contact (and mapping DocType)."""
	meta = conversation.get("meta") or {}
	sender = meta.get("sender") or meta.get("contact") or {}
	contact_id = sender.get("id") or conversation.get("contact_id")
	if not contact_id:
		return (None, _derive_contact_display(sender))

	mapping = frappe.db.get_value(
		"Chat Contact Mapping",
		{"chat_contact_id": contact_id, "chat_account_id": account_id},
		["name", "erpnext_contact"],
		as_dict=True,
	)
	if mapping and mapping.erpnext_contact:
		_sync_contact_details(mapping.erpnext_contact, sender)
		contact_doc = frappe.get_doc("Contact", mapping.erpnext_contact)
		return mapping.erpnext_contact, _derive_contact_display(sender, contact_doc)

	contact_doc = _create_contact_from_sender(sender)
	if not contact_doc:
		return (None, _derive_contact_display(sender))

	frappe.get_doc(
		{
			"doctype": "Chat Contact Mapping",
			"erpnext_contact": contact_doc.name,
			"chat_contact_id": contact_id,
			"chat_account_id": account_id,
		}
	).insert(ignore_permissions=True)
	return contact_doc.name, _derive_contact_display(sender, contact_doc)


def _derive_contact_display(sender: Dict[str, Any], contact_doc=None) -> Optional[str]:
	if sender:
		for key in ("available_name", "name", "email", "identifier"):
			if sender.get(key):
				return sender.get(key)
	if contact_doc:
		full_name = " ".join(filter(None, [contact_doc.first_name, contact_doc.last_name])).strip()
		if full_name:
			return full_name
		if contact_doc.email_id:
			return contact_doc.email_id
	return None


def _sync_contact_details(contact_name: str, sender: Dict[str, Any]) -> None:
	"""Backfill ERP Contact data with the latest Chat sender metadata."""
	if not sender or not contact_name:
		return

	doc = frappe.get_doc("Contact", contact_name)
	updated = False

	name = (
		sender.get("available_name")
		or sender.get("name")
		or sender.get("email")
		or sender.get("identifier")
	)
	if name:
		parts = name.split(" ", 1)
		first_name = parts[0]
		last_name = parts[1] if len(parts) > 1 else ""
		if first_name and doc.first_name != first_name:
			doc.first_name = first_name
			updated = True
		if doc.last_name != last_name:
			doc.last_name = last_name
			updated = True

	if sender.get("email") and doc.email_id != sender["email"]:
		doc.email_id = sender["email"]
		updated = True

	if sender.get("phone_number") and doc.mobile_no != sender["phone_number"]:
		doc.mobile_no = sender["phone_number"]
		updated = True

	if updated:
		doc.save(ignore_permissions=True)


def _create_contact_from_sender(sender: Dict[str, Any]):
	"""Create an ERPNext Contact document from Chat sender metadata."""
	if not sender:
		return None

	email = sender.get("email")
	phone = sender.get("phone_number")
	if email:
		existing = frappe.db.get_value("Contact", {"email_id": email})
		if existing:
			return frappe.get_doc("Contact", existing)
	if phone:
		existing = frappe.db.get_value("Contact", {"mobile_no": phone})
		if existing:
			return frappe.get_doc("Contact", existing)

	name = (
		sender.get("available_name")
		or sender.get("name")
		or sender.get("email")
		or sender.get("identifier")
		or "Chat Contact"
	)
	name_parts = name.split(" ", 1)
	first_name = name_parts[0] if name_parts else "Chat"
	last_name = name_parts[1] if len(name_parts) > 1 else ""

	contact = frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": first_name,
			"last_name": last_name,
			"email_id": sender.get("email"),
			"mobile_no": sender.get("phone_number"),
		}
	)
	contact.insert(ignore_permissions=True)
	return contact


def _ensure_label(label_name: str) -> Optional[str]:
	"""Create CRM Label records on the fly so the Table MultiSelect field has a valid Link."""
	label_name = (label_name or "").strip()
	if not label_name:
		return None

	existing = frappe.db.get_value("CRM Label", {"label_name": label_name})
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "CRM Label",
			"label_name": label_name,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _map_status(value: Optional[str]) -> str:
	value = (value or "").strip().lower()
	if value in {"pending", "snoozed", "resolved", "closed"}:
		return value.title()
	return "Open"


def _get_conversation_snapshot(doc) -> Dict[str, Any]:
	"""Get a snapshot of key fields for change detection."""
	snapshot = {
		"status": doc.status or "",
		"priority": doc.priority or "",
		"assigned_to": doc.assigned_to or "",
		"contact": doc.contact or "",
		"contact_display": doc.contact_display or "",
		"last_message_preview": (doc.last_message_preview or "")[:200],
		"last_message_at": str(doc.last_message_at) if doc.last_message_at else "",
		"channel": doc.channel or "",
	}
	# Include message count
	if hasattr(doc, "messages") and doc.messages:
		snapshot["message_count"] = len(doc.messages)
		snapshot["message_ids"] = sorted([str(m.message_id) for m in doc.messages if m.message_id])[:50]
	else:
		snapshot["message_count"] = 0
		snapshot["message_ids"] = []
	return snapshot


def _has_conversation_changed(doc, before_snapshot: Dict[str, Any]) -> bool:
	"""Check if conversation has meaningful changes after field mapping."""
	after_snapshot = _get_conversation_snapshot(doc)

	for key, before_val in before_snapshot.items():
		after_val = after_snapshot.get(key)
		if before_val != after_val:
			logger.debug(f"[Chatwoot] Change detected in {key}: {before_val} -> {after_val}")
			return True

	return False


def _map_priority(value: Optional[str]) -> str:
	value = (value or "").strip().lower()
	if value in {"low", "medium", "high", "urgent"}:
		return value.title()
	return "None"


def _map_timestamp(value: Any) -> Optional[str]:
	if not value:
		return None
	# Chat sends epoch seconds or ISO strings
	if isinstance(value, (int, float)):
		try:
			return datetime.utcfromtimestamp(value).isoformat()
		except Exception:
			return None

	try:
		return get_datetime(value).isoformat()
	except Exception:
		return None


def _resolve_assignee(meta: Dict[str, Any]) -> Optional[str]:
	"""Link Chat assignee_id to an ERPNext User via Chat User Token records."""
	assignee = meta.get("assignee") if isinstance(meta, dict) else None
	assignee_id = None
	if isinstance(assignee, dict):
		assignee_id = assignee.get("id")
	elif isinstance(meta, dict):
		assignee_id = meta.get("assignee_id")

	if not assignee_id:
		return None

	row = frappe.db.get_value(
		"Chat User Token",
		{"chat_user_id": cint(assignee_id)},
		"user",
	)
	return row


def _convert_message_payload(message: Dict[str, Any]) -> Dict[str, Any]:
	sender = message.get("sender") or {}
	sender_name = sender.get("available_name") or sender.get("name") or sender.get("email")
	direction = "Incoming"
	if message.get("private"):
		direction = "Private"
	elif (message.get("sender_type") or "").lower() in {"user", "agent"} or message.get("message_type") == 1:
		direction = "Outgoing"

	return {
		"message_id": str(message.get("id")),
		"sent_at": _map_timestamp(message.get("created_at")),
		"sender_name": sender_name,
		"sender_type": message.get("sender_type"),
		"direction": direction,
		"content": message.get("content") or "",
		"is_private": cint(message.get("private")),
	}


def _sync_messages(doc, api: Optional[ChatwootAPI], limit: int = 1000) -> None:
	"""Fetch Chat messages and mirror them into the child table."""
	if not api or not doc.chat_conversation_id:
		return

	existing = {child.message_id: child for child in (doc.get("messages") or []) if child.message_id}
	seen = set(existing.keys())
	new_rows = 0
	page = 1
	per_page = 100

	while len(seen) < limit:
		try:
			response = api.get_messages(
				doc.chat_conversation_id,
				page=page,
				per_page=min(per_page, limit - len(seen)),
			)
		except ChatwootAPIError as exc:
			logger.error("[Chatwoot] Unable to pull messages for %s: %s", doc.chat_conversation_id, exc)
			break

		messages = list(_extract_conversation_list(response))
		if not messages:
			break

		for message in messages:
			payload = _convert_message_payload(message)
			message_id = payload["message_id"]
			if message_id in existing:
				child = existing[message_id]
				updated = False
				for key, value in payload.items():
					if child.get(key) != value:
						child.set(key, value)
						updated = True
				if updated:
					child.flags.dirty = True
				continue

			if len(seen) >= limit:
				break
			doc.append("messages", payload)
			seen.add(message_id)
			new_rows += 1

		if len(messages) < per_page:
			break
		page += 1

	if new_rows:
		logger.info("[Chatwoot] Synced %s messages for conversation %s", new_rows, doc.chat_conversation_id)


def _upsert_conversation(payload: Dict[str, Any], settings, api: Optional[ChatwootAPI]) -> None:
	cw_id = payload.get("id")
	if not cw_id:
		return

	name = frappe.db.get_value(
		"Chat Conversation", {"chat_conversation_id": cw_id}
	)
	is_new = not name

	if name:
		doc = frappe.get_doc("Chat Conversation", name)
		# Take snapshot BEFORE mapping fields for change detection
		before_snapshot = _get_conversation_snapshot(doc)
	else:
		doc = frappe.new_doc("Chat Conversation")
		doc.chat_conversation_id = cw_id
		before_snapshot = None

	doc.account_id = payload.get("account_id") or settings.default_account_id
	doc.inbox_id = payload.get("inbox_id")
	doc.status = _map_status(payload.get("status"))
	doc.priority = _map_priority(payload.get("priority"))
	meta = payload.get("meta") or {}
	doc.assigned_to = _resolve_assignee(meta)
	doc.channel = payload.get("channel")
	contact_name, display_name = _ensure_contact_link(payload, doc.account_id)
	if contact_name and not doc.contact:
		doc.contact = contact_name
	if display_name:
		doc.contact_display = display_name

	preview = payload.get("message") or payload.get("last_non_activity_message")
	if isinstance(preview, dict):
		preview = preview.get("content")
	elif isinstance(preview, list) and preview:
		preview = preview[-1].get("content")
	elif not preview and payload.get("messages"):
		preview = payload["messages"][-1].get("content")
	doc.last_message_preview = preview
	doc.last_message_at = _map_timestamp(payload.get("last_activity_at"))
	doc.external_url = f"{settings.chat_base_url.rstrip('/')}/app/accounts/{doc.account_id}/conversations/{cw_id}"

	labels = payload.get("labels") or []
	doc.set("labels", [])
	for label in labels:
		label_name = _ensure_label(label)
		if label_name:
			doc.append("labels", {"crm_label": label_name})

	tags = payload.get("tags") or payload.get("additional_attributes", {}).get("tags")
	if tags:
		doc.tags_json = json.dumps(tags)

	_sync_messages(doc, api)

	# Check if there are actual changes (skip save if no changes)
	if not is_new and before_snapshot:
		has_changes = _has_conversation_changed(doc, before_snapshot)
		if not has_changes:
			# No changes - just update last_synced without creating a version
			frappe.db.set_value("Chat Conversation", doc.name, "last_synced", now_datetime(), update_modified=False)
			return

	# Save only if new or has changes
	doc.last_synced = now_datetime()
	doc.save(ignore_permissions=True)

	if is_new:
		logger.info(f"[Chatwoot] Created new conversation {doc.name} (CW ID: {cw_id})")
	else:
		logger.info(f"[Chatwoot] Updated conversation {doc.name} with changes")


def sync_chat_conversations(max_conversations: int = 200) -> None:
	"""
	Pulls the latest conversations from Chat and stores/updates Chat Conversation DocTypes.
	Honours the integration settings toggles so schedulers won't run in environments
	where the integration is disabled.
	"""
	settings = frappe.get_single("Chat Integration Settings")
	if not (settings.enabled and settings.enable_api and settings.sync_conversations):
		logger.info(
			"[Chatwoot] Conversation sync skipped (enabled=%s, api=%s, sync=%s)",
			settings.enabled,
			settings.enable_api,
			settings.sync_conversations,
		)
		return

	api = _get_service_api()
	if not api:
		return

	logger.info("[Chatwoot] Starting conversation sync (max=%s)", max_conversations)
	page = 1
	fetched = 0
	per_page = 50

	while fetched < max_conversations:
		try:
			response = api.get_conversations(status="all", assignee_type="all", page=page, per_page=per_page)
		except ChatwootAPIError as exc:
			logger.error(
				f"[Chatwoot] Failed to fetch conversations on page {page}: {exc}"
			)
			break

		records = list(_extract_conversation_list(response))
		if not records:
			logger.info("[Chatwoot] No conversations returned on page %s", page)
			break

		for record in records:
			_upsert_conversation(record, settings, api)
			fetched += 1
			if fetched >= max_conversations:
				break

		if len(records) < per_page:
			break
		page += 1

	logger.info("[Chatwoot] Conversation sync finished. Upserted %s records.", fetched)
	frappe.db.commit()


def enqueue_conversation_sync():
	"""Helper to enqueue sync via UI/whitelisted methods."""
	frappe.enqueue(
		"chat_bridge.customer_support.doctype.chat_conversation.sync.sync_chat_conversations",
		now=frappe.flags.in_test,
	)
