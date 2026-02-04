# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def before_install():
	"""
	Run before app installation.

	Checks:
	- Frappe version >= 15
	- ERPNext is installed
	- Required dependencies
	"""
	frappe.msgprint(_("Checking prerequisites for AI Communications Hub..."))

	# Check Frappe version
	frappe_version = frappe.__version__
	if not frappe_version.startswith("15") and not frappe_version.startswith("16"):
		frappe.throw(_("AI Communications Hub requires Frappe v15 or higher. Current version: {0}").format(frappe_version))

	# Check ERPNext is installed
	if "erpnext" not in frappe.get_installed_apps():
		frappe.throw(_("AI Communications Hub requires ERPNext to be installed"))

	frappe.msgprint(_("Prerequisites check passed!"), indicator="green")


def after_install():
	"""
	Run after app installation.

	Actions:
	- Create custom fields on Customer
	- Create default settings document
	- Create Qdrant collection
	- Set up default fixtures
	- Create sample data (if in development)
	"""
	frappe.msgprint(_("Setting up AI Communications Hub..."))

	# Create custom fields
	create_customer_custom_fields()

	# Create default settings
	create_default_settings()

	# Create Qdrant collection
	try:
		from ai_comms_hub.api.rag import create_collection_if_not_exists
		create_collection_if_not_exists()
		frappe.msgprint(_("Qdrant collection created successfully"), indicator="green")
	except Exception as e:
		frappe.log_error(f"Failed to create Qdrant collection: {str(e)}", "Qdrant Setup Error")
		frappe.msgprint(
			_("Warning: Could not create Qdrant collection. You may need to run setup_qdrant.py manually."),
			indicator="orange"
		)

	# Load default fixtures
	from ai_comms_hub.setup.fixtures import install_fixtures
	install_fixtures()

	# Add custom permissions
	setup_permissions()

	# Create sample data in development mode
	if frappe.conf.developer_mode:
		create_sample_data()

	frappe.db.commit()

	frappe.msgprint(
		_("AI Communications Hub installed successfully! Please configure settings before use."),
		indicator="green",
		title=_("Installation Complete")
	)


