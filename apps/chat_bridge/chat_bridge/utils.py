"""
Utility functions for Chat Bridge
"""
import frappe
from typing import Optional

def get_chat_settings():
	"""Get Chat Integration Settings"""
	try:
		return frappe.get_single("Chat Integration Settings")
	except frappe.DoesNotExistError:
		frappe.throw("Chat Integration Settings not found. Please configure the integration first.")

def get_user_chat_token(user: Optional[str] = None):
	"""Get Chat API token for user"""
	if not user:
		user = frappe.session.user
	
	try:
		return frappe.get_doc("Chat User Token", {"user": user})
	except frappe.DoesNotExistError:
		return None

def is_chat_enabled() -> bool:
	"""Check if Chat integration is enabled"""
	try:
		settings = get_chat_settings()
		return bool(settings.chat_base_url)
	except:
		return False

