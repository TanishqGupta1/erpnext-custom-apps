#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Cleanup old conversations and data.

Scheduled: Daily at 2:00 AM
Purpose: Archive old data, cleanup temporary files, maintain database health
"""

import frappe
from frappe import _
from datetime import datetime, timedelta
import os


def cleanup_old_conversations():
	"""
	Archive conversations older than retention period.
	"""
	settings = frappe.get_single("AI Communications Hub Settings")
	retention_days = settings.conversation_retention_days or 90

	cutoff_date = datetime.now() - timedelta(days=retention_days)

	# Find old resolved conversations
	old_conversations = frappe.get_all(
		"Communication Hub",
		filters={
			"status": ["in", ["Resolved", "Closed"]],
			"modified": ["<", cutoff_date]
		},
		limit=1000
	)

	archived = 0

	for conv in old_conversations:
		try:
			# Mark as archived instead of deleting
			frappe.db.set_value(
				"Communication Hub",
				conv.name,
				"is_archived",
				1,
				update_modified=False
			)
			archived += 1

		except Exception as e:
			frappe.log_error(
				f"Error archiving conversation {conv.name}: {str(e)}",
				"Conversation Cleanup"
			)

	if archived > 0:
		frappe.db.commit()
		print(f"Archived {archived} old conversations")


def cleanup_error_logs():
	"""
	Delete old error logs (keep last 30 days).
	"""
	cutoff_date = datetime.now() - timedelta(days=30)

	try:
		# Delete old error logs
		frappe.db.sql("""
			DELETE FROM `tabError Log`
			WHERE creation < %s
			LIMIT 1000
		""", (cutoff_date,))

		frappe.db.commit()
		print("Cleaned up old error logs")

	except Exception as e:
		frappe.log_error(f"Error cleaning error logs: {str(e)}", "Error Log Cleanup")


def cleanup_temporary_files():
	"""
	Delete temporary files older than 7 days.
	"""
	temp_dir = frappe.get_site_path("private", "temp")

	if not os.path.exists(temp_dir):
		return

	cutoff_time = datetime.now() - timedelta(days=7)
	deleted = 0

	try:
		for filename in os.listdir(temp_dir):
			file_path = os.path.join(temp_dir, filename)

			if os.path.isfile(file_path):
				# Check file modification time
				file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

				if file_time < cutoff_time:
					os.remove(file_path)
					deleted += 1

		if deleted > 0:
			print(f"Deleted {deleted} temporary files")

	except Exception as e:
		frappe.log_error(f"Error cleaning temp files: {str(e)}", "Temp File Cleanup")


def cleanup_vector_database():
	"""
	Remove orphaned vectors from Qdrant (vectors without corresponding documents).
	"""
	from ai_comms_hub.api.rag import get_qdrant_settings
	import requests

	settings = get_qdrant_settings()

	try:
		# Get all vector IDs from Qdrant
		response = requests.post(
			f"{settings['url']}/collections/{settings['collection']}/points/scroll",
			json={
				"limit": 1000,
				"with_payload": False,
				"with_vector": False
			},
			timeout=10
		)

		if response.status_code != 200:
			return

		points = response.json().get("result", {}).get("points", [])

		# Check which Knowledge Base documents still exist
		orphaned_ids = []

		for point in points:
			kb_id = point["id"]

			if not frappe.db.exists("Knowledge Base Article", kb_id):
				orphaned_ids.append(kb_id)

		# Delete orphaned vectors
		if orphaned_ids:
			requests.post(
				f"{settings['url']}/collections/{settings['collection']}/points/delete",
				json={"points": orphaned_ids},
				timeout=30
			)

			print(f"Deleted {len(orphaned_ids)} orphaned vectors from Qdrant")

	except Exception as e:
		frappe.log_error(f"Error cleaning vector database: {str(e)}", "Vector DB Cleanup")


def optimize_database_tables():
	"""
	Optimize frequently accessed tables.
	"""
	tables = [
		"tabCommunication Hub",
		"tabCommunication Message",
		"tabKnowledge Base Article",
		"tabCustomer"
	]

	try:
		for table in tables:
			frappe.db.sql(f"OPTIMIZE TABLE `{table}`")

		print("Database tables optimized")

	except Exception as e:
		frappe.log_error(f"Error optimizing tables: {str(e)}", "Database Optimization")


def cleanup_duplicate_messages():
	"""
	Remove duplicate messages (same platform_message_id).
	"""
	# Find duplicates
	duplicates = frappe.db.sql("""
		SELECT platform_message_id, COUNT(*) as count
		FROM `tabCommunication Message`
		WHERE platform_message_id IS NOT NULL
		AND platform_message_id != ''
		GROUP BY platform_message_id
		HAVING count > 1
	""", as_dict=True)

	deleted = 0

	for dup in duplicates:
		# Get all messages with this ID
		messages = frappe.get_all(
			"Communication Message",
			filters={"platform_message_id": dup["platform_message_id"]},
			fields=["name", "creation"],
			order_by="creation asc"
		)

		# Keep the oldest, delete the rest
		for msg in messages[1:]:
			try:
				frappe.delete_doc("Communication Message", msg.name, ignore_permissions=True)
				deleted += 1
			except Exception as e:
				frappe.log_error(f"Error deleting duplicate message: {str(e)}", "Duplicate Cleanup")

	if deleted > 0:
		frappe.db.commit()
		print(f"Removed {deleted} duplicate messages")


def all():
	"""
	Run all daily cleanup tasks.
	"""
	print("Running daily cleanup tasks...")

	cleanup_old_conversations()
	cleanup_error_logs()
	cleanup_temporary_files()
	cleanup_vector_database()
	cleanup_duplicate_messages()
	optimize_database_tables()

	print("Daily cleanup tasks completed")
