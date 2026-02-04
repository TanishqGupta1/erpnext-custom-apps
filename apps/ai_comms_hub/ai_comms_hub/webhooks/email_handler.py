"""
Email Webhook Handler

Handles inbound emails from SendGrid Inbound Parse.
"""

import frappe
from frappe import _
import json
from datetime import datetime
import re
from email.utils import parseaddr


@frappe.whitelist(allow_guest=True)
def handle_sendgrid_webhook():
	"""
	Handle SendGrid Inbound Parse webhook.

	SendGrid forwards emails to this endpoint with:
	- to, from, subject, text, html
	- attachments
	- headers (for threading)
	"""
	try:
		# Get form data (SendGrid sends multipart/form-data)
		data = frappe.local.form_dict

		# Extract email fields
		to_email = data.get("to")
		from_email = data.get("from")
		subject = data.get("subject", "")
		text_content = data.get("text", "")
		html_content = data.get("html", "")

		# Get headers for threading
		headers = data.get("headers", "")
		message_id = extract_header(headers, "Message-ID")
		in_reply_to = extract_header(headers, "In-Reply-To")
		references = extract_header(headers, "References")

		# Clean email content
		cleaned_text = clean_email_content(text_content)

		# Find or create hub
		hub = get_or_create_email_hub(
			from_email=from_email,
			to_email=to_email,
			subject=subject,
			in_reply_to=in_reply_to,
			message_id=message_id
		)

		# Create message
		msg = frappe.get_doc({
			"doctype": "Communication Message",
			"communication_hub": hub.name,
			"sender_type": "Customer",
			"sender_name": parseaddr(from_email)[0] or from_email,
			"sender_identifier": from_email,
			"content": cleaned_text,
			"content_type": "text",
			"timestamp": datetime.now(),
			"platform_message_id": message_id
		})
		msg.insert()
		frappe.db.commit()

		# Process attachments
		process_email_attachments(data, hub.name, msg.name)

		# Trigger AI response
		if hub.ai_mode == "Autonomous":
			frappe.enqueue(
				"ai_comms_hub.api.ai_engine.generate_email_response",
				hub_id=hub.name,
				message_id=msg.name,
				queue="default"
			)

		return {"status": "success", "hub_id": hub.name}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "SendGrid Webhook Error")
		return {"status": "error", "message": str(e)}


def extract_header(headers_string, header_name):
	"""
	Extract specific header from headers string.

	Args:
		headers_string (str): Full headers string
		header_name (str): Header to extract (e.g., "Message-ID")

	Returns:
		str: Header value or None
	"""
	if not headers_string:
		return None

	# Parse headers
	for line in headers_string.split("\n"):
		if line.startswith(f"{header_name}:"):
			return line.split(":", 1)[1].strip()

	return None


def clean_email_content(text):
	"""
	Clean email content by removing:
	- Quoted replies (> lines)
	- Email signatures
	- Forwarded message headers
	- Excessive whitespace

	Args:
		text (str): Raw email text

	Returns:
		str: Cleaned text
	"""
	if not text:
		return ""

	lines = text.split("\n")
	cleaned_lines = []

	# Signature markers
	signature_markers = [
		"--",
		"Sent from",
		"Get Outlook for",
		"Best regards",
		"Thanks",
		"Sincerely"
	]

	in_quote = False

	for line in lines:
		stripped = line.strip()

		# Skip quoted replies
		if stripped.startswith(">"):
			in_quote = True
			continue

		# Stop at signature
		if any(marker in stripped for marker in signature_markers):
			break

		# Stop at forwarded message
		if "-----Original Message-----" in stripped:
			break

		if stripped:
			cleaned_lines.append(line)

	# Join and remove excessive whitespace
	cleaned = "\n".join(cleaned_lines)
	cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

	return cleaned.strip()


def get_or_create_email_hub(from_email, to_email, subject, in_reply_to=None, message_id=None):
	"""
	Find or create Communication Hub for email conversation.

	Args:
		from_email (str): Sender email
		to_email (str): Recipient email
		subject (str): Email subject
		in_reply_to (str, optional): In-Reply-To header
		message_id (str, optional): Message-ID header

	Returns:
		Document: Communication Hub
	"""
	# Try to find existing thread using In-Reply-To
	if in_reply_to:
		existing = frappe.db.get_value(
			"Communication Hub",
			{
				"email_message_id": in_reply_to,
				"status": ["in", ["Open", "In Progress"]]
			},
			"name"
		)

		if existing:
			hub = frappe.get_doc("Communication Hub", existing)
			# Update thread ID
			hub.email_thread_id = extract_thread_id(subject, message_id)
			hub.email_in_reply_to = in_reply_to
			hub.email_message_id = message_id
			hub.save()
			return hub

	# Try to find by thread_id (subject-based)
	thread_id = extract_thread_id(subject, message_id)
	if thread_id:
		existing = frappe.db.get_value(
			"Communication Hub",
			{
				"email_thread_id": thread_id,
				"status": ["in", ["Open", "In Progress"]]
			},
			"name"
		)

		if existing:
			return frappe.get_doc("Communication Hub", existing)

	# Find or create customer
	customer = get_or_create_customer_by_email(from_email)

	# Classify intent from subject and body
	intent = classify_email_intent(subject)

	# Create new hub
	hub = frappe.get_doc({
		"doctype": "Communication Hub",
		"customer": customer.name,
		"channel": "Email",
		"status": "Open",
		"ai_mode": "Autonomous",
		"email_from": from_email,
		"email_to": to_email,
		"email_subject": subject,
		"email_thread_id": thread_id,
		"email_in_reply_to": in_reply_to,
		"email_message_id": message_id,
		"subject": subject,
		"intent": intent
	})
	hub.insert()
	frappe.db.commit()

	return hub


