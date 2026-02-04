"""
Function Calling Handlers

Implements functions that the AI can call to:
- Get order status
- Create quotes
- Search knowledge base
- Schedule appointments
- Get product information
"""

import frappe
from frappe import _
from datetime import datetime


def get_function_handler(function_name):
	"""
	Get function handler by name.

	Args:
		function_name (str): Function name

	Returns:
		callable: Function handler
	"""
	registry = {
		"getOrderStatus": get_order_status,
		"createQuote": create_quote,
		"searchKnowledge": search_knowledge,
		"scheduleAppointment": schedule_appointment,
		"getProductInfo": get_product_info
	}

	return registry.get(function_name)


def get_order_status(order_number):
	"""
	Get order status from ERPNext.

	Args:
		order_number (str): Sales Order number

	Returns:
		dict: Order details or error
	"""
	try:
		# Check if order exists
		if not frappe.db.exists("Sales Order", order_number):
			return {
				"status": "not_found",
				"message": f"Order {order_number} not found. Please check the order number."
			}

		# Get order details
		order = frappe.get_doc("Sales Order", order_number)

		return {
			"status": "success",
			"order_number": order.name,
			"order_status": order.status,
			"order_date": str(order.transaction_date),
			"total_amount": order.grand_total,
			"delivery_status": order.delivery_status or "Not Delivered",
			"customer": order.customer_name,
			"items": [
				{
					"item": item.item_name,
					"quantity": item.qty,
					"amount": item.amount
				}
				for item in order.items
			]
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Get Order Status Error: {order_number}")
		return {
			"status": "error",
			"message": f"Unable to retrieve order status: {str(e)}"
		}


def create_quote(customer_name, product_name, quantity=1, specifications=""):
	"""
	Create a quotation in ERPNext.

	Args:
		customer_name (str): Customer name
		product_name (str): Product or service name
		quantity (int): Quantity
		specifications (str): Additional requirements

	Returns:
		dict: Created quotation details
	"""
	try:
		# Find customer
		customer = frappe.db.get_value("Customer", {"customer_name": customer_name}, "name")
		if not customer:
			return {
				"status": "error",
				"message": f"Customer '{customer_name}' not found. Would you like me to create a new customer record?"
			}

		# Search for product
		item = frappe.db.get_value(
			"Item",
			{"item_name": ["like", f"%{product_name}%"]},
			["name", "item_name", "standard_rate"]
		)

		if not item:
			return {
				"status": "error",
				"message": f"Product '{product_name}' not found in our catalog. Please provide more details."
			}

		# Create quotation
		quotation = frappe.get_doc({
			"doctype": "Quotation",
			"quotation_to": "Customer",
			"party_name": customer,
			"transaction_date": datetime.today(),
			"valid_till": datetime.today(),
			"items": [{
				"item_code": item[0],
				"item_name": item[1],
				"qty": quantity,
				"rate": item[2] if len(item) > 2 else 0
			}]
		})

		if specifications:
			quotation.add_comment("Comment", f"Customer specifications: {specifications}")

		quotation.insert()
		frappe.db.commit()

		return {
			"status": "success",
			"quotation_number": quotation.name,
			"customer": customer_name,
			"product": item[1],
			"quantity": quantity,
			"estimated_amount": quotation.grand_total,
			"message": f"Quote {quotation.name} created successfully! A team member will review and send the detailed quote."
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create Quote Error")
		return {
			"status": "error",
			"message": f"Unable to create quote: {str(e)}"
		}


def search_knowledge(query):
	"""
	Search knowledge base using Qdrant RAG.

	Args:
		query (str): Search query

	Returns:
		dict: Search results from knowledge base
	"""
	try:
		from ai_comms_hub.api.rag import query_knowledge_base

		results = query_knowledge_base(query, top_k=3)

		if not results:
			return {
				"status": "not_found",
				"message": "I couldn't find specific information about that. Let me connect you with a team member who can help."
			}

		# Format results
		formatted_results = []
		for doc in results:
			formatted_results.append({
				"title": doc.get("title", ""),
				"content": doc.get("content", ""),
				"score": doc.get("score", 0)
			})

		return {
			"status": "success",
			"results": formatted_results,
			"summary": format_knowledge_summary(formatted_results)
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Knowledge Search Error")
		return {
			"status": "error",
			"message": "Unable to search knowledge base at this time."
		}


def format_knowledge_summary(results):
	"""Format knowledge base results into readable summary"""
	if not results:
		return ""

	summary = "Based on our knowledge base:\n\n"

	for result in results[:3]:  # Top 3 results
		if result.get("content"):
			summary += f"• {result['content'][:200]}...\n"

	return summary


def schedule_appointment(customer_name, preferred_date=None, preferred_time=None, purpose=""):
	"""
	Schedule an appointment (creates Event in ERPNext).

	Args:
		customer_name (str): Customer name
		preferred_date (str): Preferred date (YYYY-MM-DD)
		preferred_time (str): Preferred time (HH:MM)
		purpose (str): Purpose of appointment

	Returns:
		dict: Appointment details
	"""
	try:
		# Find customer
		customer = frappe.db.get_value("Customer", {"customer_name": customer_name}, "name")
		if not customer:
			return {
				"status": "error",
				"message": f"Customer '{customer_name}' not found."
			}

		# Parse date and time
		if preferred_date and preferred_time:
			from dateutil import parser
			start_datetime = parser.parse(f"{preferred_date} {preferred_time}")
		elif preferred_date:
			from dateutil import parser
			start_datetime = parser.parse(f"{preferred_date} 10:00")
		else:
			# Default to tomorrow at 10 AM
			from datetime import timedelta
			start_datetime = datetime.now() + timedelta(days=1)
			start_datetime = start_datetime.replace(hour=10, minute=0)

		# Create event
		event = frappe.get_doc({
			"doctype": "Event",
			"subject": f"Appointment: {purpose or 'Consultation'}",
			"starts_on": start_datetime,
			"event_type": "Public",
			"event_category": "Meeting",
			"description": f"Customer: {customer_name}\nPurpose: {purpose}"
		})

		event.insert()
		frappe.db.commit()

		return {
			"status": "success",
			"event_id": event.name,
			"date": str(start_datetime.date()),
			"time": start_datetime.strftime("%H:%M"),
			"message": f"Appointment scheduled for {start_datetime.strftime('%B %d, %Y at %I:%M %p')}. A team member will confirm shortly."
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Schedule Appointment Error")
		return {
			"status": "error",
			"message": f"Unable to schedule appointment: {str(e)}"
		}


def get_product_info(product_name):
	"""
	Get detailed product information.

	Args:
		product_name (str): Product name or SKU

	Returns:
		dict: Product details
	"""
	try:
		# Search for product
		filters = [
			["Item", "item_name", "like", f"%{product_name}%"]
		]

		items = frappe.get_all(
			"Item",
			filters=filters,
			fields=["name", "item_name", "description", "standard_rate", "stock_uom", "item_group"],
			limit=1
		)

		if not items:
			return {
				"status": "not_found",
				"message": f"Product '{product_name}' not found in our catalog."
			}

		item = items[0]

		# Get stock levels
		stock_qty = frappe.db.get_value(
			"Bin",
			{"item_code": item.name},
			"sum(actual_qty)"
		) or 0

		return {
			"status": "success",
			"product_name": item.item_name,
			"description": item.description or "No description available",
			"price": item.standard_rate or 0,
			"unit": item.stock_uom,
			"category": item.item_group,
			"in_stock": stock_qty > 0,
			"stock_qty": stock_qty
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Get Product Info Error: {product_name}")
		return {
			"status": "error",
			"message": f"Unable to retrieve product information: {str(e)}"
		}
