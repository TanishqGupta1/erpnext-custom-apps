# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import json


class CommunicationMessage(Document):
	"""
	Individual message within a Communication Hub conversation.

	Stores message content, sender information, delivery status, and function call results.
	"""

	def autoname(self):
		"""Set the name of the document"""
		# Name is auto-generated: format:MSG-{communication_hub}-{#####}
		pass

	def before_insert(self):
		"""Before inserting new message"""
		# Set timestamp if not provided
		if not self.timestamp:
			self.timestamp = datetime.now()

		# Set default delivery status
		if not self.delivery_status:
			self.delivery_status = "Pending"

	def validate(self):
		"""Validate document before save"""
		# Ensure communication hub exists
		if not frappe.db.exists("Communication Hub", self.communication_hub):
			frappe.throw(_("Communication Hub {0} does not exist").format(self.communication_hub))

		# Validate sender type
		if self.sender_type not in ["Customer", "AI", "Agent", "System"]:
			frappe.throw(_("Invalid sender type: {0}").format(self.sender_type))

		# Validate function call fields
		if self.is_function_call:
			if not self.function_name:
				frappe.throw(_("Function name is required for function calls"))

			# Validate function_args is valid JSON
			if self.function_args:
				try:
					json.loads(self.function_args)
				except json.JSONDecodeError:
					frappe.throw(_("Function arguments must be valid JSON"))

			# Validate function_result is valid JSON
			if self.function_result:
				try:
					json.loads(self.function_result)
				except json.JSONDecodeError:
					frappe.throw(_("Function result must be valid JSON"))

	def after_insert(self):
		"""After message is inserted"""
		# Update parent Communication Hub
		self.update_parent_hub()

		# Send real-time notification
		self.send_realtime_notification()

		# Process auto-delivery if from AI or Agent
		if self.sender_type in ["AI", "Agent"] and self.delivery_status == "Pending":
			self.enqueue_delivery()

	def on_update(self):
		"""After message is updated"""
		# If delivery status changed to "Read", update read timestamp
		if self.delivery_status == "Read" and not self.read_at:
			self.read_at = datetime.now()
			self.read_by_customer = 1

	def update_parent_hub(self):
		"""Update parent Communication Hub with new message count"""
		hub = frappe.get_doc("Communication Hub", self.communication_hub)

		# Update message counts
		hub.total_messages = frappe.db.count(
			"Communication Message",
			{"communication_hub": self.communication_hub}
		)

		hub.ai_messages = frappe.db.count(
			"Communication Message",
			{"communication_hub": self.communication_hub, "sender_type": "AI"}
		)

		hub.agent_messages = frappe.db.count(
			"Communication Message",
			{"communication_hub": self.communication_hub, "sender_type": "Agent"}
		)

		hub.updated_at = datetime.now()
		hub.save(ignore_permissions=True)

	def send_realtime_notification(self):
		"""Send real-time notification to connected clients"""
		frappe.publish_realtime(
			event="new_message",
			message={
				"hub_id": self.communication_hub,
				"message_id": self.name,
				"sender_type": self.sender_type,
				"sender_name": self.sender_name,
				"content": self.content[:100],  # First 100 chars
				"timestamp": str(self.timestamp)
			},
			doctype="Communication Hub",
			docname=self.communication_hub
		)

	def enqueue_delivery(self):
		"""Enqueue message for delivery via appropriate channel"""
		frappe.enqueue(
			"ai_comms_hub.api.message.deliver_message",
			message_id=self.name,
			queue="default",
			timeout=300
		)

	@frappe.whitelist()
	def mark_as_delivered(self, platform_message_id=None):
		"""
		Mark message as delivered.

		Args:
			platform_message_id (str, optional): Platform-specific message ID
		"""
		self.delivery_status = "Delivered"
		if platform_message_id:
			self.platform_message_id = platform_message_id
		self.save()

		return {"success": True, "status": "Delivered"}

	@frappe.whitelist()
	def mark_as_read(self):
		"""Mark message as read by customer"""
		self.delivery_status = "Read"
		self.read_by_customer = 1
		self.read_at = datetime.now()
		self.save()

		return {"success": True, "status": "Read"}

	@frappe.whitelist()
	def mark_as_failed(self, error_message):
		"""
		Mark message as failed.

		Args:
			error_message (str): Error description
		"""
		self.delivery_status = "Failed"
		self.delivery_error = error_message
		self.retry_count += 1
		self.save()

		# If retry count is below threshold, retry
		if self.retry_count < 3:
			frappe.enqueue(
				"ai_comms_hub.api.message.deliver_message",
				message_id=self.name,
				queue="default",
				timeout=300,
				enqueue_after_commit=True
			)

		return {"success": True, "status": "Failed", "retry_count": self.retry_count}

	def execute_function_call(self):
		"""
		Execute the function call specified in this message.

		Returns:
			dict: Function execution result
		"""
		if not self.is_function_call:
			return {"error": "This is not a function call message"}

		try:
			# Parse function arguments
			args = json.loads(self.function_args) if self.function_args else {}

			# Get function from registry
			from ai_comms_hub.api.functions import get_function_handler

			handler = get_function_handler(self.function_name)
			if not handler:
				raise Exception(f"Function '{self.function_name}' not found")

			# Execute function
			result = handler(**args)

			# Store result
			self.function_result = json.dumps(result, indent=2)
			self.function_success = 1
			self.save()

			return result

		except Exception as e:
			error_msg = str(e)
			self.function_error = error_msg
			self.function_success = 0
			self.save()

			frappe.log_error(
				f"Function call failed: {error_msg}",
				f"Function: {self.function_name}"
			)

			return {"error": error_msg}


