import frappe
from frappe import _


def _ensure_dashboard_access():
	"""Validate that the current user can reach the Chat inbox page."""
	if not frappe.has_permission("Chat Integration Settings", "read", user=frappe.session.user):
		frappe.throw(_("You do not have permission to access Chatwoot."), frappe.PermissionError)

	try:
		settings = frappe.get_single("Chat Integration Settings")
	except frappe.DoesNotExistError:
		frappe.throw(_("Chat Integration Settings are not configured yet."), frappe.ValidationError)

	if not settings.enabled:
		frappe.throw(_("Chat integration is disabled."), frappe.PermissionError)

	if not settings.enable_dashboard:
		frappe.throw(_("Chat dashboard is not enabled. Enable it in Chat Integration Settings."), frappe.PermissionError)

	return settings


@frappe.whitelist()
def get_bootstrap():
	"""Return lightweight bootstrap data for the inbox page."""
	settings = _ensure_dashboard_access()

	token_exists = frappe.db.exists("Chat User Token", {"user": frappe.session.user})

	return {
		"base_url": settings.chat_base_url,
		"default_account_id": settings.default_account_id,
		"token_configured": bool(token_exists),
		"enable_api": bool(settings.enable_api),
		"enable_sync": bool(settings.enable_sync),
	}

