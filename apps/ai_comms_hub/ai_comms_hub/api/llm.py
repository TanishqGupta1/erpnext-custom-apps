"""
LLM Integration Module

Handles communication with naga.ac (OpenAI-compatible API).
"""

import frappe
from frappe import _
import requests
import json


def get_llm_settings():
	"""Get LLM settings from AI Communications Hub Settings"""
	settings = frappe.get_single("AI Communications Hub Settings")
	# Use get_password() for Password fields to get decrypted value
	api_key = settings.get_password("llm_api_key") if settings.llm_api_key else None
	return {
		"api_url": settings.llm_api_url or "https://api.naga.ac/v1",
		"api_key": api_key,
		"model": settings.llm_model or "gpt-4o-mini",
		"max_tokens": settings.llm_max_tokens or 500,
		"temperature": settings.llm_temperature or 0.7
	}


def generate_completion(messages, functions=None, max_tokens=None, temperature=None):
	"""
	Generate LLM completion using naga.ac API.

	Args:
		messages (list): List of message dicts with role and content
		functions (list, optional): Function definitions for function calling
		max_tokens (int, optional): Override max tokens
		temperature (float, optional): Override temperature

	Returns:
		dict: API response with choices
	"""
	settings = get_llm_settings()

	# Build request payload
	payload = {
		"model": settings["model"],
		"messages": messages,
		"max_tokens": max_tokens or settings["max_tokens"],
		"temperature": temperature or settings["temperature"]
	}

	if functions:
		payload["functions"] = functions
		payload["function_call"] = "auto"

	# Make API request
	try:
		response = requests.post(
			f"{settings['api_url']}/chat/completions",
			headers={
				"Authorization": f"Bearer {settings['api_key']}",
				"Content-Type": "application/json"
			},
			json=payload,
			timeout=30
		)

		response.raise_for_status()
		return response.json()

	except requests.exceptions.RequestException as e:
		frappe.log_error(f"LLM API Error: {str(e)}", "LLM Integration")
		raise