def extract_thread_id(subject, message_id=None):
	"""
	Extract or generate thread ID for email threading.

	Args:
		subject (str): Email subject
		message_id (str, optional): Message-ID

	Returns:
		str: Thread ID
	"""
	# Remove Re:, Fwd:, etc.
	clean_subject = re.sub(r'^(Re|Fwd|Fw):\s*', '', subject, flags=re.IGNORECASE).strip()

	# Generate thread ID from subject
	import hashlib
	return hashlib.md5(clean_subject.encode()).hexdigest()[:16]


def classify_email_intent(subject):
	"""
	Classify email intent from subject line.

	Args:
		subject (str): Email subject

	Returns:
		str: Intent classification
	"""
	subject_lower = subject.lower()

	intents = {
		"Quote Request": ["quote", "pricing", "price", "cost", "estimate"],
		"Order Status": ["order", "status", "tracking", "delivery", "shipped"],
		"Complaint": ["unhappy", "disappointed", "complaint", "problem", "refund"],
		"Support": ["help", "support", "issue", "problem", "not working"],
		"General Inquiry": ["question", "info", "information", "wondering"]
	}

	for intent, keywords in intents.items():
		if any(keyword in subject_lower for keyword in keywords):
			return intent

	return "General Inquiry"


def process_email_attachments(data, hub_id, message_id):
	"""
	Process email attachments from SendGrid.

	Args:
		data (dict): Form data from SendGrid
		hub_id (str): Communication Hub ID
		message_id (str): Message ID
	"""
	import os
	import base64

	# SendGrid sends attachment info in different formats:
	# - attachment-info: JSON with metadata
	# - attachment1, attachment2, etc.: File content

	attachment_info = data.get("attachment-info")
	if attachment_info:
		try:
			attachment_info = json.loads(attachment_info) if isinstance(attachment_info, str) else attachment_info
		except (json.JSONDecodeError, TypeError):
			attachment_info = {}

	# Get attachment keys
	attachment_keys = [k for k in data.keys() if k.startswith("attachment") and k != "attachment-info"]

	saved_attachments = []

	for key in attachment_keys:
		try:
			# Get attachment content
			attachment = data.get(key)
			if not attachment:
				continue

			# Get metadata for this attachment
			# Key format: attachment1, attachment2, etc.
			attachment_num = key.replace("attachment", "")
			metadata = attachment_info.get(f"attachment{attachment_num}", {})

			filename = metadata.get("filename", metadata.get("name", f"attachment_{attachment_num}"))
			content_type = metadata.get("type", metadata.get("content-type", "application/octet-stream"))

			# Handle file content
			if hasattr(attachment, 'read'):
				# It's a file object
				file_content = attachment.read()
			elif isinstance(attachment, str):
				# It might be base64 encoded
				try:
					file_content = base64.b64decode(attachment)
				except Exception:
					file_content = attachment.encode('utf-8')
			else:
				file_content = attachment

			# Save to Frappe File doctype
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": filename,
				"attached_to_doctype": "Communication Message",
				"attached_to_name": message_id,
				"content": file_content,
				"is_private": 1
			})

			# Use save_file method for proper file handling
			file_url = save_attachment_file(filename, file_content, message_id)

			if file_url:
				saved_attachments.append({
					"filename": filename,
					"content_type": content_type,
					"file_url": file_url
				})

				frappe.logger().info(f"Saved email attachment: {filename}")

		except Exception as e:
			frappe.log_error(f"Error processing attachment {key}: {str(e)}", "Email Attachment Error")

	# Update message with attachment info
	if saved_attachments:
		frappe.db.set_value(
			"Communication Message",
			message_id,
			"attachments_json",
			json.dumps(saved_attachments)
		)
		frappe.db.commit()

	return saved_attachments


def save_attachment_file(filename, content, attached_to):
	"""
	Save attachment file to Frappe file system.

	Args:
		filename (str): Original filename
		content (bytes): File content
		attached_to (str): Document name to attach to

	Returns:
		str: File URL or None
	"""
	import os

	try:
		# Create temp directory if not exists
		temp_dir = frappe.get_site_path("private", "files", "ai_comms_attachments")
		os.makedirs(temp_dir, exist_ok=True)

		# Generate unique filename
		import hashlib
		file_hash = hashlib.md5(content[:1000] if len(content) > 1000 else content).hexdigest()[:8]
		safe_filename = f"{file_hash}_{filename}"

		# Save file
		file_path = os.path.join(temp_dir, safe_filename)
		with open(file_path, 'wb') as f:
			f.write(content if isinstance(content, bytes) else content.encode())

		# Create File record
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": filename,
			"attached_to_doctype": "Communication Message",
			"attached_to_name": attached_to,
			"file_url": f"/private/files/ai_comms_attachments/{safe_filename}",
			"is_private": 1
		})
		file_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		return file_doc.file_url

	except Exception as e:
		frappe.log_error(f"Error saving attachment {filename}: {str(e)}", "Attachment Save Error")
		return None


def get_or_create_customer_by_email(email):
	"""
	Find or create customer from email address.

	Args:
		email (str): Email address

	Returns:
		Document: Customer
	"""
	# Parse email
	name, email_addr = parseaddr(email)

	# Try to find existing customer
	customer_name = frappe.db.get_value("Customer", {"email_id": email_addr}, "name")

	if customer_name:
		return frappe.get_doc("Customer", customer_name)

	# Create new customer
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": name or email_addr.split("@")[0],
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "All Territories",
		"email_id": email_addr
	})
	customer.insert(ignore_permissions=True)
	frappe.db.commit()

	return customer