def create_customer_custom_fields():
	"""
	Create custom fields on Customer doctype for AI Communications Hub.
	"""
	custom_fields = {
		"Customer": [
			{
				"fieldname": "ai_comms_section",
				"label": "AI Communications",
				"fieldtype": "Section Break",
				"insert_after": "represents_company",
				"collapsible": 1
			},
			{
				"fieldname": "preferred_contact_channel",
				"label": "Preferred Contact Channel",
				"fieldtype": "Select",
				"options": "Voice\nChat\nWhatsApp\nSMS\nFacebook\nInstagram\nTwitter\nLinkedIn\nEmail",
				"insert_after": "ai_comms_section"
			},
			{
				"fieldname": "do_not_ai_contact",
				"label": "Do Not AI Contact",
				"fieldtype": "Check",
				"insert_after": "preferred_contact_channel",
				"description": "Customer prefers human agents only"
			},
			{
				"fieldname": "ai_communication_notes",
				"label": "AI Communication Notes",
				"fieldtype": "Small Text",
				"insert_after": "do_not_ai_contact",
				"description": "Special instructions for AI when communicating with this customer"
			},
			{
				"fieldname": "customer_sentiment",
				"label": "Overall Sentiment",
				"fieldtype": "Select",
				"options": "\nPositive\nNeutral\nNegative",
				"insert_after": "ai_communication_notes",
				"read_only": 1,
				"description": "Auto-updated by AI based on conversation history"
			},
			{
				"fieldname": "last_ai_interaction",
				"label": "Last AI Interaction",
				"fieldtype": "Datetime",
				"insert_after": "customer_sentiment",
				"read_only": 1
			},
			{
				"fieldname": "total_ai_conversations",
				"label": "Total AI Conversations",
				"fieldtype": "Int",
				"insert_after": "last_ai_interaction",
				"read_only": 1,
				"default": "0"
			},
			{
				"fieldname": "ai_resolution_rate",
				"label": "AI Resolution Rate (%)",
				"fieldtype": "Percent",
				"insert_after": "total_ai_conversations",
				"read_only": 1,
				"description": "Percentage of conversations resolved by AI without escalation"
			},
			{
				"fieldname": "column_break_ai_comms",
				"fieldtype": "Column Break",
				"insert_after": "ai_resolution_rate"
			},
			{
				"fieldname": "facebook_psid",
				"label": "Facebook PSID",
				"fieldtype": "Data",
				"insert_after": "column_break_ai_comms",
				"read_only": 1,
				"description": "Facebook Page-Scoped ID"
			},
			{
				"fieldname": "instagram_id",
				"label": "Instagram ID",
				"fieldtype": "Data",
				"insert_after": "facebook_psid",
				"read_only": 1
			},
			{
				"fieldname": "twitter_id",
				"label": "Twitter User ID",
				"fieldtype": "Data",
				"insert_after": "instagram_id",
				"read_only": 1
			},
			{
				"fieldname": "linkedin_profile",
				"label": "LinkedIn Profile",
				"fieldtype": "Data",
				"insert_after": "twitter_id",
				"read_only": 1
			},
			{
				"fieldname": "whatsapp_number",
				"label": "WhatsApp Number",
				"fieldtype": "Data",
				"insert_after": "linkedin_profile"
			},
			{
				"fieldname": "sms_opt_in",
				"label": "SMS Opt-In",
				"fieldtype": "Check",
				"insert_after": "whatsapp_number",
				"default": "0",
				"description": "Customer has opted in to receive SMS"
			}
		]
	}

	create_custom_fields(custom_fields, update=True)
	frappe.msgprint(_("Custom fields created on Customer"), indicator="blue")


def create_default_settings():
	"""
	Create default AI Communications Hub Settings document.
	"""
	if not frappe.db.exists("AI Communications Hub Settings", "AI Communications Hub Settings"):
		settings = frappe.get_doc({
			"doctype": "AI Communications Hub Settings",
			"__newname": "AI Communications Hub Settings",
			# LLM Provider defaults
			"llm_api_url": "https://api.naga.ac/v1",
			"llm_model": "gpt-4o-mini",
			"llm_temperature": 0.7,
			"llm_max_tokens": 1000,
			# Qdrant defaults
			"qdrant_url": "http://qdrant:6333",
			"qdrant_collection": "knowledge_base",
			"qdrant_vector_size": 1536,
			# AI Behavior defaults
			"ai_autonomy_level": 80,
			"auto_escalate_on_negative": 1,
			"rag_confidence_threshold": 70,
			"max_ai_retries": 3,
			# Channel defaults
			"enable_voice": 0,
			"enable_chat": 1,
			"enable_email": 1,
			"enable_facebook": 0,
			"enable_instagram": 0,
			"enable_twitter": 0,
			"enable_linkedin": 0,
			"enable_whatsapp": 0,
			"enable_sms": 0
		})
		settings.insert(ignore_permissions=True)
		frappe.msgprint(_("Default settings document created"), indicator="blue")


def setup_permissions():
	"""
	Set up default permissions for AI Communications Hub doctypes.
	"""
	# Give Customer Support role access to Communication Hub
	if not frappe.db.exists("Custom Role", {"role": "Customer Support"}):
		frappe.get_doc({
			"doctype": "Role",
			"role_name": "Customer Support",
			"desk_access": 1
		}).insert(ignore_permissions=True)

	# Set permissions for Communication Hub
	add_permission("Communication Hub", "Customer Support", 0, read=1, write=1, create=1)
	add_permission("Communication Hub", "System Manager", 0, read=1, write=1, create=1, delete=1)

	# Set permissions for Communication Message
	add_permission("Communication Message", "Customer Support", 0, read=1, write=1, create=1)
	add_permission("Communication Message", "System Manager", 0, read=1, write=1, create=1, delete=1)

	# Set permissions for Settings
	add_permission("AI Communications Hub Settings", "System Manager", 0, read=1, write=1)

	frappe.msgprint(_("Permissions configured"), indicator="blue")


