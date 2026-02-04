"""
Communication Hub Document Event Handlers

Handles document lifecycle events for Communication Hub:
- after_insert: Initialize hub, start AI processing
- on_update: Handle status changes, trigger notifications
- before_submit: Finalize conversation, calculate metrics
"""

import frappe
from frappe import _
from datetime import datetime


def on_hub_created(doc, method):
	"""
	Handle Communication Hub creation.

	Args:
		doc: Communication Hub document
		method: Event method name
	"""
	try:
		# Set default values if not provided
		if not doc.ai_mode:
			settings = frappe.get_single("AI Communications Hub Settings")
			doc.ai_mode = settings.default_ai_mode or "Autonomous"

		# Set initial timestamps
		doc.first_response_at = None
		doc.conversation_started_at = datetime.now()

		# Initialize context
		if not doc.context_summary:
			doc.context_summary = ""

		# Log creation
		frappe.logger().info(f"Communication Hub created: {doc.name} - Channel: {doc.channel}")

		# Notify agents if HITL mode
		if doc.ai_mode == "HITL":
			notify_agents_new_conversation(doc)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Hub Creation Error: {doc.name}")


def on_hub_updated(doc, method):
	"""
	Handle Communication Hub updates.

	Args:
		doc: Communication Hub document
		method: Event method name
	"""
	try:
		# Check for status changes
		old_status = doc.get_doc_before_save()
		if old_status:
			old_status = old_status.get("status")

		# Handle status transitions
		if old_status != doc.status:
			handle_status_change(doc, old_status, doc.status)

		# Check for AI mode changes
		old_mode = doc.get_doc_before_save()
		if old_mode:
			old_mode = old_mode.get("ai_mode")

		if old_mode != doc.ai_mode:
			handle_ai_mode_change(doc, old_mode, doc.ai_mode)

		# Update context summary if needed
		if doc.status == "In Progress" and not doc.context_summary:
			update_context_summary(doc)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Hub Update Error: {doc.name}")


def before_hub_closed(doc, method):
	"""
	Handle Communication Hub closure/submission.

	Args:
		doc: Communication Hub document
		method: Event method name
	"""
	try:
		# Calculate resolution metrics
		calculate_resolution_metrics(doc)

		# Generate conversation summary
		if not doc.resolution_summary:
			doc.resolution_summary = generate_conversation_summary(doc)

		# Update customer metrics
		if doc.customer:
			update_customer_conversation_metrics(doc.customer)

		# Log closure
		frappe.logger().info(f"Communication Hub closed: {doc.name} - Status: {doc.status}")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Hub Closure Error: {doc.name}")


def handle_status_change(doc, old_status, new_status):
	"""Handle conversation status transitions"""

	# Open -> In Progress
	if old_status == "Open" and new_status == "In Progress":
		if not doc.first_response_at:
			doc.first_response_at = datetime.now()

	# Any -> Escalated
	elif new_status == "Escalated":
		notify_agents_escalation(doc)
		doc.escalated_at = datetime.now()

	# Any -> Resolved
	elif new_status == "Resolved":
		doc.resolved_at = datetime.now()
		if doc.conversation_started_at:
			delta = datetime.now() - doc.conversation_started_at
			doc.resolution_time = delta.total_seconds() / 60  # Minutes


def handle_ai_mode_change(doc, old_mode, new_mode):
	"""Handle AI mode transitions"""

	# Autonomous -> HITL (escalation)
	if old_mode == "Autonomous" and new_mode == "HITL":
		notify_agents_hitl_request(doc)

	# HITL -> Takeover (agent takes over)
	elif new_mode == "Takeover":
		doc.agent_takeover_at = datetime.now()
		frappe.publish_realtime(
			event="agent_takeover",
			message={"hub_id": doc.name, "agent": frappe.session.user},
			doctype="Communication Hub",
			docname=doc.name
		)

	# Takeover -> Autonomous (hand back to AI)
	elif old_mode == "Takeover" and new_mode == "Autonomous":
		frappe.publish_realtime(
			event="ai_resumed",
			message={"hub_id": doc.name},
			doctype="Communication Hub",
			docname=doc.name
		)


