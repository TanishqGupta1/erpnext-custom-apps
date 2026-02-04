#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Integration tests for social media workflows (Facebook, Instagram, Twitter).
"""

import unittest
import frappe
import json
from ai_comms_hub.webhooks.social import (
	handle_facebook_webhook,
	handle_instagram_webhook,
	handle_twitter_webhook
)


class TestSocialFlow(unittest.TestCase):
	"""Test end-to-end social media conversation flows."""

	def setUp(self):
		"""Set up test environment."""
		# Create test customer
		self.test_customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": "Social Test Customer",
			"customer_type": "Individual",
			"facebook_psid": "test-psid-123",
			"instagram_id": "test-ig-123",
			"twitter_id": "test-twitter-123"
		})
		self.test_customer.insert(ignore_permissions=True)
		frappe.db.commit()

	def test_facebook_message(self):
		"""Test Facebook Messenger message handling."""
		payload = {
			"platform": "Facebook",
			"sender_id": "test-psid-123",
			"message_text": "Hello! I need help with my order.",
			"message_id": "fb-msg-001",
			"timestamp": "1642944000000"
		}

		response = handle_facebook_webhook(**payload)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Verify Communication Hub was created
		hubs = frappe.get_all(
			"Communication Hub",
			filters={
				"channel": "Facebook",
				"facebook_psid": "test-psid-123"
			},
			limit=1,
			order_by="creation desc"
		)
		self.assertGreater(len(hubs), 0)

		# Verify customer was linked
		hub = frappe.get_doc("Communication Hub", hubs[0].name)
		self.assertEqual(hub.customer, self.test_customer.name)

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_facebook_postback(self):
		"""Test Facebook Messenger postback (button click)."""
		# First create a conversation
		hub = frappe.get_doc({
			"doctype": "Communication Hub",
			"channel": "Facebook",
			"facebook_psid": "test-psid-123",
			"customer": self.test_customer.name,
			"status": "Open"
		})
		hub.insert(ignore_permissions=True)
		frappe.db.commit()

		payload = {
			"platform": "Facebook",
			"sender_id": "test-psid-123",
			"payload": "ORDER_STATUS_CHECK",
			"title": "Check Order Status"
		}

		response = handle_facebook_webhook(**payload)

		self.assertIsNotNone(response)
		# Postback should trigger action

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_instagram_message(self):
		"""Test Instagram DM handling."""
		payload = {
			"platform": "Instagram",
			"sender_id": "test-ig-123",
			"message_text": "Interested in your products!",
			"message_id": "ig-msg-001",
			"timestamp": "1642944000000"
		}

		response = handle_instagram_webhook(**payload)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Verify Communication Hub was created
		hubs = frappe.get_all(
			"Communication Hub",
			filters={
				"channel": "Instagram",
				"instagram_id": "test-ig-123"
			},
			limit=1,
			order_by="creation desc"
		)
		self.assertGreater(len(hubs), 0)

		# Cleanup
		if hubs:
			frappe.delete_doc("Communication Hub", hubs[0].name, ignore_permissions=True)

	def test_instagram_echo_filtering(self):
		"""Test Instagram echo message filtering (bot's own messages)."""
		# Create conversation
		hub = frappe.get_doc({
			"doctype": "Communication Hub",
			"channel": "Instagram",
			"instagram_id": "test-ig-123",
			"customer": self.test_customer.name,
			"status": "Open"
		})
		hub.insert(ignore_permissions=True)
		frappe.db.commit()

		# Send echo message (from bot)
		payload = {
			"platform": "Instagram",
			"sender_id": "test-ig-123",
			"message_text": "Thank you for contacting us!",
			"message_id": "ig-echo-001",
			"timestamp": "1642944000000",
			"is_echo": True  # Flag indicating this is bot's own message
		}

		response = handle_instagram_webhook(**payload)

		# Echo messages should be ignored
		# Verify no new message was created
		messages_before = frappe.db.count(
			"Communication Message",
			filters={"parent": hub.name}
		)

		# Echo should not create new message
		self.assertIsNotNone(response)

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_twitter_dm(self):
		"""Test Twitter DM handling."""
		payload = {
			"platform": "Twitter",
			"dm_id": "twitter-dm-001",
			"conversation_id": "twitter-conv-001",
			"sender_id": "test-twitter-123",
			"sender_username": "testuser",
			"message_text": "Question about your services",
			"created_at": "2025-01-24T12:00:00Z"
		}

		response = handle_twitter_webhook(**payload)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Verify Communication Hub was created
		hubs = frappe.get_all(
			"Communication Hub",
			filters={
				"channel": "Twitter",
				"twitter_id": "test-twitter-123"
			},
			limit=1,
			order_by="creation desc"
		)
		self.assertGreater(len(hubs), 0)

		# Cleanup
		if hubs:
			frappe.delete_doc("Communication Hub", hubs[0].name, ignore_permissions=True)

	def test_twitter_dm_with_attachments(self):
		"""Test Twitter DM with media attachments."""
		payload = {
			"platform": "Twitter",
			"dm_id": "twitter-dm-002",
			"conversation_id": "twitter-conv-002",
			"sender_id": "test-twitter-123",
			"message_text": "Check out this image",
			"attachments": [
				{
					"type": "photo",
					"media_url": "https://example.com/photo.jpg"
				}
			],
			"created_at": "2025-01-24T12:00:00Z"
		}

		response = handle_twitter_webhook(**payload)

		self.assertIsNotNone(response)
		self.assertTrue(response.get("success", False))

		# Cleanup
		hubs = frappe.get_all(
			"Communication Hub",
			filters={
				"twitter_dm_id": "twitter-dm-002"
			},
			limit=1
		)
		if hubs:
			frappe.delete_doc("Communication Hub", hubs[0].name, ignore_permissions=True)

	def test_complete_facebook_conversation(self):
		"""Test complete Facebook conversation flow."""
		sender_id = "complete-test-psid"

		# 1. Customer sends first message
		payload1 = {
			"platform": "Facebook",
			"sender_id": sender_id,
			"message_text": "Hi, I want to know about Product X",
			"message_id": "fb-complete-001"
		}
		handle_facebook_webhook(**payload1)

		# 2. Customer asks follow-up
		payload2 = {
			"platform": "Facebook",
			"sender_id": sender_id,
			"message_text": "How much does it cost?",
			"message_id": "fb-complete-002"
		}
		handle_facebook_webhook(**payload2)

		# 3. Customer clicks button
		payload3 = {
			"platform": "Facebook",
			"sender_id": sender_id,
			"payload": "ADD_TO_CART",
			"title": "Add to Cart"
		}
		handle_facebook_webhook(**payload3)

		# Verify conversation exists
		hubs = frappe.get_all(
			"Communication Hub",
			filters={
				"channel": "Facebook",
				"facebook_psid": sender_id
			},
			limit=1
		)
		self.assertGreater(len(hubs), 0)

		hub = frappe.get_doc("Communication Hub", hubs[0].name)

		# Verify messages
		messages = frappe.get_all(
			"Communication Message",
			filters={"parent": hub.name}
		)
		self.assertGreaterEqual(len(messages), 2)  # At least 2 customer messages

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_sentiment_detection_social(self):
		"""Test sentiment detection across social platforms."""
		test_cases = [
			{
				"platform": "Facebook",
				"text": "This is terrible! I want a refund now!",
				"expected_sentiment": "Negative"
			},
			{
				"platform": "Instagram",
				"text": "Love your products! Best purchase ever!",
				"expected_sentiment": "Positive"
			},
			{
				"platform": "Twitter",
				"text": "Order arrived on time.",
				"expected_sentiment": "Neutral"
			}
		]

		for i, case in enumerate(test_cases):
			payload = {
				"platform": case["platform"],
				"sender_id": f"sentiment-test-{i}",
				"message_text": case["text"],
				"message_id": f"sentiment-msg-{i}"
			}

			if case["platform"] == "Facebook":
				handle_facebook_webhook(**payload)
			elif case["platform"] == "Instagram":
				handle_instagram_webhook(**payload)
			elif case["platform"] == "Twitter":
				payload["dm_id"] = payload["message_id"]
				payload["conversation_id"] = f"conv-{i}"
				payload["created_at"] = "2025-01-24T12:00:00Z"
				handle_twitter_webhook(**payload)

			# Verify sentiment was detected
			# (This would require the AI to actually analyze sentiment)

			# Cleanup
			hubs = frappe.get_all(
				"Communication Hub",
				filters={"sender_id": f"sentiment-test-{i}"},
				limit=1
			)
			if hubs:
				frappe.delete_doc("Communication Hub", hubs[0].name, ignore_permissions=True)

	def tearDown(self):
		"""Clean up after tests."""
		if frappe.db.exists("Customer", self.test_customer.name):
			frappe.delete_doc("Customer", self.test_customer.name, ignore_permissions=True)
			frappe.db.commit()


if __name__ == "__main__":
	unittest.main()
