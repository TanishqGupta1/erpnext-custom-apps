#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Common helper functions for AI Communications Hub.
"""

import frappe
from frappe import _
import re
from datetime import datetime, timedelta
import hashlib
import json


def format_phone_number(phone, country_code="US"):
	"""
	Format phone number to E.164 format.

	Args:
		phone (str): Raw phone number
		country_code (str): ISO country code (default: US)

	Returns:
		str: Formatted phone number with + prefix
	"""
	# Remove all non-numeric characters
	digits = re.sub(r'\D', '', phone)

	# Add country code if missing
	if not digits.startswith('1') and country_code == "US":
		digits = '1' + digits

	return f'+{digits}'


def truncate_text(text, max_length, suffix="..."):
	"""
	Truncate text to maximum length with ellipsis.

	Args:
		text (str): Text to truncate
		max_length (int): Maximum length
		suffix (str): Suffix to add (default: "...")

	Returns:
		str: Truncated text
	"""
	if not text or len(text) <= max_length:
		return text

	return text[:max_length - len(suffix)] + suffix


def extract_email_from_string(text):
	"""
	Extract email address from string using regex.

	Args:
		text (str): String containing email

	Returns:
		str: Extracted email or None
	"""
	if not text:
		return None

	email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
	match = re.search(email_pattern, text)

	return match.group(0) if match else None


def extract_url_from_string(text):
	"""
	Extract URL from string using regex.

	Args:
		text (str): String containing URL

	Returns:
		list: List of extracted URLs
	"""
	if not text:
		return []

	url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
	urls = re.findall(url_pattern, text)

	return urls


def get_relative_time(dt):
	"""
	Get human-readable relative time (e.g., "2 hours ago").

	Args:
		dt (datetime): Datetime object

	Returns:
		str: Relative time string
	"""
	if not dt:
		return ""

	now = datetime.now()
	diff = now - dt

	if diff.days > 365:
		years = diff.days // 365
		return f"{years} year{'s' if years > 1 else ''} ago"
	elif diff.days > 30:
		months = diff.days // 30
		return f"{months} month{'s' if months > 1 else ''} ago"
	elif diff.days > 0:
		return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
	elif diff.seconds > 3600:
		hours = diff.seconds // 3600
		return f"{hours} hour{'s' if hours > 1 else ''} ago"
	elif diff.seconds > 60:
		minutes = diff.seconds // 60
		return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
	else:
		return "just now"


def format_duration(seconds):
	"""
	Format duration in seconds to human-readable format.

	Args:
		seconds (int): Duration in seconds

	Returns:
		str: Formatted duration (e.g., "1h 23m 45s")
	"""
	if not seconds:
		return "0s"

	hours = seconds // 3600
	minutes = (seconds % 3600) // 60
	secs = seconds % 60

	parts = []
	if hours > 0:
		parts.append(f"{hours}h")
	if minutes > 0:
		parts.append(f"{minutes}m")
	if secs > 0 or not parts:
		parts.append(f"{secs}s")

	return " ".join(parts)


def generate_conversation_hash(*args):
	"""
	Generate unique hash for conversation tracking.

	Args:
		*args: Variable arguments to hash (e.g., platform, sender_id, channel)

	Returns:
		str: MD5 hash string
	"""
	combined = "|".join(str(arg) for arg in args)
	return hashlib.md5(combined.encode()).hexdigest()


def sanitize_html(html_content):
	"""
	Sanitize HTML content for safe display.

	Args:
		html_content (str): Raw HTML

	Returns:
		str: Sanitized HTML
	"""
	if not html_content:
		return ""

	# Remove script tags
	html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

	# Remove on* event handlers
	html_content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)

	# Remove javascript: URLs
	html_content = re.sub(r'javascript:', '', html_content, flags=re.IGNORECASE)

	return html_content


def chunk_text(text, chunk_size=1000, overlap=200):
	"""
	Chunk text into smaller pieces for RAG ingestion.

	Args:
		text (str): Text to chunk
		chunk_size (int): Maximum chunk size (default: 1000)
		overlap (int): Overlap between chunks (default: 200)

	Returns:
		list: List of text chunks
	"""
	if not text or len(text) <= chunk_size:
		return [text] if text else []

	chunks = []
	start = 0

	while start < len(text):
		end = start + chunk_size

		# Try to break at sentence boundary
		if end < len(text):
			# Look for sentence ending punctuation
			sentence_end = max(
				text.rfind('.', start, end),
				text.rfind('!', start, end),
				text.rfind('?', start, end)
			)

			if sentence_end > start:
				end = sentence_end + 1

		chunks.append(text[start:end].strip())
		start = end - overlap if end < len(text) else end

	return chunks


def estimate_token_count(text):
	"""
	Estimate token count for LLM context (rough approximation).

	Args:
		text (str): Text to estimate

	Returns:
		int: Estimated token count
	"""
	if not text:
		return 0

	# Rough estimation: ~4 characters per token
	return len(text) // 4


def get_platform_limits(platform):
	"""
	Get message length limits for each platform.

	Args:
		platform (str): Platform name

	Returns:
		dict: Character limits and constraints
	"""
	limits = {
		"Voice": {
			"max_chars": None,  # No hard limit for voice
			"recommended_words": 50,
			"tone": "conversational"
		},
		"Chat": {
			"max_chars": 2000,  # Chatwoot limit
			"recommended_chars": 500,
			"tone": "friendly"
		},
		"WhatsApp": {
			"max_chars": 4096,  # Twilio limit
			"recommended_chars": 1000,
			"tone": "casual"
		},
		"SMS": {
			"max_chars": 1600,  # Twilio concatenated SMS limit
			"recommended_chars": 160,  # Single SMS
			"tone": "concise"
		},
		"Facebook": {
			"max_chars": 2000,  # Meta limit
			"recommended_chars": 500,
			"tone": "friendly"
		},
		"Instagram": {
			"max_chars": 1000,  # Meta limit
			"recommended_chars": 300,
			"tone": "casual"
		},
		"Twitter": {
			"max_chars": 280,  # Twitter DM limit (same as tweet)
			"recommended_chars": 240,
			"tone": "concise"
		},
		"LinkedIn": {
			"max_chars": 1300,  # LinkedIn limit
			"recommended_chars": 500,
			"tone": "professional"
		},
		"Email": {
			"max_chars": None,  # No hard limit
			"recommended_chars": 2000,
			"tone": "professional"
		}
	}

	return limits.get(platform, {
		"max_chars": 2000,
		"recommended_chars": 500,
		"tone": "neutral"
	})


def mask_sensitive_data(text):
	"""
	Mask sensitive data like credit cards, SSN, etc.

	Args:
		text (str): Text containing sensitive data

	Returns:
		str: Text with masked data
	"""
	if not text:
		return text

	# Mask credit card numbers (16 digits with optional spaces/hyphens)
	text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '****-****-****-****', text)

	# Mask SSN (XXX-XX-XXXX)
	text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****', text)

	# Mask email addresses (partially)
	text = re.sub(r'\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b',
	              lambda m: f"{m.group(1)[:2]}***@{m.group(2)}", text)

	return text


def parse_json_safe(json_string, default=None):
	"""
	Safely parse JSON string with fallback.

	Args:
		json_string (str): JSON string to parse
		default: Default value if parsing fails

	Returns:
		Parsed JSON or default value
	"""
	if not json_string:
		return default or {}

	try:
		return json.loads(json_string)
	except (json.JSONDecodeError, TypeError):
		return default or {}


def get_business_hours():
	"""
	Get business hours from settings.

	Returns:
		dict: Business hours configuration
	"""
	settings = frappe.get_single("AI Communications Hub Settings")

	return {
		"start": settings.business_hours_start or "09:00:00",
		"end": settings.business_hours_end or "17:00:00",
		"timezone": settings.timezone or "America/New_York",
		"weekdays_only": settings.weekdays_only or 1
	}


def is_business_hours():
	"""
	Check if current time is within business hours.

	Returns:
		bool: True if within business hours
	"""
	hours = get_business_hours()
	now = datetime.now()

	# Check weekday if enabled
	if hours["weekdays_only"] and now.weekday() >= 5:  # Saturday = 5, Sunday = 6
		return False

	# Parse business hours
	start_time = datetime.strptime(hours["start"], "%H:%M:%S").time()
	end_time = datetime.strptime(hours["end"], "%H:%M:%S").time()
	current_time = now.time()

	return start_time <= current_time <= end_time


def get_customer_from_identifier(identifier, platform):
	"""
	Get Customer record from platform-specific identifier.

	Args:
		identifier (str): Platform-specific ID (PSID, phone, username, etc.)
		platform (str): Platform name

	Returns:
		str: Customer name or None
	"""
	field_map = {
		"Voice": "mobile_no",
		"SMS": "mobile_no",
		"WhatsApp": "mobile_no",
		"Facebook": "facebook_psid",
		"Instagram": "instagram_id",
		"Twitter": "twitter_id",
		"LinkedIn": "linkedin_profile",
		"Email": "email_id"
	}

	field = field_map.get(platform)
	if not field:
		return None

	customers = frappe.get_all(
		"Customer",
		filters={field: identifier},
		limit=1
	)

	return customers[0].name if customers else None


def get_platform_message_limit(platform):
	"""
	Get maximum message length for a platform.

	Args:
		platform (str): Platform name (Voice, Chat, SMS, etc.)

	Returns:
		int: Maximum character limit
	"""
	limits = get_platform_limits(platform)
	return limits.get("max_chars") or 10000  # Default to 10K if no limit
