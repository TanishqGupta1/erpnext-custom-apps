import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, now_datetime
import re


class ResponseTemplate(Document):
	def validate(self):
		self.validate_shortcut_key()
		self.set_created_info()

	def before_save(self):
		if not self.owner_user and not self.is_public:
			self.owner_user = frappe.session.user

	def validate_shortcut_key(self):
		"""Ensure shortcut key is unique and properly formatted."""
		if self.shortcut_key:
			# Normalize shortcut key
			self.shortcut_key = self.shortcut_key.lower().strip()
			if not self.shortcut_key.startswith("/"):
				self.shortcut_key = "/" + self.shortcut_key

			# Check uniqueness
			existing = frappe.db.exists(
				"Response Template",
				{"shortcut_key": self.shortcut_key, "name": ["!=", self.name]}
			)
			if existing:
				frappe.throw(f"Shortcut key '{self.shortcut_key}' is already in use")

	def set_created_info(self):
		"""Set created by and created on if not set."""
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_on:
			self.created_on = nowdate()

	def render(self, context=None):
		"""
		Render template with context variables.

		Args:
			context: Dictionary of variables to substitute

		Returns:
			Rendered content string
		"""
		content = self.content
		subject = self.subject

		if not context:
			context = {}

		# Add default variables
		default_context = {
			"date": nowdate(),
			"time": frappe.utils.nowtime(),
			"company_name": frappe.defaults.get_global_default("company") or "Our Company",
			"agent_name": frappe.db.get_value("User", frappe.session.user, "full_name") or "Support Agent"
		}
		default_context.update(context)

		# Replace variables in content
		for key, value in default_context.items():
			pattern = r"\{\{\s*" + key + r"\s*\}\}"
			content = re.sub(pattern, str(value or ""), content)
			if subject:
				subject = re.sub(pattern, str(value or ""), subject)

		return {
			"subject": subject,
			"content": content
		}

	def record_usage(self):
		"""Record template usage."""
		frappe.db.set_value(
			"Response Template",
			self.name,
			{
				"usage_count": self.usage_count + 1,
				"last_used": now_datetime()
			},
			update_modified=False
		)

	def get_translation(self, language):
		"""Get translated content for a language."""
		for translation in self.translations:
			if translation.language == language:
				return {
					"subject": translation.subject,
					"content": translation.content
				}
		return None


@frappe.whitelist()
def get_templates(category=None, channel=None, search=None, user=None):
	"""
	Get available response templates.

	Args:
		category: Filter by category
		channel: Filter by applicable channel
		search: Search term
		user: User to get templates for (for private templates)

	Returns:
		List of templates
	"""
	filters = {"is_active": 1}

	if category:
		filters["category"] = category

	if channel and channel != "All":
		filters["applicable_channels"] = ["in", ["All", channel]]

	# Handle public/private templates
	or_filters = [["is_public", "=", 1]]
	if user:
		or_filters.append(["owner_user", "=", user])

	templates = frappe.get_all(
		"Response Template",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "template_name", "category", "shortcut_key",
			"subject", "content", "applicable_channels", "usage_count"
		],
		order_by="usage_count desc, template_name asc"
	)

	# Apply search filter
	if search:
		search_lower = search.lower()
		templates = [
			t for t in templates
			if search_lower in t.template_name.lower()
			or (t.shortcut_key and search_lower in t.shortcut_key.lower())
			or search_lower in (t.content or "").lower()
		]

	return templates


@frappe.whitelist()
def get_template_by_shortcut(shortcut_key):
	"""
	Get template by shortcut key.

	Args:
		shortcut_key: Shortcut key (e.g., /greeting)

	Returns:
		Template document or None
	"""
	if not shortcut_key.startswith("/"):
		shortcut_key = "/" + shortcut_key

	template_name = frappe.db.get_value(
		"Response Template",
		{"shortcut_key": shortcut_key, "is_active": 1},
		"name"
	)

	if template_name:
		return frappe.get_doc("Response Template", template_name)
	return None


@frappe.whitelist()
def render_template(template_name, context=None):
	"""
	Render a template with context.

	Args:
		template_name: Template name or shortcut key
		context: JSON string or dict of context variables

	Returns:
		Rendered template content
	"""
	import json

	# Handle shortcut key
	if template_name.startswith("/"):
		template = get_template_by_shortcut(template_name)
		if not template:
			frappe.throw(f"Template with shortcut '{template_name}' not found")
	else:
		template = frappe.get_doc("Response Template", template_name)

	# Parse context
	if isinstance(context, str):
		context = json.loads(context) if context else {}

	# Render and record usage
	result = template.render(context)
	template.record_usage()

	return result


@frappe.whitelist()
def suggest_templates(message_content, channel=None, limit=5):
	"""
	Suggest templates based on message content.

	Args:
		message_content: Message to analyze
		channel: Current channel
		limit: Maximum suggestions

	Returns:
		List of suggested templates
	"""
	filters = {
		"is_active": 1,
		"use_for_ai_suggestions": 1
	}

	if channel:
		filters["applicable_channels"] = ["in", ["All", channel]]

	templates = frappe.get_all(
		"Response Template",
		filters=filters,
		fields=[
			"name", "template_name", "ai_trigger_keywords",
			"ai_priority", "content", "shortcut_key"
		],
		order_by="ai_priority desc"
	)

	# Score templates based on keyword matches
	message_lower = message_content.lower()
	scored_templates = []

	for template in templates:
		score = 0
		if template.ai_trigger_keywords:
			keywords = [k.strip().lower() for k in template.ai_trigger_keywords.split(",")]
			for keyword in keywords:
				if keyword and keyword in message_lower:
					score += template.ai_priority or 5

		if score > 0:
			scored_templates.append({
				"name": template.name,
				"template_name": template.template_name,
				"shortcut_key": template.shortcut_key,
				"score": score,
				"preview": (template.content or "")[:100] + "..."
			})

	# Sort by score and limit
	scored_templates.sort(key=lambda x: x["score"], reverse=True)
	return scored_templates[:limit]


@frappe.whitelist()
def get_template_categories():
	"""Get all active template categories with counts."""
	categories = frappe.get_all(
		"Response Template Category",
		filters={"is_active": 1},
		fields=["name", "category_name", "description", "icon", "color"]
	)

	for cat in categories:
		cat["template_count"] = frappe.db.count(
			"Response Template",
			filters={"category": cat.name, "is_active": 1}
		)

	return categories
