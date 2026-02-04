"""
Social Media Webhook Handler

Handles webhooks from social media platforms:
- Facebook Messenger (Meta Graph API)
- Instagram DMs (Meta Graph API)
- Twitter/X DMs (Twitter API v2)
- LinkedIn Messages (LinkedIn API)
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta


@frappe.whitelist(allow_guest=True)
def handle_facebook_webhook():
	"""
	Handle Facebook Messenger webhooks.

	Webhook events:
	- messages (incoming messages)
	- messaging_postbacks (button clicks)
	- message_reads (read receipts)
	"""
	try:
		# Verify webhook (GET request)
		if frappe.request.method == "GET":
			return verify_facebook_webhook()

		# Process webhook (POST request)
		data = frappe.local.form_dict

		# Process each entry
		for entry in data.get("entry", []):
			for messaging_event in entry.get("messaging", []):
				process_facebook_message(messaging_event)

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Facebook Webhook Error")
		return {"status": "error", "message": str(e)}


def verify_facebook_webhook():
	"""Verify Facebook webhook during setup"""
	mode = frappe.form_dict.get("hub.mode")
	token = frappe.form_dict.get("hub.verify_token")
	challenge = frappe.form_dict.get("hub.challenge")

	# Get verify token from settings
	verify_token = frappe.db.get_single_value("AI Communications Hub Settings", "facebook_verify_token")

	if mode == "subscribe" and token == verify_token:
		return challenge
	else:
		frappe.throw(_("Invalid verification token"), frappe.ValidationError)


def process_facebook_message(event):
	"""
	Process incoming Facebook Messenger message.

	Args:
		event (dict): Messaging event from Facebook
	"""
	sender_psid = event.get("sender", {}).get("id")
	recipient_id = event.get("recipient", {}).get("id")

	# Check if message exists
	if "message" in event:
		message_data = event["message"]
		message_text = message_data.get("text", "")
		message_id = message_data.get("mid")

		# Find or create hub
		hub = get_or_create_social_hub(
			platform="Facebook",
			sender_id=sender_psid,
			page_id=recipient_id
		)

		# Check 24-hour window
		if not check_24_hour_window(hub):
			# Outside window - may need message template
			pass

		# Create message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub.name,
			"sender_type": "Customer",
			"sender_name": "Facebook User",
			"sender_identifier": sender_psid,
			"content": message_text,
			"timestamp": datetime.now(),
			"platform_message_id": message_id
		})
		msg.insert()
		frappe.db.commit()

		# Trigger AI response
		if hub.ai_mode == "Autonomous":
			frappe.enqueue(
				"ai_comms_hub.api.ai_engine.generate_response",
				hub_id=hub.name,
				message_id=msg.name,
				queue="default"
			)


@frappe.whitelist(allow_guest=True)
def handle_instagram_webhook():
	"""
	Handle Instagram DM webhooks.

	Similar to Facebook but for Instagram.
	"""
	try:
		if frappe.request.method == "GET":
			return verify_facebook_webhook()  # Same verification

		data = frappe.local.form_dict

		for entry in data.get("entry", []):
			for messaging_event in entry.get("messaging", []):
				process_instagram_message(messaging_event)

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Instagram Webhook Error")
		return {"status": "error", "message": str(e)}


def process_instagram_message(event):
	"""
	Process incoming Instagram DM.

	Args:
		event (dict): Messaging event from Instagram
	"""
	sender_id = event.get("sender", {}).get("id")
	recipient_id = event.get("recipient", {}).get("id")
	message_data = event.get("message", {})
	message_text = message_data.get("text", "")
	message_id = message_data.get("mid")

	# Handle different message types
	if not message_text:
		# Check for attachments (images, stickers, etc.)
		attachments = message_data.get("attachments", [])
		if attachments:
			attachment_types = [a.get("type") for a in attachments]
			message_text = f"[Sent {', '.join(attachment_types)}]"
		else:
			message_text = "[Non-text message]"

	# Find or create hub
	hub = get_or_create_social_hub(
		platform="Instagram",
		sender_id=sender_id,
		page_id=recipient_id
	)

	# Check 24-hour messaging window
	if not check_24_hour_window(hub):
		frappe.logger().warning(f"Instagram 24h window expired for hub {hub.name}")

	# Create message
	msg = frappe.get_doc({
		"doctype": "Communication Message",
		"communication_hub": hub.name,
		"sender_type": "Customer",
		"sender_name": "Instagram User",
		"sender_identifier": sender_id,
		"content": message_text,
		"timestamp": datetime.now(),
		"platform_message_id": message_id
	})
	msg.insert()
	frappe.db.commit()

	# Trigger AI response if in Autonomous mode
	if hub.ai_mode == "Autonomous":
		frappe.enqueue(
			"ai_comms_hub.api.ai_engine.generate_response",
			hub_id=hub.name,
			message_id=msg.name,
			queue="default"
		)


@frappe.whitelist(allow_guest=True)
def handle_twitter_webhook():
	"""
	Handle Twitter/X DM webhooks.

	Note: Twitter requires webhook registration and CRC validation.
	For free tier, use polling instead of webhooks.
	"""
	try:
		# CRC validation (GET request)
		if frappe.request.method == "GET":
			return verify_twitter_crc()

		# Process webhook (POST)
		data = frappe.local.form_dict

		# Process direct message events
		for event in data.get("direct_message_events", []):
			process_twitter_dm(event)

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Twitter Webhook Error")
		return {"status": "error", "message": str(e)}


def verify_twitter_crc():
	"""Verify Twitter CRC challenge"""
	import hmac
	import hashlib
	import base64

	crc_token = frappe.form_dict.get("crc_token")
	consumer_secret = frappe.db.get_single_value("AI Communications Hub Settings", "twitter_consumer_secret")

	# Create HMAC SHA-256 hash
	sha256_hash = hmac.new(
		consumer_secret.encode(),
		msg=crc_token.encode(),
		digestmod=hashlib.sha256
	).digest()

	# Return base64 encoded hash
	response_token = base64.b64encode(sha256_hash).decode()

	return {
		"response_token": f"sha256={response_token}"
	}


def process_twitter_dm(event):
	"""
	Process Twitter direct message event.

	Args:
		event (dict): DM event from Twitter API v2
	"""
	try:
		event_type = event.get("type")

		# Only process MessageCreate events
		if event_type != "MessageCreate":
			return

		message_create = event.get("message_create", {})
		sender_id = message_create.get("sender_id")
		target = message_create.get("target", {})
		recipient_id = target.get("recipient_id")
		message_data = message_create.get("message_data", {})
		message_text = message_data.get("text", "")
		message_id = event.get("id")

		# Skip messages sent by our account
		settings = frappe.get_single("AI Communications Hub Settings")
		our_twitter_id = settings.twitter_user_id
		if sender_id == our_twitter_id:
			return

		# Handle attachments
		if not message_text:
			attachment = message_data.get("attachment", {})
			if attachment:
				att_type = attachment.get("type", "media")
				message_text = f"[Sent {att_type}]"
			else:
				message_text = "[Non-text message]"

		# Find or create hub
		hub = get_or_create_social_hub(
			platform="Twitter",
			sender_id=sender_id
		)

		# Store Twitter-specific data
		if not hub.twitter_dm_id:
			hub.db_set("twitter_dm_id", message_id)

		# Create message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub.name,
			"sender_type": "Customer",
			"sender_name": f"Twitter User @{sender_id[:8]}",
			"sender_identifier": sender_id,
			"content": message_text,
			"timestamp": datetime.now(),
			"platform_message_id": message_id
		})
		msg.insert()
		frappe.db.commit()

		# Trigger AI response
		if hub.ai_mode == "Autonomous":
			frappe.enqueue(
				"ai_comms_hub.api.ai_engine.generate_response",
				hub_id=hub.name,
				message_id=msg.name,
				queue="default"
			)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Twitter DM Processing Error")


def check_24_hour_window(hub):
	"""
	Check if within 24-hour messaging window for Meta platforms.

	Args:
		hub (Document): Communication Hub

	Returns:
		bool: True if within window
	"""
	if hub.channel not in ["Facebook", "Instagram"]:
		return True

	if not hub.created_at:
		return True

	time_since_creation = datetime.now() - hub.created_at
	return time_since_creation < timedelta(hours=24)


def get_or_create_social_hub(platform, sender_id, page_id=None):
	"""
	Find or create Communication Hub for social media conversation.

	Args:
		platform (str): Facebook, Instagram, Twitter, LinkedIn
		sender_id (str): Platform-specific sender ID
		page_id (str, optional): Page ID for Facebook/Instagram

	Returns:
		Document: Communication Hub
	"""
	# Try to find existing hub
	filters = {
		"channel": platform,
		"social_sender_id": sender_id,
		"status": ["in", ["Open", "In Progress"]]
	}

	if page_id:
		filters["social_page_id"] = page_id

	existing = frappe.db.get_value("Communication Hub", filters, "name")

	if existing:
		return frappe.get_doc("Communication Hub", existing)

	# Find or create customer
	customer = get_or_create_customer_by_social(platform, sender_id)

	# Create new hub
	hub = frappe.get_doc({
		"doctype": "Communication Hub",
		"customer": customer.name,
		"channel": platform,
		"status": "Open",
		"ai_mode": "Autonomous",
		"social_platform": platform,
		"social_sender_id": sender_id,
		"social_page_id": page_id,
		"within_24h_window": 1,
		"subject": f"{platform} conversation with {sender_id}"
	})
	hub.insert()
	frappe.db.commit()

	return hub


# LinkedIn webhook handlers
@frappe.whitelist(allow_guest=True)
def handle_linkedin_webhook():
	"""
	Handle LinkedIn message webhooks.

	Note: LinkedIn messaging API requires special approval.
	LinkedIn uses Organization Access for messaging.
	"""
	try:
		# LinkedIn webhook verification (challenge response)
		if frappe.request.method == "GET":
			return verify_linkedin_webhook()

		data = frappe.local.form_dict

		# Process different event types
		event_type = data.get("eventType")

		if event_type == "MESSAGING":
			process_linkedin_message(data)
		elif event_type == "SHARE_MENTION":
			# Handle @mentions - could create leads
			frappe.logger().info(f"LinkedIn mention received")

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "LinkedIn Webhook Error")
		return {"status": "error", "message": str(e)}


def verify_linkedin_webhook():
	"""Verify LinkedIn webhook subscription"""
	challenge = frappe.form_dict.get("challenge")
	if challenge:
		return challenge

	frappe.throw("LinkedIn verification failed")


def process_linkedin_message(data):
	"""
	Process LinkedIn message event.

	Args:
		data (dict): LinkedIn webhook payload
	"""
	try:
		# Extract message details
		# LinkedIn webhook structure varies by API version
		event_data = data.get("eventData", {})
		message_event = event_data.get("messageEvent", {})

		sender_urn = message_event.get("from", "")
		message_body = message_event.get("body", {})
		message_text = message_body.get("text", "")
		message_id = message_event.get("id")

		# Extract sender ID from URN (urn:li:person:ABC123)
		sender_id = sender_urn.split(":")[-1] if sender_urn else "unknown"

		if not message_text:
			# Check for attachments
			attachments = message_body.get("attachments", [])
			if attachments:
				message_text = "[Sent attachment]"
			else:
				message_text = "[Non-text message]"

		# Find or create hub
		hub = get_or_create_social_hub(
			platform="LinkedIn",
			sender_id=sender_id
		)

		# Create message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub.name,
			"sender_type": "Customer",
			"sender_name": f"LinkedIn User",
			"sender_identifier": sender_id,
			"content": message_text,
			"timestamp": datetime.now(),
			"platform_message_id": message_id
		})
		msg.insert()
		frappe.db.commit()

		# Trigger AI response
		if hub.ai_mode == "Autonomous":
			frappe.enqueue(
				"ai_comms_hub.api.ai_engine.generate_response",
				hub_id=hub.name,
				message_id=msg.name,
				queue="default"
			)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "LinkedIn Message Processing Error")


def get_or_create_customer_by_social(platform, sender_id):
	"""
	Find or create customer from social media ID.

	Args:
		platform (str): Social platform name
		sender_id (str): Platform-specific sender ID

	Returns:
		Document: Customer document
	"""
	# Map platform to custom field
	field_map = {
		"Facebook": "facebook_psid",
		"Instagram": "instagram_id",
		"Twitter": "twitter_id",
		"LinkedIn": "linkedin_profile"
	}

	field = field_map.get(platform)

	# Try to find existing customer by social ID
	if field and frappe.db.has_column("Customer", field):
		existing = frappe.get_all(
			"Customer",
			filters={field: sender_id},
			limit=1
		)
		if existing:
			return frappe.get_doc("Customer", existing[0].name)

	# Try to find by partial match or contact info
	# This is a placeholder for more sophisticated matching

	# Create new guest customer
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": f"{platform} User {sender_id[:8]}",
		"customer_type": "Individual",
		"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual",
		"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"
	})

	# Set social ID if field exists
	if field and frappe.db.has_column("Customer", field):
		customer.set(field, sender_id)

	customer.insert(ignore_permissions=True)
	frappe.db.commit()

	return customer
