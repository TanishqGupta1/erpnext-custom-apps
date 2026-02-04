#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Integration tests for voice (VAPI) workflow.
"""

import unittest
import frappe
import json
from ai_comms_hub.webhooks.voice import handle_vapi_webhook


class TestVoiceFlow(unittest.TestCase):
	"""Test end-to-end voice conversation flow."""

	def setUp(self):
		"""Set up test environment."""
		# Create test customer
		self.test_customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": "Voice Test Customer",
			"customer_type": "Individual",
			"mobile_no": "+1234567890"
		})
		self.test_customer.insert(ignore_permissions=True)
		frappe.db.commit()

	def test_call_started_event(self):
		"""Test call.started webhook event."""
		payload = {
			"event_type": "call.started",
			"call_id": "test-call-001",
			"data": {
				"call": {
					"id": "test-call-001",
					"customer": {"number": "+1234567890"},
					"assistantId": "assistant-test"
				},
				"timestamp": "2025-01-24T12:00:00Z"
			}
		}

		response = handle_vapi_webhook(
			event_type=payload["event_type"],
			call_id=payload["call_id"],
			data=json.dumps(payload["data"])
		)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Verify Communication Hub was created
		hubs = frappe.get_all(
			"Communication Hub",
			filters={"vapi_call_id": "test-call-001"},
			limit=1
		)
		self.assertGreater(len(hubs), 0)

		# Cleanup
		if hubs:
			frappe.delete_doc("Communication Hub", hubs[0].name, ignore_permissions=True)

	def test_speech_update_event(self):
		"""Test speech-update webhook event."""
		# First create a call
		hub = frappe.get_doc({
			"doctype": "Communication Hub",
			"channel": "Voice",
			"vapi_call_id": "test-call-002",
			"sender_id": "+1234567890",
			"customer": self.test_customer.name,
			"status": "Open"
		})
		hub.insert(ignore_permissions=True)
		frappe.db.commit()

		# Send speech update
		payload = {
			"event_type": "speech-update",
			"call_id": "test-call-002",
			"data": {
				"transcript": "I need help with my order",
				"role": "user"
			}
		}

		response = handle_vapi_webhook(
			event_type=payload["event_type"],
			call_id=payload["call_id"],
			data=json.dumps(payload["data"])
		)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Verify message was created
		messages = frappe.get_all(
			"Communication Message",
			filters={"parent": hub.name},
			limit=1
		)
		self.assertGreater(len(messages), 0)

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_function_call_event(self):
		"""Test function-call webhook event."""
		# Create a call
		hub = frappe.get_doc({
			"doctype": "Communication Hub",
			"channel": "Voice",
			"vapi_call_id": "test-call-003",
			"sender_id": "+1234567890",
			"customer": self.test_customer.name,
			"status": "Open"
		})
		hub.insert(ignore_permissions=True)
		frappe.db.commit()

		# Send function call request
		payload = {
			"event_type": "function-call",
			"call_id": "test-call-003",
			"data": {
				"functionCall": {
					"name": "get_order_status",
					"parameters": {
						"order_id": "TEST-ORDER-001"
					}
				}
			}
		}

		response = handle_vapi_webhook(
			event_type=payload["event_type"],
			call_id=payload["call_id"],
			data=json.dumps(payload["data"])
		)

		self.assertIsNotNone(response)
		# Response should contain function result
		self.assertIn("result", response)

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_end_of_call_report(self):
		"""Test end-of-call-report webhook event."""
		# Create a call
		hub = frappe.get_doc({
			"doctype": "Communication Hub",
			"channel": "Voice",
			"vapi_call_id": "test-call-004",
			"sender_id": "+1234567890",
			"customer": self.test_customer.name,
			"status": "In Progress"
		})
		hub.insert(ignore_permissions=True)
		frappe.db.commit()

		# Send end of call report
		payload = {
			"event_type": "end-of-call-report",
			"call_id": "test-call-004",
			"data": {
				"call": {
					"id": "test-call-004",
					"duration": 120,
					"cost": 0.50
				},
				"transcript": [
					{"role": "user", "text": "Hello"},
					{"role": "assistant", "text": "Hi! How can I help you?"}
				],
				"endedReason": "customer-ended-call"
			}
		}

		response = handle_vapi_webhook(
			event_type=payload["event_type"],
			call_id=payload["call_id"],
			data=json.dumps(payload["data"])
		)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Verify hub was updated
		hub.reload()
		self.assertEqual(hub.status, "Resolved")

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_complete_call_flow(self):
		"""Test complete end-to-end call flow."""
		call_id = "test-call-complete-001"

		# 1. Call started
		payload1 = {
			"event_type": "call.started",
			"call_id": call_id,
			"data": {"call": {"id": call_id, "customer": {"number": "+1234567890"}}}
		}
		handle_vapi_webhook(payload1["event_type"], payload1["call_id"], json.dumps(payload1["data"]))

		# 2. Customer speaks
		payload2 = {
			"event_type": "speech-update",
			"call_id": call_id,
			"data": {"transcript": "What's my order status?", "role": "user"}
		}
		handle_vapi_webhook(payload2["event_type"], payload2["call_id"], json.dumps(payload2["data"]))

		# 3. AI requests function call
		payload3 = {
			"event_type": "function-call",
			"call_id": call_id,
			"data": {"functionCall": {"name": "get_order_status", "parameters": {"order_id": "ORD-123"}}}
		}
		handle_vapi_webhook(payload3["event_type"], payload3["call_id"], json.dumps(payload3["data"]))

		# 4. Call ends
		payload4 = {
			"event_type": "end-of-call-report",
			"call_id": call_id,
			"data": {"endedReason": "customer-ended-call"}
		}
		handle_vapi_webhook(payload4["event_type"], payload4["call_id"], json.dumps(payload4["data"]))

		# Verify conversation exists and is resolved
		hubs = frappe.get_all(
			"Communication Hub",
			filters={"vapi_call_id": call_id},
			limit=1
		)
		self.assertGreater(len(hubs), 0)

		hub = frappe.get_doc("Communication Hub", hubs[0].name)
		self.assertEqual(hub.status, "Resolved")

		# Verify messages were created
		messages = frappe.get_all(
			"Communication Message",
			filters={"parent": hub.name}
		)
		self.assertGreater(len(messages), 0)

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def tearDown(self):
		"""Clean up after tests."""
		if frappe.db.exists("Customer", self.test_customer.name):
			frappe.delete_doc("Customer", self.test_customer.name, ignore_permissions=True)
			frappe.db.commit()


if __name__ == "__main__":
	unittest.main()
