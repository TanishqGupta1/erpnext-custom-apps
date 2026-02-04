import frappe
from frappe import _

@frappe.whitelist()
def get_conversations(filters=None, limit=50, offset=0):
	"""Get list of conversations with filters"""
	filters = frappe.parse_json(filters) if filters else {}

	# Ensure limit and offset are integers
	limit = int(limit)
	offset = int(offset)

	# Build filter conditions
	conditions = []
	values = []

	if filters.get("status"):
		conditions.append("status = %s")
		values.append(filters["status"])

	if filters.get("priority"):
		conditions.append("priority = %s")
		values.append(filters["priority"])

	if filters.get("assigned_to"):
		conditions.append("assigned_to = %s")
		values.append(filters["assigned_to"])

	if filters.get("contact"):
		conditions.append("contact = %s")
		values.append(filters["contact"])

	if filters.get("search"):
		conditions.append("(contact_display LIKE %s OR last_message_preview LIKE %s)")
		search_term = f"%{filters['search']}%"
		values.extend([search_term, search_term])

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	conversations = frappe.db.sql(f"""
		SELECT
			name,
			chat_conversation_id,
			contact_display,
			contact,
			status,
			priority,
			assigned_to,
			last_message_preview,
			last_message_at,
			channel,
			customer,
			lead,
			issue
		FROM `tabChat Conversation`
		WHERE {where_clause}
		ORDER BY last_message_at DESC
		LIMIT {limit} OFFSET {offset}
	""", values, as_dict=True)

	return conversations

@frappe.whitelist()
def get_conversation_details(conversation_name):
	"""Get full conversation details with messages"""
	conversation = frappe.get_doc("Chat Conversation", conversation_name)

	# Get contact details if linked
	contact_info = None
	if conversation.contact:
		contact_info = frappe.db.get_value(
			"Contact",
			conversation.contact,
			["email_id", "mobile_no", "phone", "company_name"],
			as_dict=True
		)

	# Get messages - CORRECT field names: message_id, direction, sent_at
	messages = frappe.db.sql("""
		SELECT
			message_id,
			direction,
			content,
			sender_name,
			sender_type,
			sent_at,
			is_private
		FROM `tabChat Message`
		WHERE parent = %s
		ORDER BY sent_at ASC
	""", conversation.name, as_dict=True)

	# Get labels - join with CRM Label to get label_name and color
	labels = frappe.db.sql("""
		SELECT
			cl.label_name,
			cl.color
		FROM `tabChat Conversation Label` ccl
		LEFT JOIN `tabCRM Label` cl ON ccl.crm_label = cl.name
		WHERE ccl.parent = %s
	""", conversation.name, as_dict=True)

	return {
		"conversation": conversation.as_dict(),
		"contact_info": contact_info,
		"messages": messages,
		"labels": labels
	}

@frappe.whitelist()
def send_message(conversation_name, message, message_type="outgoing", is_private=False):
	"""Send a message in a conversation"""
	conversation = frappe.get_doc("Chat Conversation", conversation_name)

	# Map message_type to direction
	direction_map = {
		"outgoing": "Outgoing",
		"private": "Private",
		"incoming": "Incoming"
	}
	direction = direction_map.get(message_type, "Outgoing")

	# Generate unique message ID
	import time
	message_id = f"msg_{int(time.time())}_{conversation_name}"

	# Add message to conversation
	message_row = conversation.append("messages", {
		"message_id": message_id,
		"direction": direction,
		"content": message,
		"sender_name": frappe.session.user,
		"sender_type": "agent",
		"sent_at": frappe.utils.now(),
		"is_private": 1 if is_private else 0
	})

	conversation.last_message_preview = message[:200]
	conversation.last_message_at = frappe.utils.now()
	conversation.save(ignore_permissions=True)

	# TODO: Send to Chatwoot via API

	return message_row.as_dict()

@frappe.whitelist()
def update_conversation_field(conversation_name, fieldname, value):
	"""Update a single field on a conversation"""
	allowed_fields = ["status", "priority", "assigned_to", "contact", "customer", "lead", "issue", "notes"]

	if fieldname not in allowed_fields:
		frappe.throw(_("Field {0} cannot be updated").format(fieldname))

	conversation = frappe.get_doc("Chat Conversation", conversation_name)
	conversation.set(fieldname, value)
	conversation.save(ignore_permissions=True)

	return {"success": True}

@frappe.whitelist()
def get_filter_options():
	"""Get available filter options"""
	return {
		"statuses": ["Open", "Pending", "Snoozed", "Resolved", "Closed"],
		"priorities": ["None", "Low", "Medium", "High", "Urgent"],
		"users": frappe.get_all("User", filters={"enabled": 1}, fields=["name", "full_name"])
	}
