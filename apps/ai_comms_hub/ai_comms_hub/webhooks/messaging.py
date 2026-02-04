"""
Messaging Webhook Handler

Handles inbound webhooks from Twilio for SMS and WhatsApp messages.
"""

import frappe
from frappe import _
import json
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import urlencode


@frappe.whitelist(allow_guest=True)
def handle_twilio_webhook():
	"""
	Handle Twilio webhook for incoming SMS/WhatsApp messages.

	Twilio sends POST with form data:
	- MessageSid: Unique message ID
	- From: Sender phone number
	- To: Your Twilio number
	- Body: Message content
	- NumMedia: Number of media attachments
	- MediaUrl0, MediaContentType0, etc.: Media attachments

	For WhatsApp, 'From' and 'To' are prefixed with 'whatsapp:'
	"""
	try:
		# Verify Twilio signature
		if not verify_twilio_signature():
			frappe.local.response['http_status_code'] = 403
			return {"status": "error", "message": "Invalid signature"}

		# Get form data
		data = frappe.local.form_dict

		# Determine if SMS or WhatsApp
		from_number = data.get("From", "")
		to_number = data.get("To", "")

		if from_number.startswith("whatsapp:"):
			return handle_whatsapp_message(data)
		else:
			return handle_sms_message(data)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Twilio Webhook Error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def handle_sms_webhook():
	"""
	Handle Twilio SMS webhook (direct endpoint for n8n workflows).

	This is an alias for handle_twilio_webhook for SMS-specific routing.
	"""
	return handle_twilio_webhook()


@frappe.whitelist(allow_guest=True)
def handle_whatsapp_webhook():
	"""
	Handle Twilio WhatsApp webhook (direct endpoint for n8n workflows).

	This is an alias for handle_twilio_webhook for WhatsApp-specific routing.
	"""
	return handle_twilio_webhook()


def verify_twilio_signature():
	"""
	Verify Twilio webhook signature for security.

	Twilio signs requests using HMAC-SHA1 with your Auth Token.
	The signature is in the X-Twilio-Signature header.

	Returns:
		bool: True if signature is valid
	"""
	settings = frappe.get_single("AI Communications Hub Settings")

	# Skip verification if auth token not configured
	if not settings.twilio_auth_token:
		frappe.logger().warning("Twilio Auth Token not configured - skipping signature verification")
		return True

	# Get signature from header
	signature = frappe.request.headers.get("X-Twilio-Signature", "")
	if not signature:
		frappe.logger().warning("No X-Twilio-Signature header found")
		return False

	# Build validation URL
	# Twilio signs the full URL including query params
	url = frappe.request.url

	# Get POST parameters sorted by key
	params = dict(frappe.local.form_dict)

	# Build string to sign: URL + sorted POST params
	s = url
	for key in sorted(params.keys()):
		s += key + str(params[key])

	# Compute expected signature
	auth_token = settings.twilio_auth_token
	expected_signature = base64.b64encode(
		hmac.new(
			auth_token.encode('utf-8'),
			s.encode('utf-8'),
			hashlib.sha1
		).digest()
	).decode('utf-8')

	# Compare signatures
	return hmac.compare_digest(signature, expected_signature)


def handle_sms_message(data):
	"""
	Process incoming SMS message from Twilio.

	Args:
		data (dict): Twilio webhook payload

	Returns:
		dict: Response status
	"""
	# Extract message details
	message_sid = data.get("MessageSid")
	from_number = data.get("From", "")
	to_number = data.get("To", "")
	body = data.get("Body", "")
	num_media = int(data.get("NumMedia", 0))

	# Clean phone numbers (remove + prefix for consistency)
	from_number = from_number.strip()
	to_number = to_number.strip()

	# Check for duplicate message
	if message_already_processed(message_sid):
		return {"status": "duplicate", "message_sid": message_sid}

	# Find or create hub
	hub = get_or_create_sms_hub(from_number, to_number)

	# Build message content
	message_content = body

	# Handle media attachments
	attachments = []
	if num_media > 0:
		for i in range(num_media):
			media_url = data.get(f"MediaUrl{i}")
			media_type = data.get(f"MediaContentType{i}", "")

			if media_url:
				attachments.append({
					"url": media_url,
					"content_type": media_type
				})

		# Append media indicator to message if body is empty
		if not body and attachments:
			media_types = [a.get("content_type", "media").split("/")[0] for a in attachments]
			message_content = f"[Sent {', '.join(media_types)}]"

	# Create message
	msg = frappe.get_doc({
		"doctype": "Communication Message",
		"communication_hub": hub.name,
		"sender_type": "Customer",
		"sender_name": f"SMS User {from_number[-4:]}",
		"sender_identifier": from_number,
		"content": message_content,
		"timestamp": datetime.now(),
		"platform_message_id": message_sid,
		"delivery_status": "Received"
	})

	# Store attachments if any
	if attachments:
		msg.attachments_json = json.dumps(attachments)

	msg.insert()
	frappe.db.commit()

	# Log successful receipt
	frappe.logger().info(f"SMS received from {from_number}: {message_sid}")

	# Trigger AI response if in Autonomous mode
	if hub.ai_mode == "Autonomous":
		frappe.enqueue(
			"ai_comms_hub.api.ai_engine.generate_response",
			hub_id=hub.name,
			message_id=msg.name,
			queue="default",
			enqueue_after_commit=True
		)

	# Return TwiML empty response (no auto-reply, we handle it async)
	frappe.local.response['http_status_code'] = 200
	frappe.local.response['content_type'] = 'text/xml'
	return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


