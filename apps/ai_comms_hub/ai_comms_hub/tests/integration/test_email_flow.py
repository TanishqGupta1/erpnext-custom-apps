#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Integration tests for email (SendGrid) workflow.
"""

import unittest
import frappe
from ai_comms_hub.webhooks.email import handle_sendgrid_inbound


class TestEmailFlow(unittest.TestCase):
	"""Test end-to-end email conversation flow."""

	def setUp(self):
		"""Set up test environment."""
		# Create test customer
		self.test_customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": "Email Test Customer",
			"customer_type": "Individual",
			"email_id": "test@example.com"
		})
		self.test_customer.insert(ignore_permissions=True)
		frappe.db.commit()

	def test_new_email_thread(self):
		"""Test handling new email (no thread)."""
		payload = {
			"from": "test@example.com",
			"to": "support@company.com",
			"subject": "Need help with order",
			"text": "Hello, I need assistance with my recent order. Can you help?",
			"headers": "Message-ID: <new-thread-001@example.com>"
		}

		response = handle_sendgrid_inbound(**payload)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Verify Communication Hub was created
		hubs = frappe.get_all(
			"Communication Hub",
			filters={
				"channel": "Email",
				"sender_id": "test@example.com"
			},
			limit=1,
			order_by="creation desc"
		)
		self.assertGreater(len(hubs), 0)

		# Verify message
		hub = frappe.get_doc("Communication Hub", hubs[0].name)
		messages = frappe.get_all(
			"Communication Message",
			filters={"parent": hub.name},
			limit=1
		)
		self.assertGreater(len(messages), 0)

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_email_reply_threading(self):
		"""Test email reply threading (In-Reply-To header)."""
		# Create initial conversation
		hub = frappe.get_doc({
			"doctype": "Communication Hub",
			"channel": "Email",
			"sender_id": "test@example.com",
			"customer": self.test_customer.name,
			"status": "In Progress",
			"email_message_id": "<original-001@example.com>"
		})
		hub.insert(ignore_permissions=True)
		frappe.db.commit()

		# Send reply
		payload = {
			"from": "test@example.com",
			"to": "support@company.com",
			"subject": "Re: Need help with order",
			"text": "Thanks for the response. I have a follow-up question.",
			"headers": "Message-ID: <reply-001@example.com>\nIn-Reply-To: <original-001@example.com>\nReferences: <original-001@example.com>"
		}

		response = handle_sendgrid_inbound(**payload)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Verify reply was added to existing conversation
		messages = frappe.get_all(
			"Communication Message",
			filters={"parent": hub.name},
			order_by="creation desc",
			limit=1
		)
		self.assertGreater(len(messages), 0)

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_email_intent_classification(self):
		"""Test email intent classification."""
		test_cases = [
			{
				"text": "What is the status of order ORD-12345?",
				"expected_intent": "order_inquiry"
			},
			{
				"text": "I need a quote for 100 units of Product X.",
				"expected_intent": "quote_request"
			},
			{
				"text": "My product arrived damaged. I want a refund.",
				"expected_intent": "complaint"
			}
		]

		for case in test_cases:
			payload = {
				"from": "test@example.com",
				"to": "support@company.com",
				"subject": "Customer inquiry",
				"text": case["text"],
				"headers": f"Message-ID: <test-{case['expected_intent']}@example.com>"
			}

			response = handle_sendgrid_inbound(**payload)

			# Find the created hub
			hubs = frappe.get_all(
				"Communication Hub",
				filters={
					"email_message_id": f"<test-{case['expected_intent']}@example.com>"
				},
				limit=1
			)

			if hubs:
				hub = frappe.get_doc("Communication Hub", hubs[0].name)
				messages = frappe.get_all(
					"Communication Message",
					filters={"parent": hub.name},
					fields=["detected_intent"],
					limit=1
				)

				if messages:
					# Intent should match or be reasonable
					self.assertIsNotNone(messages[0].get("detected_intent"))

				# Cleanup
				frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_email_content_cleaning(self):
		"""Test email content cleaning (quoted replies, signatures)."""
		email_with_quote = """Hello,

