from frappe import _
import frappe

def get_data():
	"""Show Customer Support module with Chatwoot"""
	# Check if user has permission to view Chatwoot
	if not frappe.has_permission("Chat Integration Settings", "read", user=frappe.session.user):
		return []

	return [
		{
			"module_name": "Customer Support",
			"category": "Modules",
			"color": "#3498db",
			"icon": "fa fa-comments",
			"type": "module",
			"label": _("Customer Support"),
			"description": _("Chat integration for customer support"),
			"_doctype": "Chat Conversation",
			"hidden": 0,
			"items": [
				{
					"type": "doctype",
					"name": "Chat Integration Settings",
					"label": _("Chat Settings"),
					"description": _("Configure Chat integration")
				},
				{
					"type": "page",
					"name": "conversations",
					"label": _("Conversations"),
					"description": _("View and manage customer conversations")
				},
				{
					"type": "doctype",
					"name": "Chat Contact Mapping",
					"label": _("Contact Mappings"),
					"description": _("Manage contact synchronization")
				},
				{
					"type": "doctype",
					"name": "CRM Label",
					"label": _("Labels"),
					"description": _("Manage conversation labels")
				},
				{
					"type": "doctype",
					"name": "Chat User Token",
					"label": _("User Tokens"),
					"description": _("Manage API access tokens")
				}
			]
		}
	]
