"""
Tasks that run on every scheduler tick (every minute).

These are lightweight maintenance tasks:
- Session cleanup
- Stale connection handling
- Quick health checks
"""

import frappe
from frappe import _
from datetime import datetime, timedelta


def cleanup_old_sessions():
	"""
	Clean up old/stale sessions and temporary data.

	Runs every minute to ensure timely cleanup.
	"""
	try:
		cleanup_stale_conversations()
		cleanup_expired_tokens()
		cleanup_temporary_files()

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Session Cleanup Error")


def cleanup_stale_conversations():
	"""
	Handle conversations that have been inactive for too long.
	"""
	settings = frappe.get_single("AI Communications Hub Settings")

	# Get auto-close timeout (default 24 hours)
	timeout_hours = getattr(settings, 'auto_close_timeout', 24) or 24
	cutoff_time = datetime.now() - timedelta(hours=timeout_hours)

	# Find stale open conversations
	stale_hubs = frappe.get_all(
		"Communication Hub",
		filters={
			"status": ["in", ["Open", "In Progress"]],
			"modified": ["<", cutoff_time]
		},
		fields=["name", "channel", "customer"],
		limit=100
	)

	for hub in stale_hubs:
		try:
			# Check if there's been any recent activity
			recent_message = frappe.get_all(
				"Communication Message",
				filters={
					"communication_hub": hub.name,
					"creation": [">", cutoff_time]
				},
				limit=1
			)

			if not recent_message:
				# Auto-close the conversation
				frappe.db.set_value(
					"Communication Hub",
					hub.name,
					{
						"status": "Auto-Closed",
						"resolution_summary": "Automatically closed due to inactivity"
					}
				)

				frappe.logger().info(f"Auto-closed stale conversation: {hub.name}")

		except Exception as e:
			frappe.log_error(f"Error closing stale hub {hub.name}: {str(e)}", "Stale Hub Cleanup")

	if stale_hubs:
		frappe.db.commit()


def cleanup_expired_tokens():
	"""
	Clean up expired webhook verification tokens and temporary auth data.
	"""
	# Clean up any temporary verification tokens older than 1 hour
	cutoff_time = datetime.now() - timedelta(hours=1)

	# Check if we have a token storage table
	if frappe.db.table_exists("AI Comms Temp Token"):
		frappe.db.delete(
			"AI Comms Temp Token",
			filters={"creation": ["<", cutoff_time]}
		)
		frappe.db.commit()


def cleanup_temporary_files():
	"""
	Clean up temporary files from attachment processing.
	"""
	import os

	# Get temp directory path
	temp_dir = frappe.get_site_path("private", "files", "ai_comms_temp")

	if not os.path.exists(temp_dir):
		return

	cutoff_time = datetime.now() - timedelta(hours=2)
	cutoff_timestamp = cutoff_time.timestamp()

	try:
		for filename in os.listdir(temp_dir):
			filepath = os.path.join(temp_dir, filename)

			if os.path.isfile(filepath):
				file_mtime = os.path.getmtime(filepath)

				if file_mtime < cutoff_timestamp:
					os.remove(filepath)
					frappe.logger().debug(f"Removed temp file: {filename}")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Temp File Cleanup Error")


def check_service_health():
	"""
	Quick health check for external services.
	Only logs errors, doesn't block.
	"""
	import requests

	settings = frappe.get_single("AI Communications Hub Settings")

	# Check Qdrant
	if settings.qdrant_url:
		try:
			response = requests.get(
				f"{settings.qdrant_url}/health",
				timeout=2
			)
			if response.status_code != 200:
				frappe.logger().warning("Qdrant health check failed")
		except Exception:
			frappe.logger().warning("Qdrant unreachable")

	# Check Chatwoot
	if settings.chatwoot_url and settings.chatwoot_api_key:
		try:
			response = requests.get(
				f"{settings.chatwoot_url}/api/v1/profile",
				headers={"api_access_token": settings.chatwoot_api_key},
				timeout=2
			)
			if response.status_code != 200:
				frappe.logger().warning("Chatwoot health check failed")
		except Exception:
			frappe.logger().warning("Chatwoot unreachable")
