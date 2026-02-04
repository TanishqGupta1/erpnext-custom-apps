"""
AI Engine

Core AI response generation logic that orchestrates:
- RAG knowledge retrieval
- LLM completion
- Function calling
- Response delivery
- HITL escalation
"""

import frappe
from frappe import _
from datetime import datetime
import json


# Keywords that trigger HITL escalation
ESCALATION_TRIGGERS = [
	"speak to human", "talk to human", "real person", "human agent",
	"manager", "supervisor", "complaint", "lawyer", "legal",
	"refund", "cancel subscription", "close account", "very angry",
	"frustrated", "unacceptable", "terrible service"
]

# Confidence threshold for HITL escalation
CONFIDENCE_THRESHOLD = 0.6


def generate_response(hub_id, message_id):
	"""
	Generate AI response for a customer message.

	Args:
		hub_id (str): Communication Hub ID
		message_id (str): Triggering message ID

	Returns:
		dict: Response details or None
	"""
	try:
		# Get hub and check AI mode
		hub = frappe.get_doc("Communication Hub", hub_id)

		if hub.ai_mode not in ["Autonomous", "HITL"]:
			return None  # Don't generate if in Takeover or Manual mode

		# Get latest customer message
		customer_msg = frappe.get_doc("Communication Message", message_id)

		# Check for escalation triggers
		if should_escalate(customer_msg.content):
			return handle_escalation(hub, customer_msg, "Customer requested human assistance")

		# Get conversation history
		conversation = get_conversation_history(hub_id, limit=10)

		# Query knowledge base
		rag_results = []
		if should_use_rag(customer_msg.content):
			try:
				from ai_comms_hub.api.rag import query_knowledge_base
				rag_results = query_knowledge_base(customer_msg.content, top_k=3)
			except Exception as e:
				frappe.log_error(f"RAG query failed: {str(e)}", "AI Engine RAG Error")

		# Check RAG confidence - escalate if too low and question seems important
		if rag_results and is_important_question(customer_msg.content):
			avg_confidence = sum(r.get("score", 0) for r in rag_results) / len(rag_results)
			if avg_confidence < CONFIDENCE_THRESHOLD:
				return handle_escalation(hub, customer_msg, f"Low confidence ({avg_confidence:.2f}) for important question")

		# Generate response with function calling
		from ai_comms_hub.api.llm import generate_completion, build_function_definitions

		# Build system prompt
		system_prompt = build_system_prompt(hub.channel, rag_results, hub)

		# Build messages
		messages = [{"role": "system", "content": system_prompt}]
		for msg in conversation:
			role = "user" if msg["sender_type"] == "Customer" else "assistant"
			messages.append({"role": role, "content": msg["content"]})

		# Get function definitions
		functions = build_function_definitions()

		# Generate completion with function calling
		response = generate_completion(messages, functions=functions)

		# Check if function call was requested
		choice = response["choices"][0]
		message = choice["message"]

		if message.get("function_call"):
			# Execute function and get result
			function_result = execute_function_call(
				message["function_call"],
				hub,
				customer_msg
			)

			# If function failed or needs human, escalate
			if function_result.get("needs_human"):
				return handle_escalation(hub, customer_msg, function_result.get("reason", "Function requires human"))

			# Add function result to context and regenerate
			messages.append({
				"role": "assistant",
				"content": None,
				"function_call": message["function_call"]
			})
			messages.append({
				"role": "function",
				"name": message["function_call"]["name"],
				"content": json.dumps(function_result)
			})

			# Generate final response with function result
			response = generate_completion(messages)
			choice = response["choices"][0]
			message = choice["message"]

			# Create function call message record
			func_msg = frappe.get_doc({
				"doctype": "Communication Message",
				"communication_hub": hub_id,
				"sender_type": "System",
				"sender_name": "Function Call",
				"content": f"[Function: {message['function_call']['name']}]",
				"timestamp": datetime.now(),
				"is_function_call": 1,
				"function_name": message["function_call"]["name"],
				"function_result": json.dumps(function_result)
			})
			func_msg.insert()

		# Get final response content
		response_content = message.get("content", "")

		# Check for uncertainty markers in response
		if contains_uncertainty(response_content):
			if hub.ai_mode == "HITL":
				return handle_hitl_draft(hub, customer_msg, response_content)

		# Format response for platform
		formatted_content = format_for_platform(response_content, hub.channel)

		# Create AI message
		ai_msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub_id,
			"sender_type": "AI",
			"sender_name": "AI Assistant",
			"content": formatted_content,
			"timestamp": datetime.now(),
			"delivery_status": "Pending"
		})
		ai_msg.insert()
		frappe.db.commit()

		# Update hub with RAG info
		if rag_results:
			hub.db_set("knowledge_base_used", 1)
			hub.db_set("rag_documents", json.dumps([
				{"id": doc.get("id", ""), "title": doc.get("title", ""), "score": doc.get("score", 0)}
				for doc in rag_results
			]))
			avg_score = sum(doc.get("score", 0) for doc in rag_results) / len(rag_results)
			hub.db_set("rag_confidence", avg_score * 100)

		# Analyze sentiment asynchronously
		frappe.enqueue(
			"ai_comms_hub.api.ai_engine.analyze_and_update_sentiment",
			hub_id=hub_id,
			content=customer_msg.content,
			queue="short"
		)

		# Update conversation context summary
		frappe.enqueue(
			"ai_comms_hub.api.ai_engine.update_context_summary",
			hub_id=hub_id,
			queue="short"
		)

		return {
			"success": True,
			"message_id": ai_msg.name,
			"content": formatted_content
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"AI Response Generation Error: {hub_id}")
		# Try to send a fallback message
		try:
			send_fallback_message(hub_id)
		except Exception:
			pass
		return {"success": False, "error": str(e)}


