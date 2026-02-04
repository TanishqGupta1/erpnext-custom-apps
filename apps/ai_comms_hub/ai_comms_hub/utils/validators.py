#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Data validation utilities for AI Communications Hub.
"""

import frappe
from frappe import _
import re
from datetime import datetime


def validate_phone_number(phone):
	"""
	Validate phone number format.

	Args:
		phone (str): Phone number to validate

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	if not phone:
		return (False, _("Phone number is required"))

	# Remove all non-numeric characters
	digits = re.sub(r'\D', '', phone)

	# Check length (US numbers: 10 digits, international: 7-15 digits)
	if len(digits) < 7 or len(digits) > 15:
		return (False, _("Phone number must be between 7 and 15 digits"))

	return (True, "")


def validate_email(email):
	"""
	Validate email address format.

	Args:
		email (str): Email address to validate

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	if not email:
		return (False, _("Email address is required"))

	# RFC 5322 compliant regex (simplified)
	email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

	if not re.match(email_pattern, email):
		return (False, _("Invalid email address format"))

	return (True, "")


def validate_url(url):
	"""
	Validate URL format.

	Args:
		url (str): URL to validate

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	if not url:
		return (False, _("URL is required"))

	url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$'

	if not re.match(url_pattern, url):
		return (False, _("Invalid URL format. Must start with http:// or https://"))

	return (True, "")


def validate_platform(platform):
	"""
	Validate platform name.

	Args:
		platform (str): Platform name

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	valid_platforms = [
		"Voice", "Chat", "WhatsApp", "SMS",
		"Facebook", "Instagram", "Twitter", "LinkedIn", "Email"
	]

	if platform not in valid_platforms:
		return (False, _("Invalid platform. Must be one of: {0}").format(", ".join(valid_platforms)))

	return (True, "")


def validate_sentiment(sentiment):
	"""
	Validate sentiment value.

	Args:
		sentiment (str): Sentiment value

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	valid_sentiments = ["Positive", "Neutral", "Negative"]

	if sentiment not in valid_sentiments:
		return (False, _("Invalid sentiment. Must be one of: {0}").format(", ".join(valid_sentiments)))

	return (True, "")


def validate_ai_mode(mode):
	"""
	Validate AI mode.

	Args:
		mode (str): AI mode

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	valid_modes = ["Autonomous", "Human-in-the-Loop", "Human Takeover"]

	if mode not in valid_modes:
		return (False, _("Invalid AI mode. Must be one of: {0}").format(", ".join(valid_modes)))

	return (True, "")


def validate_status(status):
	"""
	Validate communication status.

	Args:
		status (str): Status value

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	valid_statuses = ["Open", "In Progress", "Resolved", "Escalated", "Closed"]

	if status not in valid_statuses:
		return (False, _("Invalid status. Must be one of: {0}").format(", ".join(valid_statuses)))

	return (True, "")


def validate_api_key(api_key, min_length=20):
	"""
	Validate API key format.

	Args:
		api_key (str): API key to validate
		min_length (int): Minimum key length (default: 20)

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	if not api_key:
		return (False, _("API key is required"))

	if len(api_key) < min_length:
		return (False, _("API key must be at least {0} characters").format(min_length))

	# Check for basic alphanumeric format
	if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
		return (False, _("API key contains invalid characters"))

	return (True, "")


def validate_json_structure(json_data, required_fields):
	"""
	Validate JSON structure contains required fields.

	Args:
		json_data (dict): JSON data to validate
		required_fields (list): List of required field names

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	if not isinstance(json_data, dict):
		return (False, _("Data must be a valid JSON object"))

	missing_fields = [field for field in required_fields if field not in json_data]

	if missing_fields:
		return (False, _("Missing required fields: {0}").format(", ".join(missing_fields)))

	return (True, "")


def validate_message_length(message, platform):
	"""
	Validate message length for platform limits.

	Args:
		message (str): Message content
		platform (str): Platform name

	Returns:
		tuple: (is_valid: bool, error_message: str, truncated_message: str)
	"""
	if not message:
		return (False, _("Message cannot be empty"), "")

	from ai_comms_hub.utils.helpers import get_platform_limits

	limits = get_platform_limits(platform)
	max_chars = limits.get("max_chars")

	if max_chars and len(message) > max_chars:
		truncated = message[:max_chars - 3] + "..."
		return (
			False,
			_("Message exceeds {0} character limit for {1}").format(max_chars, platform),
			truncated
		)

	return (True, "", message)