# Helper functions

@frappe.whitelist()
def create_message(hub_id, content, sender_type, sender_name=None, is_function_call=False,
                   function_name=None, function_args=None):
	"""
	Create a new message in a conversation.

	Args:
		hub_id (str): Communication Hub ID
		content (str): Message content
		sender_type (str): Customer, AI, Agent, or System
		sender_name (str, optional): Sender's name
		is_function_call (bool, optional): Whether this is a function call
		function_name (str, optional): Function name if function call
		function_args (dict, optional): Function arguments if function call

	Returns:
		dict: Created message document
	"""
	# Verify hub exists
	if not frappe.db.exists("Communication Hub", hub_id):
		frappe.throw(_("Communication Hub {0} does not exist").format(hub_id))

	# Create message
	message = frappe.get_doc({
		"doctype": "Communication Message",
		"communication_hub": hub_id,
		"sender_type": sender_type,
		"sender_name": sender_name or sender_type,
		"content": content,
		"timestamp": datetime.now(),
		"is_function_call": is_function_call,
		"function_name": function_name,
		"function_args": json.dumps(function_args) if function_args else None
	})

	message.insert()

	# If function call, execute it
	if is_function_call:
		result = message.execute_function_call()
		return {
			"message": message.as_dict(),
			"function_result": result
		}

	return message.as_dict()


@frappe.whitelist()
def get_conversation_messages(hub_id, limit=50, offset=0):
	"""
	Get messages for a conversation.

	Args:
		hub_id (str): Communication Hub ID
		limit (int, optional): Number of messages to return
		offset (int, optional): Pagination offset

	Returns:
		list: List of message documents
	"""
	messages = frappe.get_all(
		"Communication Message",
		filters={"communication_hub": hub_id},
		fields=[
			"name", "sender_type", "sender_name", "content", "timestamp",
			"is_function_call", "function_name", "function_result",
			"delivery_status", "read_by_customer"
		],
		order_by="timestamp asc",
		limit_start=offset,
		limit_page_length=limit
	)

	return messages


@frappe.whitelist()
def search_messages(query, hub_id=None, limit=20):
	"""
	Search messages by content.

	Args:
		query (str): Search query
		hub_id (str, optional): Limit search to specific hub
		limit (int, optional): Number of results

	Returns:
		list: Matching messages
	"""
	filters = [
		["Communication Message", "content", "like", f"%{query}%"]
	]

	if hub_id:
		filters.append(["Communication Message", "communication_hub", "=", hub_id])

	messages = frappe.get_all(
		"Communication Message",
		filters=filters,
		fields=[
			"name", "communication_hub", "sender_type", "sender_name",
			"content", "timestamp"
		],
		order_by="timestamp desc",
		limit_page_length=limit
	)

	return messages