def generate_ai_response(hub_id, content):
	"""
	Generate AI response synchronously (for agent bot webhooks).

	Args:
		hub_id (str): Communication Hub ID
		content (str): Customer message content

	Returns:
		str: AI response content or None
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)

		# Get conversation history
		conversation = get_conversation_history(hub_id, limit=5)

		# Query knowledge base
		rag_results = []
		if should_use_rag(content):
			try:
				from ai_comms_hub.api.rag import query_knowledge_base
				rag_results = query_knowledge_base(content, top_k=3)
			except Exception:
				pass

		# Build prompt
		system_prompt = build_system_prompt(hub.channel, rag_results, hub)

		messages = [{"role": "system", "content": system_prompt}]
		for msg in conversation:
			role = "user" if msg["sender_type"] == "Customer" else "assistant"
			messages.append({"role": role, "content": msg["content"]})

		# Add current message
		messages.append({"role": "user", "content": content})

		# Generate
		from ai_comms_hub.api.llm import generate_completion
		response = generate_completion(messages)

		return response["choices"][0]["message"]["content"]

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Sync AI Response Error: {hub_id}")
		return None


def build_system_prompt(platform, rag_context=None, hub=None):
	"""
	Build comprehensive system prompt with platform guidelines and context.

	Args:
		platform (str): Channel name
		rag_context (list): Knowledge base results
		hub (Document): Communication Hub document

	Returns:
		str: System prompt
	"""
	# Platform-specific guidelines
	platform_guidelines = {
		"Voice": {
			"tone": "conversational and clear",
			"length": "concise, 1-2 sentences per response",
			"style": "natural speech, avoid complex words, no special characters"
		},
		"SMS": {
			"tone": "friendly and brief",
			"length": "160 characters ideal, max 320",
			"style": "no emojis, clear and direct"
		},
		"WhatsApp": {
			"tone": "friendly and conversational",
			"length": "up to 1000 characters",
			"style": "casual, light emoji use allowed"
		},
		"Chat": {
			"tone": "helpful and professional",
			"length": "2-4 sentences typical",
			"style": "clear formatting, can use bullet points"
		},
		"Facebook": {
			"tone": "friendly and conversational",
			"length": "up to 2000 characters",
			"style": "casual, emojis sparingly"
		},
		"Instagram": {
			"tone": "casual and visual",
			"length": "up to 1000 characters",
			"style": "short paragraphs, emojis encouraged"
		},
		"Twitter": {
			"tone": "concise and engaging",
			"length": "280 characters maximum",
			"style": "very brief, strategic emoji use"
		},
		"LinkedIn": {
			"tone": "professional but warm",
			"length": "up to 1300 characters",
			"style": "professional, minimal emojis"
		},
		"Email": {
			"tone": "professional and helpful",
			"length": "2-3 paragraphs",
			"style": "proper grammar, formatted with paragraphs, include greeting and sign-off"
		}
	}

	guidelines = platform_guidelines.get(platform, platform_guidelines["Chat"])

	# Get company info
	company_name = frappe.db.get_single_value("AI Communications Hub Settings", "company_name") or "our company"

	prompt = f"""You are an AI customer service assistant for {company_name}, communicating via {platform}.

## Communication Guidelines for {platform}:
- Tone: {guidelines['tone']}
- Length: {guidelines['length']}
- Style: {guidelines['style']}

## Core Instructions:
1. Be helpful, accurate, and professional
2. Use the knowledge base context when available
3. Never make up information - if unsure, say so
4. For complex issues, offer to connect with a human agent
5. Protect customer privacy - never repeat sensitive info back

