"""
Patch to enhance Chat DocTypes with recommended improvements
Adds:
- Sync status tracking
- Error logging
- Additional role permissions
- Connection test functionality
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Main execution function"""
	print("=== Enhancing Chat DocTypes ===\n")

	# Add custom fields
	add_sync_tracking_fields()

	# Add role permissions
	add_role_permissions()

	# Add database indexes
	add_database_indexes()

	# Clear cache
	frappe.clear_cache()

	frappe.db.commit()
	print("\n✅ Chat DocTypes enhanced successfully!")


def add_sync_tracking_fields():
	"""Add sync status and error tracking fields"""
	print("Adding sync tracking fields...")

	custom_fields = {
		'Chat Contact Mapping': [
			{
				'fieldname': 'sync_status',
				'label': 'Sync Status',
				'fieldtype': 'Select',
				'options': 'Active\nFailed\nDisabled',
				'default': 'Active',
				'insert_after': 'sync_direction',
				'in_list_view': 1,
			},
			{
				'fieldname': 'last_sync_error',
				'label': 'Last Sync Error',
				'fieldtype': 'Small Text',
				'read_only': 1,
				'insert_after': 'sync_status',
			},
			{
				'fieldname': 'sync_attempts',
				'label': 'Failed Sync Attempts',
				'fieldtype': 'Int',
				'default': 0,
				'read_only': 1,
				'insert_after': 'last_sync_error',
			},
		],
		'Chat Conversation Mapping': [
			{
				'fieldname': 'sync_status',
				'label': 'Sync Status',
				'fieldtype': 'Select',
				'options': 'Active\nFailed\nDisabled',
				'default': 'Active',
				'insert_after': 'sync_direction',
				'in_list_view': 1,
			},
			{
				'fieldname': 'last_sync_error',
				'label': 'Last Sync Error',
				'fieldtype': 'Small Text',
				'read_only': 1,
				'insert_after': 'sync_status',
			},
		],
		'Chat User Token': [
			{
				'fieldname': 'token_status',
				'label': 'Token Status',
				'fieldtype': 'Select',
				'options': 'Active\nExpired\nRevoked',
				'default': 'Active',
				'insert_after': 'access_token',
				'in_list_view': 1,
			},
			{
				'fieldname': 'expires_at',
				'label': 'Token Expires At',
				'fieldtype': 'Datetime',
				'insert_after': 'token_status',
			},
			{
				'fieldname': 'last_used',
				'label': 'Last Used',
				'fieldtype': 'Datetime',
				'read_only': 1,
				'insert_after': 'expires_at',
			},
		],
		'CRM Label': [
			{
				'fieldname': 'label_type',
				'label': 'Label Type',
				'fieldtype': 'Select',
				'options': '\nCustomer\nProduct\nStatus\nPriority\nTeam\nOther',
				'default': 'Other',
				'insert_after': 'label_name',
				'in_standard_filter': 1,
			},
			{
				'fieldname': 'chat_label_id',
				'label': 'Chat Label ID',
				'fieldtype': 'Data',
				'read_only': 1,
				'insert_after': 'label_type',
			},
			{
				'fieldname': 'usage_count',
				'label': 'Times Used',
				'fieldtype': 'Int',
				'default': 0,
				'read_only': 1,
				'insert_after': 'chat_label_id',
			},
		],
		'Chat Conversation Label': [
			{
				'fieldname': 'applied_at',
				'label': 'Applied At',
				'fieldtype': 'Datetime',
				'read_only': 1,
				'insert_after': 'crm_label',
			},
			{
				'fieldname': 'applied_by',
				'label': 'Applied By',
				'fieldtype': 'Link',
				'options': 'User',
				'read_only': 1,
				'insert_after': 'applied_at',
			},
		],
		'Chat Message': [
			{
				'fieldname': 'attachments',
				'label': 'Attachment URLs (JSON)',
				'fieldtype': 'Text',
				'insert_after': 'content',
			},
			{
				'fieldname': 'message_type',
				'label': 'Message Type',
				'fieldtype': 'Select',
				'options': 'Text\nImage\nFile\nVideo\nAudio\nLocation',
				'default': 'Text',
				'insert_after': 'attachments',
			},
		],
		'Chat Integration Settings': [
			{
				'fieldname': 'webhook_url_display',
				'label': 'Webhook URL (Copy to Chatwoot)',
				'fieldtype': 'Data',
				'read_only': 1,
				'insert_after': 'webhook_secret',
				'description': 'Copy this URL to your Chat webhook configuration',
			},
			{
				'fieldname': 'last_sync_time',
				'label': 'Last Manual Sync',
				'fieldtype': 'Datetime',
				'read_only': 1,
				'insert_after': 'sync_messages',
			},
			{
				'fieldname': 'connection_status',
				'label': 'Connection Status',
				'fieldtype': 'Data',
				'read_only': 1,
				'insert_after': 'last_sync_time',
			},
		],
	}

	create_custom_fields(custom_fields, update=True)
	print("✓ Custom fields added")


