#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Unit tests for LLM API module.
"""

import unittest
import frappe
from ai_comms_hub.api.llm import (
	get_llm_settings,
	generate_completion,
	call_with_function_calling,
	validate_function_call_response
)


class TestLLM(unittest.TestCase):
	"""Test LLM API functionality."""

	def setUp(self):
		"""Set up test environment."""
		self.settings = get_llm_settings()

	def test_get_llm_settings(self):
		"""Test LLM settings retrieval."""
		self.assertIsNotNone(self.settings)
		self.assertIn("api_key", self.settings)
		self.assertIn("base_url", self.settings)
		self.assertIn("model", self.settings)

	def test_generate_completion_simple(self):
		"""Test simple completion generation."""
		messages = [
			{"role": "user", "content": "Say 'test' if you can read this"}
		]

		response = generate_completion(messages, max_tokens=50, temperature=0)

		self.assertIsNotNone(response)
		self.assertIn("test", response.lower())

	def test_generate_completion_with_system(self):
		"""Test completion with system message."""
		messages = [
			{"role": "system", "content": "You are a helpful assistant that always responds with 'OK'."},
			{"role": "user", "content": "Hello"}
		]

		response = generate_completion(messages, max_tokens=10, temperature=0)

		self.assertIsNotNone(response)
		self.assertIn("ok", response.lower())

	def test_generate_completion_with_history(self):
		"""Test completion with conversation history."""
		messages = [
			{"role": "user", "content": "My name is Alice"},
			{"role": "assistant", "content": "Hello Alice! How can I help you?"},
			{"role": "user", "content": "What is my name?"}
		]

		response = generate_completion(messages, max_tokens=50, temperature=0)

		self.assertIsNotNone(response)
		self.assertIn("alice", response.lower())

	def test_function_calling_schema(self):
		"""Test function calling with schema."""
		functions = [
			{
				"name": "get_order_status",
				"description": "Get the status of a customer order",
				"parameters": {
					"type": "object",
					"properties": {
						"order_id": {
							"type": "string",
							"description": "The order ID"
						}
					},
					"required": ["order_id"]
				}
			}
		]

		messages = [
			{"role": "user", "content": "What's the status of order ORD-123?"}
		]

		response = call_with_function_calling(messages, functions)

		self.assertIsNotNone(response)
		# Response should either be a function call or text
		self.assertTrue(
			isinstance(response, str) or
			(isinstance(response, dict) and "function_call" in response)
		)

	def test_validate_function_call_response(self):
		"""Test function call response validation."""
		# Valid function call
		valid_response = {
			"function_call": {
				"name": "get_order_status",
				"arguments": '{"order_id": "ORD-123"}'
			}
		}

		is_valid, error = validate_function_call_response(valid_response, ["get_order_status"])
		self.assertTrue(is_valid)
		self.assertIsNone(error)

		# Invalid function name
		invalid_response = {
			"function_call": {
				"name": "invalid_function",
				"arguments": '{"order_id": "ORD-123"}'
			}
		}

		is_valid, error = validate_function_call_response(invalid_response, ["get_order_status"])
		self.assertFalse(is_valid)
		self.assertIsNotNone(error)

	def test_temperature_parameter(self):
		"""Test temperature parameter effect."""
		messages = [{"role": "user", "content": "Tell me a random number between 1 and 10"}]

		# Temperature 0 should be more deterministic
		response1 = generate_completion(messages, max_tokens=20, temperature=0)
		response2 = generate_completion(messages, max_tokens=20, temperature=0)

		# Both responses should be similar or identical at temperature 0
		self.assertIsNotNone(response1)
		self.assertIsNotNone(response2)

	def test_max_tokens_parameter(self):
		"""Test max tokens limit."""
		messages = [{"role": "user", "content": "Write a long essay about AI"}]

		response = generate_completion(messages, max_tokens=10, temperature=0)

		self.assertIsNotNone(response)
		# Response should be truncated due to low max_tokens
		self.assertLess(len(response.split()), 50)  # Rough check

	def test_error_handling_invalid_api_key(self):
		"""Test error handling for invalid API key."""
		# This test would need to temporarily modify settings
		# Placeholder for implementation
		pass

	def test_error_handling_timeout(self):
		"""Test error handling for API timeout."""
		# This test would need to simulate timeout
		# Placeholder for implementation
		pass

	def tearDown(self):
		"""Clean up after tests."""
		pass


if __name__ == "__main__":
	unittest.main()