## Escalation Triggers (say "Let me connect you with a team member"):
- Customer explicitly requests human help
- Complex billing/refund issues
- Legal or complaint matters
- Technical issues beyond your knowledge
- Customer expresses strong frustration

"""

	# Add customer context if available
	if hub:
		if hub.customer_name:
			prompt += f"\n## Customer: {hub.customer_name}\n"
		if hub.context:
			prompt += f"\n## Conversation Context:\n{hub.context}\n"

	# Add knowledge base context
	if rag_context:
		prompt += "\n## Knowledge Base Information:\n"
		for i, doc in enumerate(rag_context, 1):
			content = doc.get("content", "")[:500]  # Limit context size
			title = doc.get("title", f"Document {i}")
			prompt += f"\n### {title}\n{content}\n"

	prompt += """
## Response Format:
- Answer the customer's question directly
- Be concise but complete
- If using knowledge base info, integrate it naturally
- End with a helpful follow-up question or offer if appropriate
"""

	return prompt


def generate_email_response(hub_id, message_id):
	"""
	Generate AI email response with proper formatting.

	Args:
		hub_id (str): Communication Hub ID
		message_id (str): Triggering message ID
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)

		if hub.ai_mode not in ["Autonomous", "HITL"]:
			return

		# Generate response
		generate_response(hub_id, message_id)

		# Get the AI response we just created
		ai_message = frappe.get_all(
			"Communication Message",
			filters={
				"communication_hub": hub_id,
				"sender_type": "AI"
			},
			fields=["name", "content"],
			order_by="timestamp desc",
			limit=1
		)

		if not ai_message:
			return

		# Convert to HTML
		html_content = convert_to_email_html(ai_message[0]["content"])

		# Update message with HTML
		msg = frappe.get_doc("Communication Message", ai_message[0]["name"])
		msg.content_type = "html"
		msg.save()

		# Queue for email delivery
		frappe.enqueue(
			"ai_comms_hub.api.message.send_email",
			hub_id=hub_id,
			message_id=msg.name,
			queue="default"
		)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Email Response Error: {hub_id}")


def convert_to_email_html(text_content):
	"""
	Convert plain text AI response to HTML email format.

	Args:
		text_content (str): Plain text content

	Returns:
		str: HTML formatted content
	"""
	import re

	# Split into paragraphs
	paragraphs = text_content.split('\n\n')

	html_parts = ['<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">']

	for para in paragraphs:
		para = para.strip()
		if not para:
			continue

		# Check if it's a list (lines starting with - or *)
		if '\n-' in para or '\n*' in para:
			items = [item.strip('- *').strip() for item in para.split('\n') if item.strip()]
			html_parts.append('<ul style="margin: 10px 0; padding-left: 20px;">')
			for item in items:
				html_parts.append(f'<li style="margin: 5px 0;">{item}</li>')
			html_parts.append('</ul>')
		else:
			# Bold text between ** **
			para = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', para)
			html_parts.append(f'<p style="margin: 10px 0;">{para}</p>')

	html_parts.append('</div>')
	return ''.join(html_parts)


def get_conversation_history(hub_id, limit=10):
	"""
	Get conversation history for context.

	Args:
		hub_id (str): Communication Hub ID
		limit (int): Number of messages to retrieve

	Returns:
		list: Conversation messages
	"""
	messages = frappe.get_all(
		"Communication Message",
		filters={"communication_hub": hub_id},
		fields=["sender_type", "sender_name", "content", "timestamp"],
		order_by="timestamp asc",
		limit=limit
	)

	return messages


def should_use_rag(message_content):
	"""
	Determine if RAG knowledge search should be used.

	Args:
		message_content (str): Customer message

	Returns:
		bool: True if RAG should be used
	"""
	# Keywords that suggest knowledge base lookup
	knowledge_keywords = [
		"product", "price", "cost", "how to", "what is",
		"policy", "procedure", "specification", "feature",
		"warranty", "return", "shipping", "delivery"
	]

	content_lower = message_content.lower()

	return any(keyword in content_lower for keyword in knowledge_keywords)


