#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Sync messages across platforms (Twitter polling, status updates, etc.).

Scheduled: Every hour
Purpose: Poll platforms that don't support webhooks, sync message statuses
"""

import frappe
from frappe import _
import requests
from datetime import datetime, timedelta


def sync_twitter_dms():
	"""
	Poll Twitter DMs for accounts without premium API.

	Note: This is a backup for n8n workflow. Only used if n8n is down.
	"""
	settings = frappe.get_single("AI Communications Hub Settings")

	if not settings.twitter_bearer_token:
		frappe.log_error("Twitter bearer token not configured", "Twitter DM Sync")
		return

	try:
		# Get last sync time
		last_sync = frappe.db.get_value(
			"Communication Hub",
			{"channel": "Twitter"},
			"MAX(modified)",
			as_dict=False
		) or datetime.now() - timedelta(hours=1)

		headers = {"Authorization": f"Bearer {settings.twitter_bearer_token}"}

		# Get DMs
		response = requests.get(
			"https://api.twitter.com/2/dm_events",
			headers=headers,
			params={
				"dm_event.fields": "id,text,created_at,sender_id",
				"max_results": 100
			},
			timeout=10
		)

		if response.status_code != 200:
			frappe.log_error(f"Twitter API error: {response.status_code}", "Twitter DM Sync")
			return

		data = response.json()
		new_messages = 0

		for dm in data.get("data", []):
			# Check if message already exists
			if frappe.db.exists("Communication Hub", {"twitter_dm_id": dm["id"]}):
				continue

			# Create new Communication Hub
			hub = frappe.get_doc({
				"doctype": "Communication Hub",
				"channel": "Twitter",
				"sender_id": dm["sender_id"],
				"twitter_dm_id": dm["id"],
				"status": "Open",
				"ai_mode": settings.default_ai_mode or "Autonomous"
			})
			hub.insert(ignore_permissions=True)

			# Create message
			message = frappe.get_doc({
				"doctype": "Communication Message",
				"parent": hub.name,
				"parenttype": "Communication Hub",
				"parentfield": "messages",
				"message_text": dm.get("text", ""),
				"sender_type": "Customer",
				"timestamp": dm.get("created_at")
			})
			message.insert(ignore_permissions=True)

			new_messages += 1

		if new_messages > 0:
			frappe.db.commit()
			print(f"Synced {new_messages} new Twitter DMs")

	except Exception as e:
		frappe.log_error(f"Error syncing Twitter DMs: {str(e)}", "Twitter DM Sync")


def update_message_statuses():
	"""
	Update delivery and read statuses for messages across platforms.
	"""
	# Get messages sent in last 24 hours that don't have confirmed delivery
	messages = frappe.get_all(
		"Communication Message",
		filters={
			"sender_type": "AI Agent",
			"delivery_status": ["in", ["Pending", "Sent"]],
			"modified": [">=", datetime.now() - timedelta(hours=24)]
		},
		fields=["name", "parent", "platform_message_id"],
		limit=100
	)

	for msg in messages:
		try:
			# Get parent Communication Hub
			hub = frappe.get_doc("Communication Hub", msg["parent"])

			# Platform-specific status check
			if hub.channel == "WhatsApp":
				update_whatsapp_status(msg, hub)
			elif hub.channel == "SMS":
				update_sms_status(msg, hub)
			# Add more platforms as needed

		except Exception as e:
			frappe.log_error(
				f"Error updating message status for {msg['name']}: {str(e)}",
				"Message Status Update"
			)


def update_whatsapp_status(message, hub):
	"""
	Update WhatsApp message delivery status via Twilio API.
	"""
	settings = frappe.get_single("AI Communications Hub Settings")

	if not settings.twilio_account_sid or not message.get("platform_message_id"):
		return

	try:
		from requests.auth import HTTPBasicAuth

		auth = HTTPBasicAuth(settings.twilio_account_sid, settings.twilio_auth_token)

		response = requests.get(
			f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages/{message['platform_message_id']}.json",
			auth=auth,
			timeout=10
		)

		if response.status_code == 200:
			data = response.json()
			status_map = {
				"queued": "Pending",
				"sending": "Pending",
				"sent": "Sent",
				"delivered": "Delivered",
				"read": "Read",
				"failed": "Failed",
				"undelivered": "Failed"
			}

			new_status = status_map.get(data.get("status"), "Pending")

			frappe.db.set_value(
				"Communication Message",
				message["name"],
				"delivery_status",
				new_status,
				update_modified=False
			)

	except Exception as e:
		frappe.log_error(f"WhatsApp status update error: {str(e)}", "WhatsApp Status")


def update_sms_status(message, hub):
	"""
	Update SMS message delivery status via Twilio API.
	"""
	# Same as WhatsApp - Twilio handles both
	update_whatsapp_status(message, hub)


def sync_chatwoot_conversations():
	"""
	Sync Chatwoot conversation statuses (resolved, reopened, etc.).
	"""
	settings = frappe.get_single("AI Communications Hub Settings")

	if not settings.chatwoot_api_key or not settings.chatwoot_account_id:
		return

	try:
		headers = {"api_access_token": settings.chatwoot_api_key}

		# Get conversations updated in last hour
		response = requests.get(
			f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/conversations",
			headers=headers,
			params={"status": "all"},
			timeout=10
		)

		if response.status_code != 200:
			frappe.log_error(f"Chatwoot API error: {response.status_code}", "Chatwoot Sync")
			return

		conversations = response.json().get("data", {}).get("payload", [])

		for conv in conversations:
			conv_id = str(conv.get("id"))

			# Find matching Communication Hub
			hubs = frappe.get_all(
				"Communication Hub",
				filters={"chatwoot_conversation_id": conv_id},
				limit=1
			)

			if not hubs:
				continue

			# Update status
			chatwoot_status = conv.get("status")
			status_map = {
				"open": "In Progress",
				"resolved": "Resolved",
				"pending": "Open"
			}

			new_status = status_map.get(chatwoot_status, "Open")

			frappe.db.set_value(
				"Communication Hub",
				hubs[0].name,
				"status",
				new_status,
				update_modified=False
			)

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(f"Error syncing Chatwoot: {str(e)}", "Chatwoot Sync")


def sync_pending_messages():
	"""
	Sync pending messages - retry failed deliveries and poll platforms.

	This is the main entry point called by the scheduler.
	"""
	print("Running sync_pending_messages...")

	# Retry failed message deliveries
	retry_failed_deliveries()

	# Poll platforms without webhooks
	sync_twitter_dms()

	# Sync Chatwoot conversations
	sync_chatwoot_conversations()

	# Update message statuses
	update_message_statuses()

	print("sync_pending_messages completed")


def retry_failed_deliveries():
	"""
	Retry messages that failed to deliver.
	"""
	# Get messages that failed in the last 24 hours
	failed_messages = frappe.get_all(
		"Communication Message",
		filters={
			"delivery_status": "Failed",
			"retry_count": ["<", 3],
			"modified": [">=", datetime.now() - timedelta(hours=24)]
		},
		fields=["name", "communication_hub"],
		limit=50
	)

	for msg in failed_messages:
		try:
			from ai_comms_hub.api.message import deliver_message

			# Increment retry count
			frappe.db.set_value(
				"Communication Message",
				msg.name,
				"retry_count",
				frappe.db.get_value("Communication Message", msg.name, "retry_count") + 1
			)

			# Attempt redelivery
			deliver_message(msg.name)

		except Exception as e:
			frappe.log_error(f"Retry failed for {msg.name}: {str(e)}", "Message Retry")

	if failed_messages:
		frappe.db.commit()
		print(f"Retried {len(failed_messages)} failed messages")


def check_conversation_timeouts():
	"""
	Check for conversations that need attention due to timeouts.

	This is called by the scheduler hourly.
	"""
	print("Running check_conversation_timeouts...")

	settings = frappe.get_single("AI Communications Hub Settings")

	# Get response timeout (default 30 minutes)
	response_timeout = getattr(settings, 'response_timeout_minutes', 30) or 30
	cutoff_time = datetime.now() - timedelta(minutes=response_timeout)

	# Find conversations waiting for AI response
	waiting_hubs = frappe.get_all(
		"Communication Hub",
		filters={
			"status": "Open",
			"ai_mode": "Autonomous",
			"modified": ["<", cutoff_time]
		},
		fields=["name", "customer", "channel"],
		limit=100
	)

	for hub in waiting_hubs:
		try:
			# Check if last message was from customer (awaiting response)
			last_message = frappe.get_all(
				"Communication Message",
				filters={"communication_hub": hub.name},
				fields=["sender_type", "creation"],
				order_by="creation desc",
				limit=1
			)

			if last_message and last_message[0].sender_type == "Customer":
				# Customer is waiting - escalate or retry AI
				if last_message[0].creation < cutoff_time:
					# Escalate to HITL
					frappe.db.set_value(
						"Communication Hub",
						hub.name,
						{
							"ai_mode": "HITL",
							"escalation_reason": "Response timeout - customer waiting"
						}
					)

					# Notify agents
					from ai_comms_hub.api.communication import notify_agents_hitl_request
					hub_doc = frappe.get_doc("Communication Hub", hub.name)
					notify_agents_hitl_request(hub_doc)

					frappe.logger().warning(f"Escalated timeout hub: {hub.name}")

		except Exception as e:
			frappe.log_error(f"Timeout check error for {hub.name}: {str(e)}", "Conversation Timeout")

	if waiting_hubs:
		frappe.db.commit()

	print(f"Checked {len(waiting_hubs)} conversations for timeouts")


def all():
	"""
	Run all hourly sync tasks.
	"""
	print("Running hourly sync tasks...")

	sync_pending_messages()
	check_conversation_timeouts()

	print("Hourly sync tasks completed")