def handle_whatsapp_message(data):
	"""
	Process incoming WhatsApp message from Twilio.

	Args:
		data (dict): Twilio webhook payload

	Returns:
		dict: Response status
	"""
	# Extract message details
	message_sid = data.get("MessageSid")
	from_number = data.get("From", "").replace("whatsapp:", "")
	to_number = data.get("To", "").replace("whatsapp:", "")
	body = data.get("Body", "")
	num_media = int(data.get("NumMedia", 0))

	# WhatsApp-specific fields
	profile_name = data.get("ProfileName", "")  # WhatsApp profile name
	wa_id = data.get("WaId", "")  # WhatsApp ID (phone without +)

	# Check for duplicate message
	if message_already_processed(message_sid):
		return {"status": "duplicate", "message_sid": message_sid}

	# Find or create hub
	hub = get_or_create_whatsapp_hub(from_number, to_number, profile_name)

	# Build message content
	message_content = body

	# Handle media attachments
	attachments = []
	if num_media > 0:
		for i in range(num_media):
			media_url = data.get(f"MediaUrl{i}")
			media_type = data.get(f"MediaContentType{i}", "")

			if media_url:
				attachments.append({
					"url": media_url,
					"content_type": media_type
				})

		# Append media indicator to message if body is empty
		if not body and attachments:
			media_types = [a.get("content_type", "media").split("/")[0] for a in attachments]
			message_content = f"[Sent {', '.join(media_types)}]"

	# Detect special message types
	button_text = data.get("ButtonText", "")  # Quick reply button
	button_payload = data.get("ButtonPayload", "")

	if button_text:
		message_content = f"[Button: {button_text}]"
		if button_payload:
			message_content += f" (Payload: {button_payload})"

	# Handle location sharing
	latitude = data.get("Latitude")
	longitude = data.get("Longitude")
	if latitude and longitude:
		message_content = f"[Location: {latitude}, {longitude}]"

	# Create message
	sender_name = profile_name if profile_name else f"WhatsApp User {from_number[-4:]}"
	msg = frappe.get_doc({
		"doctype": "Communication Message",
		"communication_hub": hub.name,
		"sender_type": "Customer",
		"sender_name": sender_name,
		"sender_identifier": from_number,
		"content": message_content,
		"timestamp": datetime.now(),
		"platform_message_id": message_sid,
		"delivery_status": "Received"
	})

	# Store attachments if any
	if attachments:
		msg.attachments_json = json.dumps(attachments)

	msg.insert()
	frappe.db.commit()

	# Log successful receipt
	frappe.logger().info(f"WhatsApp received from {from_number}: {message_sid}")

	# Update 24-hour window
	hub.db_set("within_24h_window", 1)
	hub.db_set("last_customer_message", datetime.now())

	# Trigger AI response if in Autonomous mode
	if hub.ai_mode == "Autonomous":
		frappe.enqueue(
			"ai_comms_hub.api.ai_engine.generate_response",
			hub_id=hub.name,
			message_id=msg.name,
			queue="default",
			enqueue_after_commit=True
		)

	# Return TwiML empty response
	frappe.local.response['http_status_code'] = 200
	frappe.local.response['content_type'] = 'text/xml'
	return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


def message_already_processed(message_sid):
	"""
	Check if message has already been processed (idempotency check).

	Args:
		message_sid (str): Twilio message SID

	Returns:
		bool: True if already processed
	"""
	if not message_sid:
		return False

	return frappe.db.exists(
		"Communication Message",
		{"platform_message_id": message_sid}
	)


def get_or_create_sms_hub(from_number, to_number):
	"""
	Find or create Communication Hub for SMS conversation.

	Args:
		from_number (str): Sender phone number
		to_number (str): Recipient phone number (our Twilio number)

	Returns:
		Document: Communication Hub
	"""
	# Try to find existing open conversation
	existing = frappe.db.get_value(
		"Communication Hub",
		{
			"channel": "SMS",
			"sms_phone_number": from_number,
			"status": ["in", ["Open", "In Progress"]]
		},
		"name"
	)

	if existing:
		return frappe.get_doc("Communication Hub", existing)

	# Find or create customer
	customer = get_or_create_customer_by_phone(from_number)

	# Create new hub
	hub = frappe.get_doc({
		"doctype": "Communication Hub",
		"customer": customer.name,
		"channel": "SMS",
		"status": "Open",
		"ai_mode": "Autonomous",
		"sms_phone_number": from_number,
		"subject": f"SMS conversation with {from_number}"
	})
	hub.insert()
	frappe.db.commit()

	frappe.logger().info(f"Created new SMS hub: {hub.name} for {from_number}")

	return hub