def validate_llm_settings(settings):
	"""
	Validate LLM API settings.

	Args:
		settings (dict): LLM settings dictionary

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	required_fields = ["api_key", "base_url", "model"]

	is_valid, error = validate_json_structure(settings, required_fields)
	if not is_valid:
		return (is_valid, error)

	# Validate API key
	is_valid, error = validate_api_key(settings["api_key"])
	if not is_valid:
		return (is_valid, error)

	# Validate base URL
	is_valid, error = validate_url(settings["base_url"])
	if not is_valid:
		return (is_valid, error)

	# Validate model name
	if not settings["model"] or len(settings["model"]) < 3:
		return (False, _("Invalid model name"))

	return (True, "")


def validate_qdrant_settings(settings):
	"""
	Validate Qdrant vector database settings.

	Args:
		settings (dict): Qdrant settings dictionary

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	required_fields = ["url", "collection"]

	is_valid, error = validate_json_structure(settings, required_fields)
	if not is_valid:
		return (is_valid, error)

	# Validate URL
	is_valid, error = validate_url(settings["url"])
	if not is_valid:
		return (is_valid, error)

	# Validate collection name
	if not settings["collection"] or not re.match(r'^[a-zA-Z0-9_-]+$', settings["collection"]):
		return (False, _("Invalid collection name. Use only letters, numbers, hyphens, and underscores"))

	return (True, "")


def validate_webhook_payload(payload, platform):
	"""
	Validate webhook payload structure for platform.

	Args:
		payload (dict): Webhook payload
		platform (str): Platform name

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	# Platform-specific required fields
	platform_requirements = {
		"Voice": ["call_id", "event_type"],
		"Facebook": ["sender_id", "message_text"],
		"Instagram": ["sender_id", "message_text"],
		"Twitter": ["sender_id", "message_text"],
		"Email": ["from", "to", "subject", "text"],
		"Chat": ["conversation_id", "message_text"],
		"WhatsApp": ["from", "body"],
		"SMS": ["from", "body"],
		"LinkedIn": ["sender_id", "message_text"]
	}

	required_fields = platform_requirements.get(platform, [])

	return validate_json_structure(payload, required_fields)


def validate_escalation_reason(reason):
	"""
	Validate escalation reason.

	Args:
		reason (str): Escalation reason

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	valid_reasons = [
		"Negative Sentiment",
		"Low Confidence",
		"Human Requested",
		"Refund Request",
		"Technical Issue",
		"VIP Customer",
		"High Value Order",
		"After Hours Urgent",
		"Out of Scope",
		"Other"
	]

	if reason not in valid_reasons:
		return (False, _("Invalid escalation reason"))

	return (True, "")


def validate_function_call(function_name, parameters):
	"""
	Validate AI function call request.

	Args:
		function_name (str): Function to call
		parameters (dict): Function parameters

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	# Get available functions from settings
	available_functions = [
		"get_order_status",
		"create_quote",
		"check_product_availability",
		"get_customer_info",
		"update_customer_info",
		"search_knowledge_base",
		"escalate_to_human"
	]

	if function_name not in available_functions:
		return (False, _("Function '{0}' not found").format(function_name))

	# Function-specific parameter validation
	if function_name == "get_order_status":
		if "order_id" not in parameters:
			return (False, _("order_id parameter required"))

	elif function_name == "create_quote":
		required = ["customer_name", "items"]
		is_valid, error = validate_json_structure(parameters, required)
		if not is_valid:
			return (is_valid, error)

	elif function_name == "check_product_availability":
		if "product_name" not in parameters and "product_code" not in parameters:
			return (False, _("product_name or product_code required"))

	return (True, "")


def validate_date_range(start_date, end_date):
	"""
	Validate date range.

	Args:
		start_date (datetime): Start date
		end_date (datetime): End date

	Returns:
		tuple: (is_valid: bool, error_message: str)
	"""
	if not start_date or not end_date:
		return (False, _("Both start and end dates are required"))

	if start_date > end_date:
		return (False, _("Start date cannot be after end date"))

	# Check if range is too large (e.g., more than 1 year)
	delta = end_date - start_date
	if delta.days > 365:
		return (False, _("Date range cannot exceed 1 year"))

	return (True, "")


def sanitize_input(text, allow_html=False):
	"""
	Sanitize user input to prevent injection attacks.

	Args:
		text (str): Text to sanitize
		allow_html (bool): Whether to allow HTML (default: False)

	Returns:
		str: Sanitized text
	"""
	if not text:
		return ""

	# Remove null bytes
	text = text.replace('\x00', '')

	if not allow_html:
		# Escape HTML special characters
		text = (text
			.replace('&', '&amp;')
			.replace('<', '&lt;')
			.replace('>', '&gt;')
			.replace('"', '&quot;')
			.replace("'", '&#x27;'))
	else:
		from ai_comms_hub.utils.helpers import sanitize_html
		text = sanitize_html(text)

	return text