def add_role_permissions():
	"""Add permissions for Support Team and Sales User roles"""
	print("Adding role permissions...")

	# DocTypes and their permission configurations
	doctype_permissions = {
		'Chat Conversation': [
			{
				'role': 'Support Team',
				'read': 1,
				'write': 1,
				'create': 1,
				'delete': 0,
				'email': 1,
				'print': 1,
				'share': 1,
			},
			{
				'role': 'Sales User',
				'read': 1,
				'write': 1,
				'create': 0,
				'delete': 0,
			},
		],
		'Chat Contact Mapping': [
			{
				'role': 'Support Team',
				'read': 1,
				'write': 0,
				'create': 0,
				'delete': 0,
			},
		],
		'Chat Conversation Mapping': [
			{
				'role': 'Support Team',
				'read': 1,
				'write': 0,
				'create': 0,
				'delete': 0,
			},
		],
		'CRM Label': [
			{
				'role': 'Support Team',
				'read': 1,
				'write': 1,
				'create': 1,
				'delete': 0,
			},
			{
				'role': 'Sales User',
				'read': 1,
				'write': 0,
				'create': 0,
				'delete': 0,
			},
		],
		'Chat User Token': [
			{
				'role': 'All',
				'read': 1,
				'write': 1,
				'create': 1,
				'delete': 1,
				'if_owner': 1,  # Only own tokens
			},
		],
	}

	for doctype, permissions in doctype_permissions.items():
		for perm in permissions:
			role = perm.pop('role')

			# Check if permission already exists
			exists = frappe.db.exists('Custom DocPerm', {
				'parent': doctype,
				'role': role,
			})

			if not exists:
				try:
					doc = frappe.get_doc('DocType', doctype)
					doc.append('permissions', {
						'role': role,
						**perm
					})
					doc.save(ignore_permissions=True)
					print(f"  ✓ Added {role} permission to {doctype}")
				except Exception as e:
					print(f"  ✗ Error adding {role} to {doctype}: {e}")


def add_database_indexes():
	"""Add database indexes for better query performance"""
	print("Adding database indexes...")

	indexes = [
		# Conversation status and timestamp index
		"""
		CREATE INDEX IF NOT EXISTS idx_chat_conversation_status
		ON `tabChat Conversation` (status, last_message_at)
		""",

		# Contact mapping index
		"""
		CREATE INDEX IF NOT EXISTS idx_chat_contact_mapping
		ON `tabChat Contact Mapping` (erpnext_contact, chat_account_id)
		""",

		# Conversation mapping index
		"""
		CREATE INDEX IF NOT EXISTS idx_chat_conversation_mapping_contact
		ON `tabChat Conversation Mapping` (erpnext_contact)
		""",

		"""
		CREATE INDEX IF NOT EXISTS idx_chat_conversation_mapping_lead
		ON `tabChat Conversation Mapping` (erpnext_lead)
		""",

		# User token index
		"""
		CREATE INDEX IF NOT EXISTS idx_chat_user_token_status
		ON `tabChat User Token` (token_status, user)
		""",
	]

	for index_sql in indexes:
		try:
			frappe.db.sql(index_sql)
			print(f"  ✓ Index created")
		except Exception as e:
			print(f"  ✗ Error creating index: {e}")

	frappe.db.commit()


def update_webhook_url():
	"""Update webhook URL display in settings"""
	try:
		settings = frappe.get_single("Chat Integration Settings")
		site_url = frappe.utils.get_url()
		webhook_url = f"{site_url}/api/method/chat_bridge.webhook.handle"

		frappe.db.set_value(
			"Chat Integration Settings",
			"Chat Integration Settings",
			"webhook_url_display",
			webhook_url
		)
		print(f"✓ Webhook URL set to: {webhook_url}")
	except Exception as e:
		print(f"✗ Error updating webhook URL: {e}")
