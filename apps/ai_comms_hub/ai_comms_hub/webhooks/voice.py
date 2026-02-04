"""
Eleven Labs Voice AI Webhook Handler

Handles webhooks from Eleven Labs Conversational AI for voice calls.
"""

import frappe
from frappe import _
import json
import hmac
import hashlib
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def handle_elevenlabs_webhook():
	"""
	Handle incoming Eleven Labs webhooks.

	Eleven Labs sends webhooks for:
	- post_call_transcription: Full conversation data with transcripts and analysis
	- post_call_audio: Base64-encoded audio of the conversation
	- call_initiation_failure: Failed call attempts with reason
	"""
	try:
		# Get webhook data
		if frappe.request.data:
			data = json.loads(frappe.request.get_data(as_text=True))
		else:
			data = frappe.local.form_dict

		# Verify webhook signature (if configured)
		if not verify_elevenlabs_signature():
			frappe.throw(_("Invalid webhook signature"), frappe.AuthenticationError)

		# Get event type
		event_type = data.get("type")
		event_timestamp = data.get("event_timestamp")

		frappe.logger().info(f"Eleven Labs webhook received: {event_type}")

		# Route to appropriate handler
		if event_type == "post_call_transcription":
			return handle_post_call_transcription(data)
		elif event_type == "post_call_audio":
			return handle_post_call_audio(data)
		elif event_type == "call_initiation_failure":
			return handle_call_initiation_failure(data)
		else:
			frappe.log_error(f"Unknown Eleven Labs event type: {event_type}", "Eleven Labs Webhook")
			return {"status": "ignored", "event": event_type}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Eleven Labs Webhook Error")
		return {"status": "error", "message": str(e)}


def verify_elevenlabs_signature():
	"""
	Verify Eleven Labs webhook signature using HMAC-SHA256.

	Eleven Labs signs webhooks using the format: timestamp.request_body
	The signature is in the ElevenLabs-Signature header.

	Returns:
		bool: True if signature is valid or verification is disabled
	"""
	# Get settings
	settings = frappe.get_single("AI Communications Hub Settings")
	webhook_secret = settings.get("elevenlabs_webhook_secret")

	# If no secret configured, skip verification (development mode)
	if not webhook_secret:
		frappe.logger().warning("Eleven Labs webhook signature verification disabled - no secret configured")
		return True

	# Get signature from headers
	signature_header = frappe.get_request_header("ElevenLabs-Signature")

	if not signature_header:
		frappe.log_error("Eleven Labs webhook missing signature header", "Eleven Labs Auth")
		return False

	try:
		# Parse signature header (format: t=timestamp,v1=signature)
		parts = {}
		for part in signature_header.split(","):
			key, value = part.split("=", 1)
			parts[key] = value

		timestamp = parts.get("t")
		signature = parts.get("v1")

		if not timestamp or not signature:
			frappe.log_error("Invalid Eleven Labs signature header format", "Eleven Labs Auth")
			return False

		# Get raw request body
		raw_body = frappe.request.get_data(as_text=True)

		# Compute expected signature
		# Eleven Labs uses: HMAC-SHA256(timestamp.request_body)
		signed_payload = f"{timestamp}.{raw_body}"
		expected_signature = hmac.new(
			webhook_secret.encode('utf-8'),
			signed_payload.encode('utf-8'),
			hashlib.sha256
		).hexdigest()

		# Compare signatures (timing-safe comparison)
		is_valid = hmac.compare_digest(signature, expected_signature)

		if not is_valid:
			frappe.log_error(
				f"Eleven Labs signature mismatch. Expected: {expected_signature[:20]}..., Got: {signature[:20]}...",
				"Eleven Labs Auth"
			)

		return is_valid

	except Exception as e:
		frappe.log_error(f"Eleven Labs signature verification error: {str(e)}", "Eleven Labs Auth")
		return False


