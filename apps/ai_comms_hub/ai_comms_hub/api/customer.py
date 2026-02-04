"""
Customer Document Event Handlers

Handles document lifecycle events for Customer:
- after_insert: Create default communication settings
- on_update: Sync customer data to communication channels
"""

import frappe
from frappe import _
from datetime import datetime


def create_default_communication_settings(doc, method):
	"""
	Initialize AI communication settings for new customer.

	Args:
		doc: Customer document
		method: Event method name
	"""
	try:
		settings = frappe.get_single("AI Communications Hub Settings")

		# Set default communication preferences on customer
		# Only if custom fields exist on Customer doctype
		custom_fields = {
			"ai_communication_enabled": 1,
			"preferred_channel": "Email",
			"ai_autonomy_level": settings.ai_autonomy_level or 80,
			"auto_escalate_enabled": 1,
			"communication_language": "English"
		}

		for field, value in custom_fields.items():
			if frappe.db.has_column("Customer", field):
				doc.db_set(field, value, update_modified=False)

		# Initialize metrics fields
		metric_fields = {
			"total_ai_conversations": 0,
			"ai_resolution_rate": 0,
			"avg_sentiment_score": 0,
			"last_ai_interaction": None
		}

		for field, value in metric_fields.items():
			if frappe.db.has_column("Customer", field):
				doc.db_set(field, value, update_modified=False)

		frappe.logger().info(f"Communication settings initialized for customer: {doc.name}")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Customer Settings Init Error: {doc.name}")


def sync_customer_to_channels(doc, method):
	"""
	Sync customer information to communication channels.

	Args:
		doc: Customer document
		method: Event method name
	"""
	try:
		# Get previous values
		old_doc = doc.get_doc_before_save()

		if not old_doc:
			return

		# Check if relevant fields changed
		sync_fields = ["customer_name", "email_id", "mobile_no", "primary_address"]
		fields_changed = any(
			getattr(old_doc, field, None) != getattr(doc, field, None)
			for field in sync_fields
			if hasattr(doc, field)
		)

		if not fields_changed:
			return

		# Sync to Chatwoot if enabled
		settings = frappe.get_single("AI Communications Hub Settings")
		if settings.chatwoot_api_key and settings.chatwoot_url:
			sync_customer_to_chatwoot(doc, settings)

		# Update any open conversations with new customer info
		update_open_conversations(doc)

		frappe.logger().info(f"Customer synced to channels: {doc.name}")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Customer Sync Error: {doc.name}")


def sync_customer_to_chatwoot(doc, settings):
	"""
	Sync customer data to Chatwoot contact.

	Args:
		doc: Customer document
		settings: AI Communications Hub Settings
	"""
	import requests

	try:
		# Get existing Chatwoot contact ID from customer
		chatwoot_contact_id = None
		if frappe.db.has_column("Customer", "chatwoot_contact_id"):
			chatwoot_contact_id = doc.get("chatwoot_contact_id")

		# Build contact data
		contact_data = {
			"name": doc.customer_name,
			"email": doc.get("email_id"),
			"phone_number": doc.get("mobile_no"),
			"custom_attributes": {
				"erpnext_customer_id": doc.name,
				"customer_group": doc.get("customer_group"),
				"territory": doc.get("territory")
			}
		}

		headers = {
			"api_access_token": settings.chatwoot_api_key,
			"Content-Type": "application/json"
		}

		if chatwoot_contact_id:
			# Update existing contact
			response = requests.put(
				f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/contacts/{chatwoot_contact_id}",
				headers=headers,
				json=contact_data,
				timeout=10
			)
		else:
			# Create new contact
			response = requests.post(
				f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/contacts",
				headers=headers,
				json=contact_data,
				timeout=10
			)

			if response.status_code == 200:
				result = response.json()
				new_contact_id = result.get("payload", {}).get("contact", {}).get("id")
				if new_contact_id and frappe.db.has_column("Customer", "chatwoot_contact_id"):
					doc.db_set("chatwoot_contact_id", new_contact_id, update_modified=False)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Chatwoot Sync Error: {doc.name}")


