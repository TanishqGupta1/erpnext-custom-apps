#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Data Migration Script

This script helps migrate data for AI Communications Hub, including:
- Migrating conversations from other systems
- Backfilling customer data
- Syncing historical knowledge base

Usage:
    bench --site <site-name> execute ai_comms_hub.scripts.migrate_data.migrate_<function>
"""

import frappe
from frappe import _
from datetime import datetime
import json


def migrate_chatwoot_conversations():
	"""
	Migrate existing Chatwoot conversations to Communication Hub.

	This reads historical Chatwoot data and creates corresponding
	Communication Hub records.
	"""
	print("=" * 60)
	print("Migrating Chatwoot Conversations")
	print("=" * 60)

	# Get Chatwoot settings
	settings = frappe.get_single("AI Communications Hub Settings")

	if not settings.chatwoot_account_id or not settings.chatwoot_api_key:
		print("❌ Chatwoot credentials not configured in settings")
		return

	try:
		# Fetch conversations from Chatwoot API
		import requests

		url = f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/conversations"
		headers = {"api_access_token": settings.chatwoot_api_key}

		response = requests.get(url, headers=headers, timeout=30)
		response.raise_for_status()

		conversations = response.json().get("data", {}).get("payload", [])

		migrated = 0
		skipped = 0

		for conv in conversations:
			# Check if already migrated
			if frappe.db.exists("Communication Hub", {
				"channel": "Chat",
				"chatwoot_conversation_id": conv.get("id")
			}):
				skipped += 1
				continue

			# Create Communication Hub record
			hub = frappe.get_doc({
				"doctype": "Communication Hub",
				"channel": "Chat",
				"status": map_chatwoot_status(conv.get("status")),
				"customer": get_or_create_customer(conv.get("meta", {}).get("sender")),
				"chatwoot_conversation_id": conv.get("id"),
				"created_at": conv.get("created_at"),
				"updated_at": conv.get("updated_at")
			})

			hub.insert(ignore_permissions=True)
			migrated += 1

			# Migrate messages for this conversation
			migrate_chatwoot_messages(hub.name, conv.get("id"), settings)

		print(f"\n✅ Migration complete: {migrated} conversations migrated, {skipped} skipped")

	except Exception as e:
		print(f"❌ Migration failed: {str(e)}")
		frappe.log_error(f"Chatwoot migration failed: {str(e)}", "Data Migration Error")


def migrate_chatwoot_messages(hub_id, chatwoot_conv_id, settings):
	"""
	Migrate messages for a specific conversation.

	Args:
		hub_id (str): Communication Hub ID
		chatwoot_conv_id (int): Chatwoot conversation ID
		settings: Settings document
	"""
	import requests

	url = f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/conversations/{chatwoot_conv_id}/messages"
	headers = {"api_access_token": settings.chatwoot_api_key}

	try:
		response = requests.get(url, headers=headers, timeout=30)
		response.raise_for_status()

		messages = response.json().get("payload", [])

		for msg in messages:
			message = frappe.get_doc({
				"doctype": "Communication Message",
				"communication_hub": hub_id,
				"sender_type": "Customer" if msg.get("message_type") == 0 else "Agent",
				"sender_name": msg.get("sender", {}).get("name", "Unknown"),
				"content": msg.get("content", ""),
				"timestamp": msg.get("created_at"),
				"delivery_status": "Delivered",
				"platform_message_id": str(msg.get("id"))
			})

			message.insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Failed to migrate messages for conversation {chatwoot_conv_id}: {str(e)}")


def backfill_customer_social_ids():
	"""
	Backfill social media IDs for existing customers.

	This scans Communication Hub records and updates Customer records
	with their social media IDs (Facebook PSID, Instagram ID, etc.)
	"""
	print("=" * 60)
	print("Backfilling Customer Social IDs")
	print("=" * 60)

	# Get all unique customer-platform combinations
	hubs = frappe.db.sql("""
		SELECT DISTINCT
			customer,
			channel,
			facebook_psid,
			instagram_id,
			twitter_sender_id,
			linkedin_sender_id
		FROM `tabCommunication Hub`
		WHERE customer IS NOT NULL
	""", as_dict=True)

	updated = 0

	for hub in hubs:
		customer = frappe.get_doc("Customer", hub.customer)
		updated_fields = False

		# Update Facebook PSID
		if hub.channel == "Facebook" and hub.facebook_psid and not customer.facebook_psid:
			customer.facebook_psid = hub.facebook_psid
			updated_fields = True

		# Update Instagram ID
		if hub.channel == "Instagram" and hub.instagram_id and not customer.instagram_id:
			customer.instagram_id = hub.instagram_id
			updated_fields = True

		# Update Twitter ID
		if hub.channel == "Twitter" and hub.twitter_sender_id and not customer.twitter_id:
			customer.twitter_id = hub.twitter_sender_id
			updated_fields = True

		# Update LinkedIn Profile
		if hub.channel == "LinkedIn" and hub.linkedin_sender_id and not customer.linkedin_profile:
			customer.linkedin_profile = hub.linkedin_sender_id
			updated_fields = True

		if updated_fields:
			customer.save(ignore_permissions=True)
			updated += 1

	print(f"\n✅ Backfill complete: {updated} customers updated")


def sync_historical_knowledge():
	"""
	Sync historical ERPNext data to knowledge base.

	This includes:
	- Products/Items
	- FAQs
	- Quotations
	- Sales Orders
	"""
	print("=" * 60)
	print("Syncing Historical Knowledge Base")
	print("=" * 60)

	try:
		from ai_comms_hub.api.rag import (
			sync_erpnext_knowledge,
			insert_document
		)

		# Sync ERPNext knowledge
		count = sync_erpnext_knowledge()
		print(f"✅ Synced {count} ERPNext documents")

		# Sync custom knowledge (if any)
		# Add your custom knowledge sync here

		print("\n✅ Knowledge base sync complete")

	except Exception as e:
		print(f"❌ Sync failed: {str(e)}")
		frappe.log_error(f"Knowledge sync failed: {str(e)}", "Data Migration Error")


def recalculate_customer_metrics():
	"""
	Recalculate AI communication metrics for all customers.

	Updates:
	- Total AI conversations
	- AI resolution rate
	- Last AI interaction
	- Overall sentiment
	"""
	print("=" * 60)
	print("Recalculating Customer Metrics")
	print("=" * 60)

	customers = frappe.get_all("Customer", fields=["name"])

	updated = 0

	for customer_row in customers:
		customer = frappe.get_doc("Customer", customer_row.name)

		# Count total AI conversations
		total_conversations = frappe.db.count("Communication Hub", {
			"customer": customer.name,
			"ai_mode": ["in", ["Autonomous", "HITL"]]
		})

		# Count resolved conversations (without escalation)
		resolved_conversations = frappe.db.count("Communication Hub", {
			"customer": customer.name,
			"ai_mode": "Autonomous",
			"status": ["in", ["Resolved", "Closed"]],
			"escalated_to_agent": 0
		})

		# Calculate resolution rate
		resolution_rate = (resolved_conversations / total_conversations * 100) if total_conversations > 0 else 0

		# Get last interaction
		last_hub = frappe.get_all("Communication Hub", {
			"customer": customer.name
		}, order_by="updated_at desc", limit=1)

		last_interaction = last_hub[0].updated_at if last_hub else None

		# Calculate overall sentiment
		sentiment_counts = frappe.db.sql("""
			SELECT sentiment, COUNT(*) as count
			FROM `tabCommunication Hub`
			WHERE customer = %s AND sentiment IS NOT NULL
			GROUP BY sentiment
		""", customer.name, as_dict=True)

		overall_sentiment = calculate_overall_sentiment(sentiment_counts)

		# Update customer
		customer.total_ai_conversations = total_conversations
		customer.ai_resolution_rate = resolution_rate
		customer.last_ai_interaction = last_interaction
		customer.customer_sentiment = overall_sentiment

		customer.save(ignore_permissions=True)
		updated += 1

	print(f"\n✅ Metrics recalculated for {updated} customers")


# Helper functions

def map_chatwoot_status(chatwoot_status):
	"""Map Chatwoot status to Communication Hub status."""
	mapping = {
		"open": "Open",
		"pending": "In Progress",
		"resolved": "Resolved",
		"closed": "Closed"
	}
	return mapping.get(chatwoot_status, "Open")


def get_or_create_customer(sender_data):
	"""
	Get or create customer from Chatwoot sender data.

	Args:
		sender_data (dict): Chatwoot sender information

	Returns:
		str: Customer name
	"""
	email = sender_data.get("email")
	phone = sender_data.get("phone_number")
	name = sender_data.get("name", "Unknown")

	# Try to find existing customer by email
	if email:
		customer = frappe.db.get_value("Customer", {"email_id": email})
		if customer:
			return customer

	# Try to find by phone
	if phone:
		customer = frappe.db.get_value("Customer", {"mobile_no": phone})
		if customer:
			return customer

	# Create new customer
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": name,
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "All Territories",
		"email_id": email,
		"mobile_no": phone
	})

	customer.insert(ignore_permissions=True)
	return customer.name


def calculate_overall_sentiment(sentiment_counts):
	"""
	Calculate overall sentiment from conversation history.

	Args:
		sentiment_counts (list): List of sentiment counts

	Returns:
		str: Overall sentiment (Positive, Neutral, Negative)
	"""
	if not sentiment_counts:
		return None

	total = sum(s.get("count", 0) for s in sentiment_counts)
	if total == 0:
		return None

	# Calculate weighted score
	scores = {
		"Positive": 1,
		"Neutral": 0,
		"Negative": -1
	}

	weighted_sum = sum(
		scores.get(s.get("sentiment"), 0) * s.get("count", 0)
		for s in sentiment_counts
	)

	avg_score = weighted_sum / total

	# Map to overall sentiment
	if avg_score > 0.2:
		return "Positive"
	elif avg_score < -0.2:
		return "Negative"
	else:
		return "Neutral"


# Main CLI interface

def main():
	"""Main migration interface."""
	print("=" * 60)
	print("AI Communications Hub - Data Migration")
	print("=" * 60)
	print("\nAvailable migrations:")
	print("1. Migrate Chatwoot conversations")
	print("2. Backfill customer social IDs")
	print("3. Sync historical knowledge")
	print("4. Recalculate customer metrics")
	print("5. Run all migrations")
	print("\n0. Exit")

	choice = input("\nSelect migration (0-5): ")

	if choice == "1":
		migrate_chatwoot_conversations()
	elif choice == "2":
		backfill_customer_social_ids()
	elif choice == "3":
		sync_historical_knowledge()
	elif choice == "4":
		recalculate_customer_metrics()
	elif choice == "5":
		migrate_chatwoot_conversations()
		backfill_customer_social_ids()
		sync_historical_knowledge()
		recalculate_customer_metrics()
	else:
		print("Exiting...")


if __name__ == "__main__":
	main()
