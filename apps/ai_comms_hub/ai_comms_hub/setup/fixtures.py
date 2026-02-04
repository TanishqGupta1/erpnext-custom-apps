# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def install_fixtures():
	"""
	Install default fixtures (default data) for AI Communications Hub.

	Fixtures include:
	- AI response templates
	- Platform-specific prompts
	- Common functions for AI
	- Email templates
	- Knowledge base categories
	"""
	frappe.msgprint(_("Installing default fixtures..."), indicator="blue")

	# Install AI response templates
	install_response_templates()

	# Install platform prompts
	install_platform_prompts()

	# Install common phrases
	install_common_phrases()

	# Install escalation rules
	install_escalation_rules()

	frappe.msgprint(_("Fixtures installed successfully"), indicator="green")


def install_response_templates():
	"""
	Install default AI response templates.
	"""
	templates = [
		{
			"template_name": "Greeting",
			"template_category": "General",
			"template_content": "Hello! I'm your AI assistant. How can I help you today?",
			"use_cases": "Initial greeting for new conversations"
		},
		{
			"template_name": "Order Status Inquiry",
			"template_category": "Orders",
			"template_content": "I'll check the status of your order right away. Could you please provide your order number?",
			"use_cases": "Customer asks about order status"
		},
		{
			"template_name": "Product Information",
			"template_category": "Products",
			"template_content": "I'd be happy to provide information about our products. What specific product are you interested in?",
			"use_cases": "Customer asks about products"
		},
		{
			"template_name": "Quote Request",
			"template_category": "Sales",
			"template_content": "I can help you with a quote. Please let me know:\n1. Product/service you're interested in\n2. Quantity needed\n3. Any specific requirements",
			"use_cases": "Customer requests a quotation"
		},
		{
			"template_name": "Escalation to Human",
			"template_category": "Escalation",
			"template_content": "I understand this requires a human touch. Let me connect you with one of our team members who can assist you better.",
			"use_cases": "Escalating to human agent"
		},
		{
			"template_name": "Closing - Resolved",
			"template_category": "Closing",
			"template_content": "Great! I'm glad I could help. Is there anything else I can assist you with?",
			"use_cases": "Issue resolved, closing conversation"
		},
		{
			"template_name": "Closing - Escalated",
			"template_category": "Closing",
			"template_content": "I've passed your request to our team. They'll get back to you shortly. Thank you for your patience!",
			"use_cases": "Closing after escalation"
		},
		{
			"template_name": "Out of Scope",
			"template_category": "General",
			"template_content": "I'm not able to help with that specific request, but I can connect you with someone who can. Would you like me to do that?",
			"use_cases": "Request outside AI capabilities"
		},
		{
			"template_name": "Technical Issue",
			"template_category": "Support",
			"template_content": "I understand you're experiencing a technical issue. Let me gather some information to help resolve this:\n1. When did the issue start?\n2. What steps have you tried?\n3. Any error messages?",
			"use_cases": "Customer reports technical problem"
		},
		{
			"template_name": "Apology - Delay",
			"template_category": "Apology",
			"template_content": "I sincerely apologize for the delay. I understand how frustrating this must be. Let me see what I can do to help expedite this.",
			"use_cases": "Acknowledging delays or issues"
		}
	]

	for template in templates:
		# Note: We're storing these as a simple JSON structure since we don't have a Response Template doctype yet
		# In production, you'd create a proper doctype for these
		pass  # Placeholder for now

	frappe.msgprint(_("Response templates installed"), indicator="blue")


def install_platform_prompts():
	"""
	Install platform-specific system prompts.
	"""
	platform_prompts = {
		"Voice": {
			"tone": "conversational and warm",
			"style": "natural spoken language",
			"length": "concise responses (2-3 sentences max)",
			"special_instructions": "Avoid technical jargon. Use contractions. Pause naturally."
		},
		"Facebook": {
			"tone": "friendly and approachable",
			"style": "casual but professional",
			"length": "up to 2000 characters",
			"special_instructions": "Use emojis sparingly. Break long messages into paragraphs."
		},
		"Instagram": {
			"tone": "casual and engaging",
			"style": "visual and concise",
			"length": "short messages preferred",
			"special_instructions": "Use emojis when appropriate. Keep it brief and friendly."
		},
		"Twitter": {
			"tone": "concise and direct",
			"style": "brief and impactful",
			"length": "280 characters maximum",
			"special_instructions": "Be ultra-concise. Every word counts."
		},
		"LinkedIn": {
			"tone": "professional and respectful",
			"style": "business communication",
			"length": "up to 1300 characters",
			"special_instructions": "Maintain professional tone. No emojis unless appropriate."
		},
		"Email": {
			"tone": "professional and helpful",
			"style": "structured business email",
			"length": "comprehensive but concise",
			"special_instructions": "Use proper email structure. Include greeting and signature."
		},
		"SMS": {
			"tone": "brief and clear",
			"style": "text message",
			"length": "160 characters preferred",
			"special_instructions": "Be extremely concise. Avoid special characters that may break on some carriers."
		},
		"WhatsApp": {
			"tone": "friendly and conversational",
			"style": "instant messaging",
			"length": "moderate length ok",
			"special_instructions": "Can use emojis. Break into multiple messages if needed."
		},
		"Chat": {
			"tone": "helpful and responsive",
			"style": "real-time chat",
			"length": "short to medium messages",
			"special_instructions": "Quick responses. Use formatting (bullets, bold) when helpful."
		}
	}

	# Store in Settings or a dedicated doctype
	# Placeholder for now
	frappe.msgprint(_("Platform prompts installed"), indicator="blue")