def update_open_conversations(doc):
	"""
	Update customer name in open conversations.

	Args:
		doc: Customer document
	"""
	try:
		# Get open conversations for this customer
		open_hubs = frappe.get_all(
			"Communication Hub",
			filters={
				"customer": doc.name,
				"status": ["in", ["Open", "In Progress"]]
			},
			pluck="name"
		)

		# Update customer name in each
		for hub_name in open_hubs:
			frappe.db.set_value(
				"Communication Hub",
				hub_name,
				"customer_name",
				doc.customer_name,
				update_modified=False
			)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Conversation Update Error: {doc.name}")


def get_customer_communication_summary(customer_name):
	"""
	Get communication summary for a customer.

	Args:
		customer_name: Customer ID

	Returns:
		dict: Communication statistics
	"""
	try:
		# Get all conversations
		conversations = frappe.get_all(
			"Communication Hub",
			filters={"customer": customer_name},
			fields=[
				"name", "channel", "status", "ai_mode",
				"sentiment", "resolution_time", "creation"
			]
		)

		if not conversations:
			return {
				"total_conversations": 0,
				"channels_used": [],
				"ai_resolution_rate": 0,
				"avg_resolution_time": 0,
				"sentiment_distribution": {}
			}

		# Calculate metrics
		total = len(conversations)
		resolved = [c for c in conversations if c.status == "Resolved"]
		ai_resolved = [c for c in resolved if c.ai_mode != "Takeover"]

		channels = list(set(c.channel for c in conversations))

		resolution_times = [c.resolution_time for c in resolved if c.resolution_time]
		avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0

		sentiments = [c.sentiment for c in conversations if c.sentiment]
		sentiment_dist = {}
		for s in sentiments:
			sentiment_dist[s] = sentiment_dist.get(s, 0) + 1

		return {
			"total_conversations": total,
			"resolved_conversations": len(resolved),
			"ai_resolved": len(ai_resolved),
			"channels_used": channels,
			"ai_resolution_rate": (len(ai_resolved) / total * 100) if total > 0 else 0,
			"avg_resolution_time": avg_resolution,
			"sentiment_distribution": sentiment_dist,
			"last_conversation": max(c.creation for c in conversations) if conversations else None
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Customer Summary Error: {customer_name}")
		return {}


@frappe.whitelist()
def get_customer_conversation_history(customer_name, limit=10):
	"""
	API to get customer's recent conversations.

	Args:
		customer_name: Customer ID
		limit: Number of conversations to return

	Returns:
		list: Recent conversations
	"""
	try:
		conversations = frappe.get_all(
			"Communication Hub",
			filters={"customer": customer_name},
			fields=[
				"name", "channel", "status", "ai_mode",
				"subject", "sentiment", "creation", "modified"
			],
			order_by="creation desc",
			limit=limit
		)

		return conversations

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Conversation History Error: {customer_name}")
		return []


@frappe.whitelist()
def set_customer_communication_preference(customer_name, preference, value):
	"""
	API to set customer communication preference.

	Args:
		customer_name: Customer ID
		preference: Preference field name
		value: New value

	Returns:
		dict: Success status
	"""
	allowed_preferences = [
		"ai_communication_enabled",
		"preferred_channel",
		"ai_autonomy_level",
		"auto_escalate_enabled",
		"communication_language"
	]

	if preference not in allowed_preferences:
		return {"success": False, "error": "Invalid preference"}

	try:
		if frappe.db.has_column("Customer", preference):
			frappe.db.set_value("Customer", customer_name, preference, value)
			return {"success": True}
		else:
			return {"success": False, "error": "Preference field not found"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Preference Update Error: {customer_name}")
		return {"success": False, "error": str(e)}
