import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_url
import requests


class ChatIntegrationSettings(Document):
	"""Single DocType for Chat integration configuration"""

	def validate(self):
		"""Validate settings"""
		if self.chat_base_url and not self.chat_base_url.startswith(('http://', 'https://')):
			frappe.throw("Chat Base URL must start with http:// or https://")

		if self.default_account_id and self.default_account_id < 1:
			frappe.throw("Default Account ID must be a positive integer")

		# Auto-set webhook URL
		self.webhook_url_display = f"{get_url()}/api/method/chat_bridge.webhook.handle"


@frappe.whitelist()
def test_connection():
	"""Test connection to Chat API"""
	settings = frappe.get_single("Chat Integration Settings")

	if not settings.enabled or not settings.enable_api:
		frappe.throw("Please enable Integration and API Access first")

	# Get a user token to test with
	token_doc = frappe.get_all(
		"Chat User Token",
		fields=["user", "access_token"],
		limit=1,
		order_by="modified desc"
	)

	if not token_doc:
		frappe.throw("No Chat User Token found. Please add a user token first.")

	token = frappe.get_value("Chat User Token", {"user": token_doc[0].user}, "access_token")

	try:
		response = requests.get(
			f"{settings.chat_base_url}/api/v1/accounts/{settings.default_account_id}",
			headers={"api_access_token": token},
			timeout=10
		)

		if response.status_code == 200:
			data = response.json()
			account_name = data.get('name', 'Unknown')

			# Update connection status
			frappe.db.set_value(
				"Chat Integration Settings",
				"Chat Integration Settings",
				"connection_status",
				f"✅ Connected to: {account_name}"
			)

			frappe.msgprint(
				f"✅ Connection successful!<br><br><b>Account:</b> {account_name}<br><b>Account ID:</b> {settings.default_account_id}",
				title="Connection Test",
				indicator="green"
			)
			return {"success": True, "account_name": account_name}
		else:
			error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
			frappe.db.set_value(
				"Chat Integration Settings",
				"Chat Integration Settings",
				"connection_status",
				f"❌ Failed: {error_msg}"
			)
			frappe.throw(f"Connection failed: {error_msg}")

	except requests.exceptions.Timeout:
		frappe.throw("Connection timeout - please check your Chat Base URL")
	except requests.exceptions.ConnectionError:
		frappe.throw("Cannot connect to Chat - please check the URL and your network")
	except Exception as e:
		frappe.throw(f"Connection error: {str(e)}")


@frappe.whitelist()
def manual_sync_conversations(max_conversations=50):
	"""Manually trigger conversation sync"""
	settings = frappe.get_single("Chat Integration Settings")

	if not settings.enabled or not settings.enable_api:
		frappe.throw("Integration and API must be enabled to sync")

	if not settings.sync_conversations:
		frappe.throw("Conversation sync is disabled. Please enable it in settings.")

	try:
		# Import here to avoid circular imports
		from chat_bridge.customer_support.doctype.chat_conversation.sync import sync_chat_conversations

		# Run sync in background
		frappe.enqueue(
			sync_chat_conversations,
			max_conversations=int(max_conversations),
			queue='long',
			timeout=600
		)

		# Update last sync time
		frappe.db.set_value(
			"Chat Integration Settings",
			"Chat Integration Settings",
			"last_sync_time",
			now_datetime()
		)

		frappe.msgprint(
			f"✅ Sync started!<br><br>Syncing up to {max_conversations} conversations in the background.<br>Check the Chat Conversation list for updates.",
			title="Manual Sync",
			indicator="blue"
		)

		return {"success": True, "message": "Sync started"}

	except Exception as e:
		frappe.throw(f"Sync failed: {str(e)}")