def handle_hitl_request(hub_id, reason=""):
	"""
	Handle Human-in-the-Loop escalation request.

	Args:
		hub_id (str): Communication Hub ID
		reason (str): Reason for escalation
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)
		hub.ai_mode = "HITL"
		hub.save()

		# Notify agents
		notify_agents_hitl(hub, reason)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"HITL Request Error: {hub_id}")


def notify_agents_hitl(hub, reason=""):
	"""Send real-time notification to available agents"""
	# Get Customer Support role users
	agents = frappe.get_all(
		"User",
		filters={
			"enabled": 1,
			"name": ["in", frappe.get_all(
				"Has Role",
				filters={"role": "Customer Support"},
				pluck="parent"
			)]
		},
		pluck="name"
	)

	for agent in agents:
		frappe.publish_realtime(
			event="hitl_request",
			message={
				"hub_id": hub.name,
				"customer": hub.customer_name,
				"channel": hub.channel,
				"subject": hub.subject,
				"reason": reason
			},
			user=agent
		)


# ============================================
# Function Execution Handlers
# ============================================

def execute_function_call(function_call, hub, customer_msg):
	"""
	Execute a function call requested by the LLM.

	Args:
		function_call (dict): Function call with name and arguments
		hub (Document): Communication Hub
		customer_msg (Document): Customer message

	Returns:
		dict: Function execution result
	"""
	function_name = function_call.get("name")
	arguments = json.loads(function_call.get("arguments", "{}"))

	frappe.logger().info(f"Executing function: {function_name} with args: {arguments}")

	# Route to appropriate handler
	handlers = {
		"getOrderStatus": execute_get_order_status,
		"createQuote": execute_create_quote,
		"searchKnowledge": execute_search_knowledge,
		"scheduleAppointment": execute_schedule_appointment,
		"getProductInfo": execute_get_product_info,
		"getCustomerInfo": execute_get_customer_info,
		"checkInventory": execute_check_inventory
	}

	handler = handlers.get(function_name)
	if handler:
		try:
			return handler(arguments, hub, customer_msg)
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), f"Function Execution Error: {function_name}")
			return {
				"error": str(e),
				"needs_human": True,
				"reason": f"Function {function_name} failed: {str(e)}"
			}
	else:
		return {
			"error": f"Unknown function: {function_name}",
			"needs_human": False
		}


def execute_get_order_status(args, hub, customer_msg):
	"""Get order status from ERPNext"""
	order_number = args.get("order_number", "")

	# Try Sales Order first
	if frappe.db.exists("Sales Order", order_number):
		order = frappe.get_doc("Sales Order", order_number)
		return {
			"found": True,
			"order_type": "Sales Order",
			"order_number": order.name,
			"status": order.status,
			"customer": order.customer_name,
			"total": order.grand_total,
			"currency": order.currency,
			"delivery_status": order.delivery_status,
			"billing_status": order.billing_status,
			"transaction_date": str(order.transaction_date),
			"items": [
				{"item": item.item_name, "qty": item.qty, "rate": item.rate}
				for item in order.items[:5]  # Limit to 5 items
			]
		}

	# Try Sales Invoice
	if frappe.db.exists("Sales Invoice", order_number):
		invoice = frappe.get_doc("Sales Invoice", order_number)
		return {
			"found": True,
			"order_type": "Sales Invoice",
			"order_number": invoice.name,
			"status": invoice.status,
			"customer": invoice.customer_name,
			"total": invoice.grand_total,
			"currency": invoice.currency,
			"outstanding": invoice.outstanding_amount,
			"due_date": str(invoice.due_date) if invoice.due_date else None
		}

	# Try Delivery Note
	if frappe.db.exists("Delivery Note", order_number):
		dn = frappe.get_doc("Delivery Note", order_number)
		return {
			"found": True,
			"order_type": "Delivery Note",
			"order_number": dn.name,
			"status": dn.status,
			"customer": dn.customer_name,
			"posting_date": str(dn.posting_date)
		}

	# Search by customer if we have customer linked
	if hub.customer:
		recent_orders = frappe.get_all(
			"Sales Order",
			filters={
				"customer": hub.customer,
				"docstatus": ["!=", 2]
			},
			fields=["name", "status", "grand_total", "transaction_date"],
			order_by="transaction_date desc",
			limit=3
		)
		if recent_orders:
			return {
				"found": False,
				"message": f"Order {order_number} not found. Recent orders for this customer:",
				"recent_orders": recent_orders
			}

	return {
		"found": False,
		"message": f"Order {order_number} not found in the system."
	}


def execute_create_quote(args, hub, customer_msg):
	"""Create a quotation in ERPNext"""
	customer_name = args.get("customer_name")
	product_name = args.get("product_name")
	quantity = args.get("quantity", 1)
	specifications = args.get("specifications", "")

	# Find or use hub customer
	customer = hub.customer
	if not customer and customer_name:
		# Try to find customer
		customer = frappe.db.get_value("Customer", {"customer_name": ["like", f"%{customer_name}%"]}, "name")

	if not customer:
		return {
			"success": False,
			"needs_human": True,
			"reason": "Customer not found in system. Human needed to verify customer details."
		}

	# Find item
	item = frappe.db.get_value(
		"Item",
		{"item_name": ["like", f"%{product_name}%"], "disabled": 0},
		["name", "item_name", "standard_rate"],
		as_dict=True
	)

	if not item:
		return {
			"success": False,
			"message": f"Product '{product_name}' not found. Please provide exact product name.",
			"needs_human": False
		}

	# Create quotation
	try:
		quotation = frappe.get_doc({
			"doctype": "Quotation",
			"party_type": "Customer",
			"party_name": customer,
			"items": [{
				"item_code": item.name,
				"qty": quantity,
				"rate": item.standard_rate
			}],
			"notes": f"Created via AI Assistant\nSpecifications: {specifications}\nHub: {hub.name}"
		})
		quotation.insert()
		frappe.db.commit()

		return {
			"success": True,
			"quotation_id": quotation.name,
			"item": item.item_name,
			"quantity": quantity,
			"unit_price": item.standard_rate,
			"total": quantity * (item.standard_rate or 0),
			"message": f"Quotation {quotation.name} created successfully."
		}
	except Exception as e:
		return {
			"success": False,
			"needs_human": True,
			"reason": f"Failed to create quotation: {str(e)}"
		}


def execute_search_knowledge(args, hub, customer_msg):
	"""Search knowledge base"""
	query = args.get("query", "")

	try:
		from ai_comms_hub.api.rag import query_knowledge_base
		results = query_knowledge_base(query, top_k=3)

		if results:
			return {
				"found": True,
				"results": [
					{
						"title": r.get("title", ""),
						"content": r.get("content", "")[:500],
						"score": r.get("score", 0)
					}
					for r in results
				]
			}
		else:
			return {
				"found": False,
				"message": "No relevant information found in knowledge base."
			}
	except Exception as e:
		return {
			"found": False,
			"error": str(e)
		}


def execute_schedule_appointment(args, hub, customer_msg):
	"""Schedule appointment - creates Event in ERPNext"""
	customer_name = args.get("customer_name")
	preferred_date = args.get("preferred_date")
	preferred_time = args.get("preferred_time", "10:00")
	purpose = args.get("purpose", "Consultation")

	# This typically needs human confirmation
	return {
		"success": False,
		"needs_human": True,
		"reason": "Appointment scheduling requires human confirmation",
		"proposed": {
			"customer": customer_name,
			"date": preferred_date,
			"time": preferred_time,
			"purpose": purpose
		}
	}


def execute_get_product_info(args, hub, customer_msg):
	"""Get product information from ERPNext"""
	product_name = args.get("product_name", "")

	# Search for item
	items = frappe.get_all(
		"Item",
		filters={
			"item_name": ["like", f"%{product_name}%"],
			"disabled": 0
		},
		fields=["name", "item_name", "item_group", "description", "standard_rate", "stock_uom"],
		limit=3
	)

	if not items:
		# Try by item code
		items = frappe.get_all(
			"Item",
			filters={
				"name": ["like", f"%{product_name}%"],
				"disabled": 0
			},
			fields=["name", "item_name", "item_group", "description", "standard_rate", "stock_uom"],
			limit=3
		)

	if items:
		# Get stock for first item
		item = items[0]
		stock = frappe.db.sql("""
			SELECT SUM(actual_qty) as qty
			FROM `tabBin`
			WHERE item_code = %s
		""", item.name, as_dict=True)

		return {
			"found": True,
			"items": [{
				"code": i.name,
				"name": i.item_name,
				"group": i.item_group,
				"description": (i.description or "")[:300],
				"price": i.standard_rate,
				"uom": i.stock_uom
			} for i in items],
			"stock_available": stock[0].qty if stock and stock[0].qty else 0
		}

	return {
		"found": False,
		"message": f"No products found matching '{product_name}'"
	}


def execute_get_customer_info(args, hub, customer_msg):
	"""Get customer information"""
	# Use hub's linked customer
	if not hub.customer:
		return {
			"found": False,
			"message": "No customer linked to this conversation"
		}

	customer = frappe.get_doc("Customer", hub.customer)

	# Get recent transactions
	recent_orders = frappe.get_all(
		"Sales Order",
		filters={"customer": hub.customer, "docstatus": 1},
		fields=["name", "grand_total", "transaction_date"],
		order_by="transaction_date desc",
		limit=3
	)

	# Get outstanding
	outstanding = frappe.db.sql("""
		SELECT SUM(outstanding_amount) as total
		FROM `tabSales Invoice`
		WHERE customer = %s AND docstatus = 1
	""", hub.customer, as_dict=True)

	return {
		"found": True,
		"customer_name": customer.customer_name,
		"customer_group": customer.customer_group,
		"territory": customer.territory,
		"email": customer.email_id,
		"phone": customer.mobile_no,
		"recent_orders": recent_orders,
		"outstanding_amount": outstanding[0].total if outstanding and outstanding[0].total else 0
	}


def execute_check_inventory(args, hub, customer_msg):
	"""Check inventory availability"""
	product_name = args.get("product_name", "")

	# Find item
	item_code = frappe.db.get_value(
		"Item",
		{"item_name": ["like", f"%{product_name}%"], "disabled": 0},
		"name"
	)

	if not item_code:
		item_code = frappe.db.get_value(
			"Item",
			{"name": ["like", f"%{product_name}%"], "disabled": 0},
			"name"
		)

	if not item_code:
		return {
			"found": False,
			"message": f"Product '{product_name}' not found"
		}

	# Get stock by warehouse
	stock = frappe.db.sql("""
		SELECT warehouse, actual_qty, reserved_qty
		FROM `tabBin`
		WHERE item_code = %s AND actual_qty > 0
	""", item_code, as_dict=True)

	total_qty = sum(s.actual_qty for s in stock)
	total_reserved = sum(s.reserved_qty or 0 for s in stock)

	return {
		"found": True,
		"item_code": item_code,
		"total_available": total_qty,
		"reserved": total_reserved,
		"free_qty": total_qty - total_reserved,
		"warehouses": [
			{"warehouse": s.warehouse, "qty": s.actual_qty}
			for s in stock[:5]
		]
	}


# ============================================
# Helper Functions
# ============================================

def should_escalate(content):
	"""
	Check if message should trigger escalation to human.

	Args:
		content (str): Message content

	Returns:
		bool: True if should escalate
	"""
	content_lower = content.lower()
	return any(trigger in content_lower for trigger in ESCALATION_TRIGGERS)


def is_important_question(content):
	"""
	Check if question is important (pricing, policy, etc).

	Args:
		content (str): Message content

	Returns:
		bool: True if important
	"""
	important_keywords = [
		"price", "cost", "refund", "return", "warranty",
		"guarantee", "policy", "contract", "legal", "payment"
	]
	content_lower = content.lower()
	return any(keyword in content_lower for keyword in important_keywords)


def contains_uncertainty(response):
	"""
	Check if AI response contains uncertainty markers.

	Args:
		response (str): AI response

	Returns:
		bool: True if uncertain
	"""
	uncertainty_markers = [
		"i'm not sure", "i don't know", "i cannot find",
		"i'm unable to", "you may want to contact",
		"i don't have access", "beyond my knowledge"
	]
	response_lower = response.lower()
	return any(marker in response_lower for marker in uncertainty_markers)


def handle_escalation(hub, customer_msg, reason):
	"""
	Handle escalation to human agent.

	Args:
		hub (Document): Communication Hub
		customer_msg (Document): Customer message
		reason (str): Escalation reason

	Returns:
		dict: Escalation result
	"""
	# Update hub status
	hub.db_set("ai_mode", "HITL")
	hub.db_set("status", "Escalated")
	hub.db_set("escalation_reason", reason)

	# Create system message
	sys_msg = frappe.get_doc({
		"doctype": "Communication Message",
		"communication_hub": hub.name,
		"sender_type": "System",
		"sender_name": "System",
		"content": f"[Escalated to human: {reason}]",
		"timestamp": datetime.now()
	})
	sys_msg.insert()

	# Send acknowledgment to customer
	ack_content = "I'll connect you with a team member who can better assist you. Please hold on."
	ack_msg = frappe.get_doc({
		"doctype": "Communication Message",
		"communication_hub": hub.name,
		"sender_type": "AI",
		"sender_name": "AI Assistant",
		"content": format_for_platform(ack_content, hub.channel),
		"timestamp": datetime.now()
	})
	ack_msg.insert()
	frappe.db.commit()

	# Notify agents
	notify_agents_hitl(hub, reason)

	return {
		"success": True,
		"escalated": True,
		"reason": reason,
		"message_id": ack_msg.name
	}


def handle_hitl_draft(hub, customer_msg, draft_response):
	"""
	Handle HITL mode - save draft for human review.

	Args:
		hub (Document): Communication Hub
		customer_msg (Document): Customer message
		draft_response (str): AI draft response

	Returns:
		dict: HITL result
	"""
	# Save draft for review
	hub.db_set("ai_draft_response", draft_response)
	hub.db_set("status", "Pending Review")

	# Notify agents of draft ready
	notify_agents_hitl(hub, "AI draft ready for review")

	return {
		"success": True,
		"hitl_draft": True,
		"draft": draft_response
	}


def format_for_platform(content, platform):
	"""
	Format response content for specific platform.

	Args:
		content (str): Response content
		platform (str): Platform name

	Returns:
		str: Formatted content
	"""
	if not content:
		return content

	# Platform character limits
	limits = {
		"Twitter": 280,
		"SMS": 320,
		"WhatsApp": 4096,
		"Facebook": 2000,
		"Instagram": 1000,
		"LinkedIn": 1300
	}

	limit = limits.get(platform)
	if limit and len(content) > limit:
		content = content[:limit - 3] + "..."

	# Platform-specific formatting
	if platform == "Voice":
		# Remove markdown, special chars for TTS
		content = content.replace("**", "").replace("*", "")
		content = content.replace("#", "").replace("`", "")
		content = content.replace("\n\n", ". ").replace("\n", ". ")

	elif platform == "Email":
		# Keep markdown for email (will be converted to HTML)
		pass

	elif platform == "SMS":
		# Remove emojis and special formatting
		import re
		content = re.sub(r'[^\x00-\x7F]+', '', content)
		content = content.replace("\n\n", " ").replace("\n", " ")

	return content.strip()


def send_fallback_message(hub_id):
	"""
	Send fallback message when AI fails.

	Args:
		hub_id (str): Communication Hub ID
	"""
	hub = frappe.get_doc("Communication Hub", hub_id)

	fallback_content = "I apologize, but I'm having trouble processing your request. Let me connect you with a team member who can help."

	msg = frappe.get_doc({
		"doctype": "Communication Message",
		"communication_hub": hub_id,
		"sender_type": "AI",
		"sender_name": "AI Assistant",
		"content": format_for_platform(fallback_content, hub.channel),
		"timestamp": datetime.now()
	})
	msg.insert()

	# Escalate
	hub.db_set("ai_mode", "HITL")
	hub.db_set("status", "Escalated")
	hub.db_set("escalation_reason", "AI processing error")

	frappe.db.commit()

	notify_agents_hitl(hub, "AI processing error - fallback sent")


def analyze_and_update_sentiment(hub_id, content):
	"""
	Analyze sentiment and update hub (background job).

	Args:
		hub_id (str): Communication Hub ID
		content (str): Message content to analyze
	"""
	try:
		from ai_comms_hub.api.llm import classify_sentiment
		sentiment = classify_sentiment(content)
		frappe.db.set_value("Communication Hub", hub_id, "sentiment", sentiment)
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"Sentiment analysis failed: {str(e)}", "AI Engine")


def update_context_summary(hub_id):
	"""
	Update conversation context summary (background job).

	Args:
		hub_id (str): Communication Hub ID
	"""
	try:
		# Get recent messages
		messages = frappe.get_all(
			"Communication Message",
			filters={"communication_hub": hub_id},
			fields=["sender_type", "content"],
			order_by="timestamp desc",
			limit=10
		)

		if len(messages) < 3:
			return  # Not enough for summary

		# Build conversation text
		conv_text = "\n".join([
			f"{'Customer' if m.sender_type == 'Customer' else 'Assistant'}: {m.content[:200]}"
			for m in reversed(messages)
		])

		# Generate summary
		from ai_comms_hub.api.llm import generate_summary
		summary = generate_summary(
			conv_text,
			"Summarize this customer service conversation in 2-3 sentences, noting the main issue and current status:"
		)

		# Update hub
		frappe.db.set_value("Communication Hub", hub_id, "context", summary)
		frappe.db.commit()

	except Exception as e:
		frappe.log_error(f"Context summary failed: {str(e)}", "AI Engine")


@frappe.whitelist()
def approve_hitl_draft(hub_id, edited_response=None):
	"""
	Approve HITL draft response (with optional edits).

	Args:
		hub_id (str): Communication Hub ID
		edited_response (str, optional): Edited response content

	Returns:
		dict: Result
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)

		content = edited_response or hub.ai_draft_response
		if not content:
			return {"success": False, "error": "No draft response found"}

		# Create approved message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub_id,
			"sender_type": "AI",
			"sender_name": "AI Assistant (Approved)",
			"content": format_for_platform(content, hub.channel),
			"timestamp": datetime.now()
		})
		msg.insert()

		# Clear draft and update status
		hub.db_set("ai_draft_response", "")
		hub.db_set("status", "In Progress")
		hub.db_set("ai_mode", "Autonomous")

		frappe.db.commit()

		return {
			"success": True,
			"message_id": msg.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"HITL Approve Error: {hub_id}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def reject_hitl_draft(hub_id, agent_response):
	"""
	Reject HITL draft and send agent's response instead.

	Args:
		hub_id (str): Communication Hub ID
		agent_response (str): Agent's response to send

	Returns:
		dict: Result
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)

		# Create agent message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub_id,
			"sender_type": "Agent",
			"sender_name": frappe.session.user,
			"content": format_for_platform(agent_response, hub.channel),
			"timestamp": datetime.now()
		})
		msg.insert()

		# Clear draft and update status
		hub.db_set("ai_draft_response", "")
		hub.db_set("status", "In Progress")

		frappe.db.commit()

		return {
			"success": True,
			"message_id": msg.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"HITL Reject Error: {hub_id}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def takeover_conversation(hub_id, agent_user=None):
	"""
	Take over a conversation from AI - agent handles all responses.

	Args:
		hub_id (str): Communication Hub ID
		agent_user (str, optional): User taking over

	Returns:
		dict: Result
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)

		# Update to Takeover mode
		hub.db_set("ai_mode", "Takeover")
		hub.db_set("status", "In Progress")
		hub.db_set("assigned_to", agent_user or frappe.session.user)

		# Create system message
		sys_msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub_id,
			"sender_type": "System",
			"sender_name": "System",
			"content": f"[Conversation taken over by {frappe.utils.get_fullname(agent_user or frappe.session.user)}]",
			"timestamp": datetime.now()
		})
		sys_msg.insert()
		frappe.db.commit()

		# Notify via realtime
		frappe.publish_realtime(
			event="ai_mode_changed",
			message={
				"hub_id": hub_id,
				"ai_mode": "Takeover",
				"agent": agent_user or frappe.session.user
			}
		)

		return {"success": True}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Takeover Error: {hub_id}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def handback_conversation(hub_id):
	"""
	Hand conversation back to AI from agent takeover.

	Args:
		hub_id (str): Communication Hub ID

	Returns:
		dict: Result
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)

		# Update to Autonomous mode
		hub.db_set("ai_mode", "Autonomous")
		hub.db_set("status", "In Progress")

		# Create system message
		sys_msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub_id,
			"sender_type": "System",
			"sender_name": "System",
			"content": f"[Conversation handed back to AI by {frappe.utils.get_fullname()}]",
			"timestamp": datetime.now()
		})
		sys_msg.insert()
		frappe.db.commit()

		# Notify via realtime
		frappe.publish_realtime(
			event="ai_mode_changed",
			message={
				"hub_id": hub_id,
				"ai_mode": "Autonomous"
			}
		)

		return {"success": True}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Handback Error: {hub_id}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def generate_suggestion(hub_id):
	"""
	Generate an AI suggestion for agent to use/modify.

	Args:
		hub_id (str): Communication Hub ID

	Returns:
		dict: Result with suggestion
	"""
	try:
		hub = frappe.get_doc("Communication Hub", hub_id)

		# Get conversation history
		conversation = get_conversation_history(hub_id, limit=10)

		if not conversation:
			return {"success": False, "error": "No conversation history"}

		# Get last customer message
		customer_msgs = [m for m in conversation if m["sender_type"] == "Customer"]
		if not customer_msgs:
			return {"success": False, "error": "No customer messages found"}

		last_customer_msg = customer_msgs[-1]["content"]

		# Query knowledge base
		rag_results = []
		if should_use_rag(last_customer_msg):
			try:
				from ai_comms_hub.api.rag import query_knowledge_base
				rag_results = query_knowledge_base(last_customer_msg, top_k=3)
			except Exception:
				pass

		# Build prompt for suggestion
		from ai_comms_hub.api.llm import generate_completion

		system_prompt = build_system_prompt(hub.channel, rag_results, hub)
		system_prompt += "\n\nIMPORTANT: Generate a helpful response suggestion for a human agent to review and modify. Be thorough but let the agent add their personal touch."

		messages = [{"role": "system", "content": system_prompt}]
		for msg in conversation:
			role = "user" if msg["sender_type"] == "Customer" else "assistant"
			messages.append({"role": role, "content": msg["content"]})

		response = generate_completion(messages)
		suggestion = response["choices"][0]["message"]["content"]

		return {
			"success": True,
			"suggestion": suggestion
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Generate Suggestion Error: {hub_id}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_hitl_stats():
	"""
	Get HITL dashboard statistics.

	Returns:
		dict: Statistics
	"""
	try:
		pending_count = frappe.db.count("Communication Hub", {"status": "Pending Review"})
		escalated_count = frappe.db.count("Communication Hub", {"status": "Escalated"})
		hitl_count = frappe.db.count("Communication Hub", {"ai_mode": "HITL", "status": ["in", ["Open", "In Progress"]]})
		takeover_count = frappe.db.count("Communication Hub", {"ai_mode": "Takeover", "status": ["in", ["Open", "In Progress"]]})

		return {
			"pending_review": pending_count,
			"escalated": escalated_count,
			"hitl_mode": hitl_count,
			"takeover_mode": takeover_count,
			"total_requiring_attention": pending_count + escalated_count
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "HITL Stats Error")
		return {}