def calculate_resolution_metrics(doc):
	"""Calculate resolution time and other metrics"""

	# Get message count
	messages = frappe.get_all(
		"Communication Message",
		filters={"communication_hub": doc.name},
		fields=["sender_type", "timestamp"]
	)

	doc.total_messages = len(messages)
	doc.customer_messages = len([m for m in messages if m.sender_type == "Customer"])
	doc.ai_messages = len([m for m in messages if m.sender_type == "AI"])
	doc.agent_messages = len([m for m in messages if m.sender_type == "Agent"])

	# Calculate response times
	if len(messages) >= 2:
		customer_msgs = sorted(
			[m for m in messages if m.sender_type == "Customer"],
			key=lambda x: x.timestamp
		)
		response_msgs = sorted(
			[m for m in messages if m.sender_type in ["AI", "Agent"]],
			key=lambda x: x.timestamp
		)

		if customer_msgs and response_msgs:
			first_customer = customer_msgs[0].timestamp
			first_response = response_msgs[0].timestamp
			if first_response > first_customer:
				doc.first_response_time = (first_response - first_customer).total_seconds()


def generate_conversation_summary(doc):
	"""Generate AI summary of conversation"""
	try:
		from ai_comms_hub.api.llm import summarize_text

		# Get all messages
		messages = frappe.get_all(
			"Communication Message",
			filters={"communication_hub": doc.name},
			fields=["sender_type", "content", "timestamp"],
			order_by="timestamp asc"
		)

		if not messages:
			return ""

		# Build conversation text
		conversation_text = "\n".join([
			f"{m.sender_type}: {m.content[:500]}"
			for m in messages
		])

		# Summarize
		summary = summarize_text(conversation_text)
		return summary

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Conversation Summary Error")
		return ""


def update_context_summary(doc):
	"""Update running context summary for ongoing conversation"""
	try:
		# Get recent messages
		messages = frappe.get_all(
			"Communication Message",
			filters={"communication_hub": doc.name},
			fields=["sender_type", "content"],
			order_by="timestamp desc",
			limit=5
		)

		if messages:
			context = "\n".join([
				f"{m.sender_type}: {m.content[:200]}"
				for m in reversed(messages)
			])
			doc.context_summary = context[:2000]

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Context Update Error")


def update_customer_conversation_metrics(customer_name):
	"""Update customer's conversation statistics"""
	try:
		# Get all customer conversations
		conversations = frappe.get_all(
			"Communication Hub",
			filters={"customer": customer_name},
			fields=["status", "ai_mode", "sentiment", "resolution_time"]
		)

		total = len(conversations)
		resolved = len([c for c in conversations if c.status == "Resolved"])
		ai_resolved = len([c for c in conversations if c.status == "Resolved" and c.ai_mode != "Takeover"])

		# Update customer custom fields (if they exist)
		if frappe.db.has_column("Customer", "total_ai_conversations"):
			frappe.db.set_value(
				"Customer",
				customer_name,
				{
					"total_ai_conversations": total,
					"ai_resolution_rate": (ai_resolved / total * 100) if total > 0 else 0
				},
				update_modified=False
			)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Customer Metrics Update Error: {customer_name}")


def notify_agents_new_conversation(doc):
	"""Notify agents of new HITL conversation"""
	agents = get_available_agents()

	for agent in agents:
		frappe.publish_realtime(
			event="new_hitl_conversation",
			message={
				"hub_id": doc.name,
				"customer": doc.customer_name or doc.customer,
				"channel": doc.channel,
				"subject": doc.subject
			},
			user=agent
		)


def notify_agents_escalation(doc):
	"""Notify agents of escalated conversation"""
	agents = get_available_agents()

	for agent in agents:
		frappe.publish_realtime(
			event="conversation_escalated",
			message={
				"hub_id": doc.name,
				"customer": doc.customer_name or doc.customer,
				"channel": doc.channel,
				"reason": doc.escalation_reason or "Manual escalation"
			},
			user=agent
		)


def notify_agents_hitl_request(doc):
	"""Notify agents of HITL request from AI"""
	agents = get_available_agents()

	for agent in agents:
		frappe.publish_realtime(
			event="hitl_request",
			message={
				"hub_id": doc.name,
				"customer": doc.customer_name or doc.customer,
				"channel": doc.channel,
				"reason": doc.escalation_reason or "AI requested human review"
			},
			user=agent
		)


def get_available_agents():
	"""Get list of users with Customer Support role"""
	return frappe.get_all(
		"Has Role",
		filters={"role": "Customer Support", "parenttype": "User"},
		pluck="parent"
	)
