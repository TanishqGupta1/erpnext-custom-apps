"""
Support module configuration for Chat Bridge
"""
from frappe import _


def extend_bootinfo(bootinfo):
	"""
	Add Chat Bridge specific data to bootinfo
	Called when user logs in
	"""
	# Add custom bootinfo data here if needed
	pass


def get_data():
	"""Configuration for Support module"""
	return [
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Chat Integration Settings",
					"label": _("Chat Settings"),
					"description": _("Configure Chat integration, webhooks, and sync")
				}
			]
		},
		{
			"label": _("Conversations"),
			"items": [
				{
					"type": "page",
					"name": "conversations",
					"label": _("Chat Conversations"),
					"description": _("View and manage customer conversations from Chatwoot")
				},
				{
					"type": "doctype",
					"name": "Chat Contact Mapping",
					"label": _("Contact Mappings"),
					"description": _("Manage contact synchronization between ERPNext and Chatwoot")
				}
			]
		},
		{
			"label": _("Configuration"),
			"items": [
				{
					"type": "doctype",
					"name": "CRM Label",
					"label": _("CRM Labels"),
					"description": _("Manage labels for categorizing conversations")
				},
				{
					"type": "doctype",
					"name": "Chat User Token",
					"label": _("User API Tokens"),
					"description": _("Manage Chat API access tokens for users")
				}
			]
		}
	]