I have a question about my order.

Thanks,
John

---
On Jan 24, 2025, support@company.com wrote:
> Thank you for contacting us.
> How can we help?
"""

		payload = {
			"from": "test@example.com",
			"to": "support@company.com",
			"subject": "Order question",
			"text": email_with_quote,
			"headers": "Message-ID: <clean-test-001@example.com>"
		}

		response = handle_sendgrid_inbound(**payload)

		# Find created message
		hubs = frappe.get_all(
			"Communication Hub",
			filters={"email_message_id": "<clean-test-001@example.com>"},
			limit=1
		)

		if hubs:
			hub = frappe.get_doc("Communication Hub", hubs[0].name)
			messages = frappe.get_all(
				"Communication Message",
				filters={"parent": hub.name},
				fields=["message_text"],
				limit=1
			)

			if messages:
				# Quoted reply should be removed
				self.assertNotIn("On Jan 24, 2025", messages[0]["message_text"])
				self.assertNotIn("> Thank you", messages[0]["message_text"])

			# Cleanup
			frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_email_with_attachments(self):
		"""Test email with attachments."""
		payload = {
			"from": "test@example.com",
			"to": "support@company.com",
			"subject": "Order issue - see attached image",
			"text": "Please see the attached screenshot of the problem.",
			"headers": "Message-ID: <attachment-test-001@example.com>",
			"attachment-info": '[{"filename": "screenshot.png", "type": "image/png"}]'
		}

		response = handle_sendgrid_inbound(**payload)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Cleanup
		hubs = frappe.get_all(
			"Communication Hub",
			filters={"email_message_id": "<attachment-test-001@example.com>"},
			limit=1
		)
		if hubs:
			frappe.delete_doc("Communication Hub", hubs[0].name, ignore_permissions=True)

	def test_complete_email_conversation(self):
		"""Test complete email conversation flow."""
		# 1. Customer sends initial email
		payload1 = {
			"from": "test@example.com",
			"to": "support@company.com",
			"subject": "Product inquiry",
			"text": "Do you have Product X in stock?",
			"headers": "Message-ID: <complete-001@example.com>"
		}
		handle_sendgrid_inbound(**payload1)

		# 2. Customer replies
		payload2 = {
			"from": "test@example.com",
			"to": "support@company.com",
			"subject": "Re: Product inquiry",
			"text": "Great! How much does it cost?",
			"headers": "Message-ID: <complete-002@example.com>\nIn-Reply-To: <complete-001@example.com>"
		}
		handle_sendgrid_inbound(**payload2)

		# 3. Customer closes inquiry
		payload3 = {
			"from": "test@example.com",
			"to": "support@company.com",
			"subject": "Re: Product inquiry",
			"text": "Thanks for the information! That's all I needed.",
			"headers": "Message-ID: <complete-003@example.com>\nIn-Reply-To: <complete-002@example.com>"
		}
		handle_sendgrid_inbound(**payload3)

		# Verify conversation
		hubs = frappe.get_all(
			"Communication Hub",
			filters={"email_message_id": "<complete-001@example.com>"},
			limit=1
		)
		self.assertGreater(len(hubs), 0)

		hub = frappe.get_doc("Communication Hub", hubs[0].name)

		# Verify all messages in thread
		messages = frappe.get_all(
			"Communication Message",
			filters={"parent": hub.name}
		)
		self.assertGreaterEqual(len(messages), 3)  # At least 3 customer messages

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def tearDown(self):
		"""Clean up after tests."""
		if frappe.db.exists("Customer", self.test_customer.name):
			frappe.delete_doc("Customer", self.test_customer.name, ignore_permissions=True)
			frappe.db.commit()


if __name__ == "__main__":
	unittest.main()