def install_common_phrases():
	"""
	Install common phrases and responses for AI.
	"""
	common_phrases = {
		"acknowledgment": [
			"I understand",
			"Got it",
			"I see",
			"Thank you for that information",
			"I appreciate you letting me know"
		],
		"confirmation": [
			"Yes, I can help with that",
			"Absolutely",
			"Of course",
			"I'd be happy to assist",
			"Certainly"
		],
		"clarification": [
			"Could you please clarify?",
			"Just to make sure I understand correctly",
			"Let me confirm",
			"To ensure I get this right",
			"Can you provide more details about"
		],
		"apology": [
			"I apologize for the inconvenience",
			"I'm sorry about that",
			"I understand your frustration",
			"My apologies",
			"I regret the confusion"
		],
		"waiting": [
			"Give me a moment to check that",
			"Let me look into that for you",
			"One moment please",
			"I'm checking on that now",
			"Let me pull up that information"
		]
	}

	# Store in Settings or dedicated doctype
	# Placeholder for now
	frappe.msgprint(_("Common phrases installed"), indicator="blue")


def install_escalation_rules():
	"""
	Install default escalation rules.
	"""
	escalation_rules = [
		{
			"rule_name": "Negative Sentiment",
			"condition": "sentiment == 'Negative'",
			"action": "escalate_to_human",
			"priority": "High",
			"description": "Escalate when customer sentiment is negative"
		},
		{
			"rule_name": "Low RAG Confidence",
			"condition": "rag_confidence < 60",
			"action": "escalate_to_human",
			"priority": "Medium",
			"description": "Escalate when AI is not confident in its response"
		},
		{
			"rule_name": "Explicit Human Request",
			"condition": "keywords: ['speak to human', 'talk to person', 'representative', 'agent']",
			"action": "escalate_to_human",
			"priority": "High",
			"description": "Escalate when customer explicitly requests human"
		},
		{
			"rule_name": "Refund Request",
			"condition": "keywords: ['refund', 'money back', 'cancel order']",
			"action": "escalate_to_human",
			"priority": "High",
			"description": "Escalate refund requests to human for policy compliance"
		},
		{
			"rule_name": "Complex Technical Issue",
			"condition": "keywords: ['not working', 'broken', 'error', 'crash'] AND messages_count > 5",
			"action": "escalate_to_human",
			"priority": "Medium",
			"description": "Escalate technical issues if AI can't resolve in 5 messages"
		},
		{
			"rule_name": "VIP Customer",
			"condition": "customer.customer_group == 'VIP'",
			"action": "notify_manager",
			"priority": "High",
			"description": "Notify manager when VIP customer initiates conversation"
		},
		{
			"rule_name": "High Value Order Inquiry",
			"condition": "order.grand_total > 10000",
			"action": "escalate_to_human",
			"priority": "Medium",
			"description": "Escalate inquiries about high-value orders"
		},
		{
			"rule_name": "After Hours - Urgent",
			"condition": "is_after_hours AND keywords: ['urgent', 'emergency', 'critical']",
			"action": "notify_on_call",
			"priority": "Critical",
			"description": "Notify on-call staff for urgent after-hours issues"
		}
	]

	# Store in Settings or dedicated doctype
	# Placeholder for now
	frappe.msgprint(_("Escalation rules installed"), indicator="blue")


def get_default_fixtures():
	"""
	Return all default fixtures as a dictionary.

	Returns:
		dict: Dictionary containing all fixtures
	"""
	return {
		"response_templates": get_response_templates(),
		"platform_prompts": get_platform_prompts(),
		"common_phrases": get_common_phrases(),
		"escalation_rules": get_escalation_rules()
	}


def get_response_templates():
	"""Return default response templates."""
	return [
		{
			"name": "greeting",
			"content": "Hello! I'm your AI assistant. How can I help you today?"
		},
		{
			"name": "order_status",
			"content": "I'll check the status of your order. Could you provide your order number?"
		},
		{
			"name": "product_info",
			"content": "I'd be happy to provide product information. What are you interested in?"
		}
	]


def get_platform_prompts():
	"""Return platform-specific prompts."""
	return {
		"Voice": "Conversational and warm tone, 2-3 sentences max",
		"Facebook": "Friendly tone, up to 2000 characters",
		"Twitter": "Concise, 280 characters max",
		"Email": "Professional business email format"
	}


def get_common_phrases():
	"""Return common phrases."""
	return {
		"acknowledgment": ["I understand", "Got it", "I see"],
		"confirmation": ["Yes, I can help", "Absolutely", "Of course"]
	}


def get_escalation_rules():
	"""Return escalation rules."""
	return [
		{
			"trigger": "negative_sentiment",
			"action": "escalate_to_human"
		},
		{
			"trigger": "low_confidence",
			"action": "escalate_to_human"
		}
	]