def get_or_create_whatsapp_hub(from_number, to_number, profile_name=None):
	"""
	Find or create Communication Hub for WhatsApp conversation.

	Args:
		from_number (str): Sender phone number
		to_number (str): Recipient phone number (our Twilio number)
		profile_name (str, optional): WhatsApp profile name

	Returns:
		Document: Communication Hub
	"""
	# Try to find existing open conversation
	existing = frappe.db.get_value(
		"Communication Hub",
		{
			"channel": "WhatsApp",
			"chatwoot_phone_number": from_number,
			"status": ["in", ["Open", "In Progress"]]
		},
		"name"
	)

	if existing:
		hub = frappe.get_doc("Communication Hub", existing)
		# Update profile name if we now have it
		if profile_name and not hub.customer_name:
			hub.db_set("customer_name", profile_name)
		return hub

	# Find or create customer
	customer = get_or_create_customer_by_phone(from_number, profile_name)

	# Create new hub
	display_name = profile_name if profile_name else from_number
	hub = frappe.get_doc({
		"doctype": "Communication Hub",
		"customer": customer.name,
		"customer_name": profile_name,
		"channel": "WhatsApp",
		"status": "Open",
		"ai_mode": "Autonomous",
		"chatwoot_phone_number": from_number,
		"within_24h_window": 1,
		"last_customer_message": datetime.now(),
		"subject": f"WhatsApp conversation with {display_name}"
	})
	hub.insert()
	frappe.db.commit()

	frappe.logger().info(f"Created new WhatsApp hub: {hub.name} for {from_number}")

	return hub


def get_or_create_customer_by_phone(phone_number, name=None):
	"""
	Find or create customer from phone number.

	Args:
		phone_number (str): Phone number
		name (str, optional): Customer name

	Returns:
		Document: Customer
	"""
	# Clean phone number
	clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")

	# Try to find existing customer by mobile
	customer_name = frappe.db.get_value(
		"Customer",
		{"mobile_no": ["like", f"%{clean_phone[-10:]}%"]},
		"name"
	)

	if customer_name:
		return frappe.get_doc("Customer", customer_name)

	# Try alternate phone field
	customer_name = frappe.db.get_value(
		"Customer",
		{"phone": ["like", f"%{clean_phone[-10:]}%"]},
		"name"
	)

	if customer_name:
		return frappe.get_doc("Customer", customer_name)

	# Create new customer
	display_name = name if name else f"Phone User {phone_number[-4:]}"
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": display_name,
		"customer_type": "Individual",
		"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual",
		"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories",
		"mobile_no": phone_number
	})
	customer.insert(ignore_permissions=True)
	frappe.db.commit()

	frappe.logger().info(f"Created new customer: {customer.name} for phone {phone_number}")

	return customer


@frappe.whitelist(allow_guest=True)
def handle_twilio_status_callback():
	"""
	Handle Twilio message status callbacks.

	Twilio sends status updates for outbound messages:
	- queued, sending, sent, delivered, undelivered, failed

	Used to track delivery status of our outbound SMS/WhatsApp messages.
	"""
	try:
		data = frappe.local.form_dict

		message_sid = data.get("MessageSid")
		message_status = data.get("MessageStatus")
		error_code = data.get("ErrorCode")
		error_message = data.get("ErrorMessage")

		if not message_sid:
			return {"status": "error", "message": "Missing MessageSid"}

		# Find the message by platform_message_id
		message_name = frappe.db.get_value(
			"Communication Message",
			{"platform_message_id": message_sid},
			"name"
		)

		if not message_name:
			# Message might be outbound (we sent it) - find by external_message_id
			message_name = frappe.db.get_value(
				"Communication Message",
				{"external_message_id": message_sid},
				"name"
			)

		if message_name:
			# Map Twilio status to our status
			status_map = {
				"queued": "Pending",
				"sending": "Pending",
				"sent": "Sent",
				"delivered": "Delivered",
				"read": "Read",
				"undelivered": "Failed",
				"failed": "Failed"
			}

			new_status = status_map.get(message_status, "Pending")

			# Update message status
			frappe.db.set_value(
				"Communication Message",
				message_name,
				{
					"delivery_status": new_status,
					"delivery_error": error_message if error_code else None
				}
			)
			frappe.db.commit()

			frappe.logger().info(f"Updated message {message_sid} status to {new_status}")

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Twilio Status Callback Error")
		return {"status": "error", "message": str(e)}