def generate_summary(text, prompt=None):
	"""
	Generate summary of text using LLM.

	Args:
		text (str): Text to summarize
		prompt (str, optional): Custom prompt

	Returns:
		str: Generated summary
	"""
	default_prompt = "Summarize the following text in 2-3 sentences:"

	messages = [
		{"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
		{"role": "user", "content": f"{prompt or default_prompt}\n\n{text}"}
	]

	response = generate_completion(messages, max_tokens=200)

	return response["choices"][0]["message"]["content"].strip()


def classify_sentiment(text):
	"""
	Classify sentiment of text.

	Args:
		text (str): Text to analyze

	Returns:
		str: Positive, Neutral, or Negative
	"""
	messages = [
		{"role": "system", "content": "You are a sentiment analysis assistant. Respond with only: Positive, Neutral, or Negative."},
		{"role": "user", "content": f"Classify the sentiment of this text:\n\n{text}"}
	]

	response = generate_completion(messages, max_tokens=10, temperature=0.3)
	sentiment = response["choices"][0]["message"]["content"].strip()

	# Validate response
	if sentiment not in ["Positive", "Neutral", "Negative"]:
		return "Neutral"

	return sentiment


def generate_response_with_context(conversation_history, platform, rag_context=None):
	"""
	Generate AI response with conversation context and platform-specific guidelines.

	Args:
		conversation_history (list): List of previous messages
		platform (str): Channel (Voice, Facebook, Email, etc.)
		rag_context (list, optional): Retrieved knowledge base documents

	Returns:
		dict: Generated response with content and metadata
	"""
	# Build system prompt with platform guidelines
	system_prompt = build_platform_system_prompt(platform, rag_context)

	# Build messages
	messages = [{"role": "system", "content": system_prompt}]

	# Add conversation history
	for msg in conversation_history:
		role = "user" if msg["sender_type"] == "Customer" else "assistant"
		messages.append({"role": role, "content": msg["content"]})

	# Generate response
	response = generate_completion(messages)

	return {
		"content": response["choices"][0]["message"]["content"],
		"finish_reason": response["choices"][0]["finish_reason"],
		"usage": response.get("usage", {})
	}


def build_platform_system_prompt(platform, rag_context=None):
	"""
	Build platform-specific system prompt.

	Args:
		platform (str): Channel name
		rag_context (list, optional): Knowledge base context

	Returns:
		str: System prompt
	"""
	platform_guidelines = {
		"Voice": {
			"tone": "conversational and clear",
			"length": "concise, 1-2 sentences per response",
			"style": "natural speech, avoid complex words"
		},
		"Facebook": {
			"tone": "friendly and conversational",
			"length": "up to 2000 characters",
			"style": "casual, use emojis sparingly"
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
			"style": "proper grammar, formatted with paragraphs"
		}
	}

	guidelines = platform_guidelines.get(platform, platform_guidelines["Email"])

	prompt = f"""You are a helpful AI assistant for a business, communicating via {platform}.

Guidelines for {platform}:
- Tone: {guidelines['tone']}
- Length: {guidelines['length']}
- Style: {guidelines['style']}

"""

	if rag_context:
		prompt += "Knowledge Base Context:\n"
		for doc in rag_context:
			prompt += f"- {doc.get('content', '')}\n"
		prompt += "\n"

	prompt += """Your task is to:
1. Understand customer needs
2. Provide accurate information from knowledge base
3. Be helpful and professional
4. Escalate to human if needed (say "Let me connect you with a team member")

If you need to lookup information, use function calls.
"""

	return prompt


def build_function_definitions():
	"""
	Build function definitions for LLM function calling.

	Returns:
		list: Function definitions in OpenAI format
	"""
	return [
		{
			"name": "getOrderStatus",
			"description": "Get the status of a customer order by order number",
			"parameters": {
				"type": "object",
				"properties": {
					"order_number": {
						"type": "string",
						"description": "The order number (e.g., SO-001)"
					}
				},
				"required": ["order_number"]
			}
		},
		{
			"name": "createQuote",
			"description": "Create a quote for customer with product specifications",
			"parameters": {
				"type": "object",
				"properties": {
					"customer_name": {
						"type": "string",
						"description": "Customer name"
					},
					"product_name": {
						"type": "string",
						"description": "Product or service name"
					},
					"quantity": {
						"type": "number",
						"description": "Quantity requested"
					},
					"specifications": {
						"type": "string",
						"description": "Additional specifications or requirements"
					}
				},
				"required": ["customer_name", "product_name"]
			}
		},
		{
			"name": "searchKnowledge",
			"description": "Search the knowledge base for information about products, policies, or procedures",
			"parameters": {
				"type": "object",
				"properties": {
					"query": {
						"type": "string",
						"description": "Search query"
					}
				},
				"required": ["query"]
			}
		},
		{
			"name": "scheduleAppointment",
			"description": "Schedule an appointment or consultation",
			"parameters": {
				"type": "object",
				"properties": {
					"customer_name": {
						"type": "string",
						"description": "Customer name"
					},
					"preferred_date": {
						"type": "string",
						"description": "Preferred date (YYYY-MM-DD)"
					},
					"preferred_time": {
						"type": "string",
						"description": "Preferred time (HH:MM)"
					},
					"purpose": {
						"type": "string",
						"description": "Purpose of appointment"
					}
				},
				"required": ["customer_name", "purpose"]
			}
		},
		{
			"name": "getProductInfo",
			"description": "Get detailed information about a product",
			"parameters": {
				"type": "object",
				"properties": {
					"product_name": {
						"type": "string",
						"description": "Product name or SKU"
					}
				},
				"required": ["product_name"]
			}
		},
		{
			"name": "getCustomerInfo",
			"description": "Get information about the current customer including recent orders and outstanding balance",
			"parameters": {
				"type": "object",
				"properties": {},
				"required": []
			}
		},
		{
			"name": "checkInventory",
			"description": "Check inventory availability for a product",
			"parameters": {
				"type": "object",
				"properties": {
					"product_name": {
						"type": "string",
						"description": "Product name or SKU to check"
					}
				},
				"required": ["product_name"]
			}
		}
	]