def handle_post_call_transcription(data):
	"""
	Handle post-call transcription webhook.

	Contains full conversation data including:
	- transcript: Array of conversation turns
	- analysis: Evaluation results, success status, summary
	- metadata: Call timing, costs, phone details
	"""
	try:
		call_data = data.get("data", {})

		agent_id = call_data.get("agent_id")
		conversation_id = call_data.get("conversation_id")
		status = call_data.get("status")

		# Get transcript
		transcript = call_data.get("transcript", [])

		# Get metadata
		metadata = call_data.get("metadata", {})
		call_duration = metadata.get("call_duration_secs")
		start_time = metadata.get("start_time_unix_secs")
		end_time = metadata.get("end_time_unix_secs")

		# Phone details from metadata
		phone_number = None
		if "phone_call" in metadata:
			phone_call = metadata["phone_call"]
			phone_number = phone_call.get("from_number") or phone_call.get("to_number")

		# Get analysis
		analysis = call_data.get("analysis", {})
		summary = analysis.get("summary", "")
		success_evaluation = analysis.get("success_evaluation")
		data_collection = analysis.get("data_collection_results", {})

		# Check if hub already exists for this conversation
		existing_hub = frappe.get_value(
			"Communication Hub",
			{"elevenlabs_conversation_id": conversation_id},
			"name"
		)

		if existing_hub:
			# Update existing hub
			hub = frappe.get_doc("Communication Hub", existing_hub)
		else:
			# Find or create customer
			customer = None
			if phone_number:
				customer = get_or_create_customer_by_phone(phone_number)

			# Create new Communication Hub
			hub = frappe.get_doc({
				"doctype": "Communication Hub",
				"customer": customer.name if customer else None,
				"channel": "Voice",
				"status": "Open",
				"ai_mode": "Autonomous",
				"elevenlabs_agent_id": agent_id,
				"elevenlabs_conversation_id": conversation_id,
				"elevenlabs_phone_number": phone_number,
				"subject": f"Voice Call - {phone_number or conversation_id[:8]}"
			})
			hub.insert()

		# Update hub with call details
		hub.call_duration = call_duration
		hub.call_status = "Completed" if status == "done" else status
		hub.call_summary = summary
		hub.call_success = 1 if success_evaluation == "success" else 0
		hub.status = "Resolved" if status == "done" else "In Progress"

		# Store full transcript as JSON
		hub.call_transcript = json.dumps(transcript, indent=2)

		# Store data collection results if any
		if data_collection:
			hub.call_data_collected = json.dumps(data_collection, indent=2)

		hub.save()

		# Create individual message records from transcript
		for turn in transcript:
			role = turn.get("role")
			message = turn.get("message", "")

			if not message:
				continue

			sender_type = "Customer" if role == "user" else "AI"
			sender_name = "Customer" if role == "user" else "Eleven Labs AI"

			# Check if message already exists (avoid duplicates)
			existing_msg = frappe.db.exists(
				"Communication Message",
				{
					"communication_hub": hub.name,
					"content": message[:140],  # First 140 chars for matching
					"sender_type": sender_type
				}
			)

			if not existing_msg:
				msg = frappe.get_doc({
					"doctype": "Communication Message",
					"communication_hub": hub.name,
					"sender_type": sender_type,
					"sender_name": sender_name,
					"content": message,
					"timestamp": datetime.now()
				})
				msg.insert()

		frappe.db.commit()

		return {
			"status": "success",
			"hub_id": hub.name,
			"conversation_id": conversation_id
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Eleven Labs Transcription Error")
		return {"status": "error", "message": str(e)}


def handle_post_call_audio(data):
	"""
	Handle post-call audio webhook.

	Contains base64-encoded MP3 audio of the full conversation.
	"""
	try:
		call_data = data.get("data", {})

		agent_id = call_data.get("agent_id")
		conversation_id = call_data.get("conversation_id")
		full_audio = call_data.get("full_audio")  # Base64 encoded MP3

		# Find Communication Hub by conversation ID
		hub_name = frappe.get_value(
			"Communication Hub",
			{"elevenlabs_conversation_id": conversation_id},
			"name"
		)

		if not hub_name:
			frappe.logger().warning(f"No hub found for conversation {conversation_id}, creating placeholder")
			# Create placeholder hub for audio
			hub = frappe.get_doc({
				"doctype": "Communication Hub",
				"channel": "Voice",
				"status": "Open",
				"ai_mode": "Autonomous",
				"elevenlabs_agent_id": agent_id,
				"elevenlabs_conversation_id": conversation_id,
				"subject": f"Voice Call - {conversation_id[:8]}"
			})
			hub.insert()
			hub_name = hub.name

		# Save audio as file attachment
		if full_audio:
			import base64

			audio_content = base64.b64decode(full_audio)

			# Create file record
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": f"call_recording_{conversation_id}.mp3",
				"attached_to_doctype": "Communication Hub",
				"attached_to_name": hub_name,
				"content": audio_content,
				"is_private": 1
			})
			file_doc.save()

			# Update hub with recording URL
			frappe.db.set_value(
				"Communication Hub",
				hub_name,
				"call_recording_url",
				file_doc.file_url
			)

			frappe.db.commit()

		return {
			"status": "success",
			"hub_id": hub_name,
			"conversation_id": conversation_id,
			"audio_saved": bool(full_audio)
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Eleven Labs Audio Error")
		return {"status": "error", "message": str(e)}


def handle_call_initiation_failure(data):
	"""
	Handle call initiation failure webhook.

	Contains failure reason and metadata about the failed call attempt.
	Failure reasons: "busy", "no-answer", "unknown"
	"""
	try:
		call_data = data.get("data", {})

		agent_id = call_data.get("agent_id")
		conversation_id = call_data.get("conversation_id")
		failure_reason = call_data.get("failure_reason")  # busy, no-answer, unknown
		metadata = call_data.get("metadata", {})

		# Extract phone number from metadata
		phone_number = None
		metadata_type = metadata.get("type")
		metadata_body = metadata.get("body", {})

		if metadata_type == "twilio":
			phone_number = metadata_body.get("From") or metadata_body.get("To")
		elif metadata_type == "sip":
			phone_number = metadata_body.get("from_number") or metadata_body.get("to_number")

		# Find or create customer
		customer = None
		if phone_number:
			customer = get_or_create_customer_by_phone(phone_number)

		# Create Communication Hub for failed call
		hub = frappe.get_doc({
			"doctype": "Communication Hub",
			"customer": customer.name if customer else None,
			"channel": "Voice",
			"status": "Closed",
			"ai_mode": "Autonomous",
			"elevenlabs_agent_id": agent_id,
			"elevenlabs_conversation_id": conversation_id,
			"elevenlabs_phone_number": phone_number,
			"call_status": "Failed",
			"call_failure_reason": failure_reason,
			"subject": f"Failed Call - {failure_reason} - {phone_number or 'Unknown'}"
		})
		hub.insert()

		# Create system message about failure
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub.name,
			"sender_type": "System",
			"sender_name": "System",
			"content": f"Call initiation failed. Reason: {failure_reason}",
			"timestamp": datetime.now()
		})
		msg.insert()

		frappe.db.commit()

		return {
			"status": "success",
			"hub_id": hub.name,
			"conversation_id": conversation_id,
			"failure_reason": failure_reason
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Eleven Labs Call Failure Error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def handle_elevenlabs_tool_call():
	"""
	Handle server tool calls from Eleven Labs agent.

	Eleven Labs agents can call server tools (webhooks) during conversation
	to interact with external APIs like ERPNext.
	"""
	try:
		# Get request data
		if frappe.request.data:
			data = json.loads(frappe.request.get_data(as_text=True))
		else:
			data = frappe.local.form_dict

		# Verify signature
		if not verify_elevenlabs_signature():
			frappe.throw(_("Invalid webhook signature"), frappe.AuthenticationError)

		# Get tool call details
		tool_name = data.get("tool_name") or data.get("name")
		parameters = data.get("parameters", {})
		conversation_id = data.get("conversation_id")

		frappe.logger().info(f"Eleven Labs tool call: {tool_name}")

		# Find Communication Hub for this conversation
		hub_name = frappe.get_value(
			"Communication Hub",
			{"elevenlabs_conversation_id": conversation_id},
			"name"
		)

		# Log function call as message
		if hub_name:
			msg = frappe.get_doc({
				"doctype": "Communication Message",
				"communication_hub": hub_name,
				"sender_type": "AI",
				"sender_name": "Eleven Labs AI",
				"content": f"Function call: {tool_name}",
				"timestamp": datetime.now(),
				"is_function_call": 1,
				"function_name": tool_name,
				"function_args": json.dumps(parameters)
			})
			msg.insert()

		# Execute the function
		result = execute_function(tool_name, parameters)

		# Update message with result
		if hub_name:
			msg.function_result = json.dumps(result)
			msg.function_success = 1 if not result.get("error") else 0
			if result.get("error"):
				msg.function_error = result["error"]
			msg.save()

		frappe.db.commit()

		# Return result to Eleven Labs
		return result

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Eleven Labs Tool Call Error")
		return {"error": str(e)}


def execute_function(function_name, parameters):
	"""
	Execute a function requested by Eleven Labs AI.

	Args:
		function_name (str): Name of function to execute
		parameters (dict): Function parameters

	Returns:
		dict: Function result
	"""
	try:
		# Import function handlers
		from ai_comms_hub.api.functions import (
			get_order_status,
			create_quote,
			search_knowledge,
			schedule_appointment,
			get_product_info
		)

		# Function registry
		functions = {
			"getOrderStatus": get_order_status,
			"get_order_status": get_order_status,
			"createQuote": create_quote,
			"create_quote": create_quote,
			"searchKnowledge": search_knowledge,
			"search_knowledge": search_knowledge,
			"scheduleAppointment": schedule_appointment,
			"schedule_appointment": schedule_appointment,
			"getProductInfo": get_product_info,
			"get_product_info": get_product_info
		}

		if function_name not in functions:
			return {"error": f"Unknown function: {function_name}"}

		# Execute function
		handler = functions[function_name]
		result = handler(**parameters)

		return result

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Function Execution Error: {function_name}")
		return {"error": str(e)}


def get_or_create_customer_by_phone(phone_number):
	"""
	Find or create customer by phone number.

	Args:
		phone_number (str): Customer phone number

	Returns:
		Document: Customer document
	"""
	# Clean phone number
	clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")

	# Try to find existing customer
	customer_name = frappe.db.get_value(
		"Customer",
		{"mobile_no": ["like", f"%{clean_phone[-10:]}%"]},
		"name"
	)

	if customer_name:
		return frappe.get_doc("Customer", customer_name)

	# Create new customer
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": f"Phone Customer {phone_number}",
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "All Territories",
		"mobile_no": phone_number
	})
	customer.insert(ignore_permissions=True)
	frappe.db.commit()

	return customer


# Legacy VAPI endpoint (deprecated - kept for backwards compatibility)
@frappe.whitelist(allow_guest=True)
def handle_vapi_webhook():
	"""
	DEPRECATED: Use handle_elevenlabs_webhook instead.

	This endpoint is kept for backwards compatibility but will be removed in future versions.
	"""
	frappe.logger().warning("VAPI webhook endpoint is deprecated. Please migrate to Eleven Labs.")
	return {
		"status": "error",
		"message": "VAPI integration has been replaced with Eleven Labs. Please update your webhook URL to use handle_elevenlabs_webhook."
	}
