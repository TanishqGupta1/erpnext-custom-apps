"""
Configuration for documentation and settings
"""
from frappe import _


def get_data():
	"""Return settings configuration for Chat Bridge"""
	return [
		{
			"label": _("Integrations"),
			"icon": "fa fa-plug",
			"items": [
				{
					"type": "doctype",
					"name": "Chat Integration Settings",
					"label": _("Chat Settings"),
					"description": _("Configure Chat integration, webhooks, and sync settings"),
					"onboard": 1,
				}
			]
		},
		{
			"label": _("Customer Support"),
			"icon": "fa fa-comments",
			"items": [
				{
					"type": "doctype",
					"name": "Chat Conversation",
					"label": _("Chat Conversations"),
					"description": _("View and manage Chat conversations"),
				},
				{
					"type": "doctype",
					"name": "Chat Contact Mapping",
					"label": _("Contact Mappings"),
					"description": _("Manage Chat to ERPNext contact mappings"),
				},
				{
					"type": "doctype",
					"name": "Chat User Token",
					"label": _("User Tokens"),
					"description": _("Manage Chat user API tokens"),
				},
				{
					"type": "doctype",
					"name": "CRM Label",
					"label": _("CRM Labels"),
					"description": _("Manage conversation labels and tags"),
				},
			]
		},
	]
