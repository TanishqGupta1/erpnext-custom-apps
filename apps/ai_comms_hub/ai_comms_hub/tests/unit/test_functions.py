#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Unit tests for AI function calling module.
"""

import unittest
import frappe
from ai_comms_hub.api.functions import (
	get_order_status,
	create_quote,
	check_product_availability,
	get_customer_info,
	update_customer_info,
	search_knowledge_base,
	escalate_to_human
)


class TestFunctions(unittest.TestCase):
	"""Test AI function calling."""

	def setUp(self):
		"""Set up test environment."""
		# Create test customer
		self.test_customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": "Test Customer for Functions",
			"customer_type": "Individual"
		})
		self.test_customer.insert(ignore_permissions=True)
		frappe.db.commit()

	def test_get_order_status_existing_order(self):
		"""Test getting status of existing order."""
		# Create test Sales Order
		order = frappe.get_doc({
			"doctype": "Sales Order",
			"customer": self.test_customer.name,
			"transaction_date": frappe.utils.today(),
			"delivery_date": frappe.utils.add_days(frappe.utils.today(), 7),
			"items": [{
				"item_code": "Test Item",
				"qty": 1,
				"rate": 100
			}]
		})
		order.insert(ignore_permissions=True)
		frappe.db.commit()

		# Test function
		result = get_order_status(order.name)

		self.assertIsNotNone(result)
		self.assertNotIn("error", result)
		self.assertIn("order_id", result)
		self.assertEqual(result["order_id"], order.name)
		self.assertIn("status", result)

		# Cleanup
		frappe.delete_doc("Sales Order", order.name, ignore_permissions=True)

	def test_get_order_status_nonexistent_order(self):
		"""Test getting status of non-existent order."""
		result = get_order_status("INVALID-ORDER-123")

		self.assertIsNotNone(result)
		self.assertIn("error", result)

	def test_create_quote_valid_data(self):
		"""Test creating quote with valid data."""
		quote_data = {
			"customer_name": self.test_customer.name,
			"items": [
				{
					"item_name": "Test Product",
					"quantity": 5,
					"unit_price": 100.00
				}
			]
		}

		result = create_quote(quote_data)

		self.assertIsNotNone(result)
		self.assertNotIn("error", result)
		self.assertIn("quote_id", result)

		# Cleanup
		if "quote_id" in result:
			frappe.delete_doc("Quotation", result["quote_id"], ignore_permissions=True)

	def test_create_quote_missing_customer(self):
		"""Test creating quote without customer name."""
		quote_data = {
			"items": [
				{
					"item_name": "Test Product",
					"quantity": 5
				}
			]
		}

		result = create_quote(quote_data)

		self.assertIsNotNone(result)
		self.assertIn("error", result)

	def test_create_quote_missing_items(self):
		"""Test creating quote without items."""
		quote_data = {
			"customer_name": self.test_customer.name
		}

		result = create_quote(quote_data)

		self.assertIsNotNone(result)
		self.assertIn("error", result)

	def test_check_product_availability_by_name(self):
		"""Test checking product availability by name."""
		# Create test item
		item = frappe.get_doc({
			"doctype": "Item",
			"item_code": "TEST-PRODUCT-001",
			"item_name": "Test Product for Availability",
			"item_group": "Products",
			"stock_uom": "Nos"
		})
		item.insert(ignore_permissions=True)
		frappe.db.commit()

		result = check_product_availability("Test Product for Availability")

		self.assertIsNotNone(result)
		self.assertNotIn("error", result)
		self.assertIn("available", result)

		# Cleanup
		frappe.delete_doc("Item", item.name, ignore_permissions=True)

	def test_check_product_availability_nonexistent(self):
		"""Test checking non-existent product."""
		result = check_product_availability("Non-Existent Product XYZ")

		self.assertIsNotNone(result)
		self.assertIn("error", result)

	def test_get_customer_info_existing(self):
		"""Test getting info for existing customer."""
		result = get_customer_info(self.test_customer.name)

		self.assertIsNotNone(result)
		self.assertNotIn("error", result)
		self.assertIn("customer_name", result)
		self.assertEqual(result["customer_name"], self.test_customer.customer_name)

	def test_get_customer_info_nonexistent(self):
		"""Test getting info for non-existent customer."""
		result = get_customer_info("Invalid Customer XYZ")

		self.assertIsNotNone(result)
		self.assertIn("error", result)

	def test_update_customer_info_valid(self):
		"""Test updating customer information."""
		updates = {
			"mobile_no": "+1234567890",
			"customer_group": "Commercial"
		}

		result = update_customer_info(self.test_customer.name, updates)

		self.assertIsNotNone(result)
		self.assertNotIn("error", result)
		self.assertTrue(result.get("success", False))

		# Verify update
		customer = frappe.get_doc("Customer", self.test_customer.name)
		self.assertEqual(customer.mobile_no, "+1234567890")

	def test_update_customer_info_invalid_field(self):
		"""Test updating customer with invalid field."""
		updates = {
			"invalid_field_xyz": "test value"
		}

		result = update_customer_info(self.test_customer.name, updates)

		# Should either ignore invalid field or return error
		self.assertIsNotNone(result)

	def test_search_knowledge_base(self):
		"""Test knowledge base search function."""
		query = "how to check order status"

		result = search_knowledge_base(query, top_k=3)

		self.assertIsNotNone(result)
		self.assertIsInstance(result, list)

		# Should return list of articles
		if len(result) > 0:
			article = result[0]
			self.assertIn("title", article)
			self.assertIn("content", article)

	def test_escalate_to_human_with_reason(self):
		"""Test escalating conversation to human with reason."""
		# Create test communication hub
		hub = frappe.get_doc({
			"doctype": "Communication Hub",
			"channel": "Chat",
			"customer": self.test_customer.name,
			"status": "Open",
			"ai_mode": "Autonomous"
		})
		hub.insert(ignore_permissions=True)
		frappe.db.commit()

		result = escalate_to_human(
			hub.name,
			reason="Low Confidence",
			notes="AI confidence below threshold"
		)

		self.assertIsNotNone(result)
		self.assertNotIn("error", result)
		self.assertTrue(result.get("escalated", False))

		# Verify escalation
		hub.reload()
		self.assertEqual(hub.status, "Escalated")
		self.assertEqual(hub.escalation_reason, "Low Confidence")

		# Cleanup
		frappe.delete_doc("Communication Hub", hub.name, ignore_permissions=True)

	def test_escalate_to_human_invalid_hub(self):
		"""Test escalating non-existent conversation."""
		result = escalate_to_human("INVALID-HUB-123", reason="Test")

		self.assertIsNotNone(result)
		self.assertIn("error", result)

	def tearDown(self):
		"""Clean up after tests."""
		# Delete test customer
		if frappe.db.exists("Customer", self.test_customer.name):
			frappe.delete_doc("Customer", self.test_customer.name, ignore_permissions=True)
			frappe.db.commit()


if __name__ == "__main__":
	unittest.main()