def add_permission(doctype, role, perm_level, read=0, write=0, create=0, delete=0, submit=0, cancel=0):
	"""
	Add a permission rule if it doesn't exist.
	"""
	if not frappe.db.exists("Custom DocPerm", {
		"parent": doctype,
		"role": role,
		"permlevel": perm_level
	}):
		frappe.get_doc({
			"doctype": "Custom DocPerm",
			"parent": doctype,
			"parentfield": "permissions",
			"parenttype": "DocType",
			"role": role,
			"permlevel": perm_level,
			"read": read,
			"write": write,
			"create": create,
			"delete": delete,
			"submit": submit,
			"cancel": cancel
		}).insert(ignore_permissions=True)


def create_sample_data():
	"""
	Create sample data for development/testing.
	"""
	frappe.msgprint(_("Creating sample data for development..."), indicator="blue")

	# Create sample customer
	if not frappe.db.exists("Customer", "John Doe - AI Test"):
		customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": "John Doe - AI Test",
			"customer_type": "Individual",
			"customer_group": "Individual",
			"territory": "All Territories",
			"mobile_no": "+1234567890",
			"email_id": "john.doe@example.com",
			"preferred_contact_channel": "Email",
			"whatsapp_number": "+1234567890",
			"sms_opt_in": 1
		})
		customer.insert(ignore_permissions=True)
		frappe.msgprint(_("Sample customer created: {0}").format(customer.name), indicator="blue")

	# Note: Don't create sample Communication Hub here as it requires actual platform integration


def before_uninstall():
	"""
	Run before app uninstallation.

	Warnings:
	- Data will be deleted
	- Custom fields will be removed
	"""
	frappe.msgprint(
		_("Warning: Uninstalling AI Communications Hub will delete all conversations, messages, and custom fields."),
		indicator="red",
		title=_("Data Loss Warning")
	)


def after_uninstall():
	"""
	Run after app uninstallation.

	Cleanup:
	- Remove custom fields
	- Delete Qdrant collection
	"""
	frappe.msgprint(_("Cleaning up AI Communications Hub..."))

	# Remove custom fields from Customer
	remove_custom_fields()

	# Note: We don't delete Qdrant collection automatically (user may want to keep knowledge base)
	frappe.msgprint(
		_("Note: Qdrant collection was not deleted. Run scripts/cleanup_qdrant.py if you want to remove it."),
		indicator="orange"
	)

	frappe.db.commit()

	frappe.msgprint(_("AI Communications Hub uninstalled successfully"), indicator="green")


def remove_custom_fields():
	"""
	Remove custom fields created by this app.
	"""
	custom_field_names = [
		"Customer-ai_comms_section",
		"Customer-preferred_contact_channel",
		"Customer-do_not_ai_contact",
		"Customer-ai_communication_notes",
		"Customer-customer_sentiment",
		"Customer-last_ai_interaction",
		"Customer-total_ai_conversations",
		"Customer-ai_resolution_rate",
		"Customer-column_break_ai_comms",
		"Customer-facebook_psid",
		"Customer-instagram_id",
		"Customer-twitter_id",
		"Customer-linkedin_profile",
		"Customer-whatsapp_number",
		"Customer-sms_opt_in"
	]

	for fieldname in custom_field_names:
		if frappe.db.exists("Custom Field", fieldname):
			frappe.delete_doc("Custom Field", fieldname, ignore_permissions=True, force=True)

	frappe.msgprint(_("Custom fields removed from Customer"), indicator="blue")
