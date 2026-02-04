#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Generate weekly summary reports.

Scheduled: Every Monday at 8:00 AM
Purpose: Generate comprehensive weekly performance reports
"""

import frappe
from frappe import _
from datetime import datetime, timedelta
from collections import defaultdict
import json


def generate_weekly_summary():
	"""
	Generate comprehensive weekly summary report.
	"""
	# Get last 7 days
	week_ago = datetime.now() - timedelta(days=7)

	# Gather metrics
	conversations = frappe.get_all(
		"Communication Hub",
		filters={"creation": [">=", week_ago]},
		fields=[
			"name", "channel", "status", "ai_mode", "customer_sentiment",
			"resolution_time", "escalation_reason", "customer"
		]
	)

	report = {
		"week_start": week_ago.date(),
		"week_end": datetime.now().date(),
		"total_conversations": len(conversations),
		"by_channel": defaultdict(int),
		"by_status": defaultdict(int),
		"by_sentiment": defaultdict(int),
		"escalation_reasons": defaultdict(int),
		"top_customers": defaultdict(int),
		"avg_resolution_time": 0,
		"ai_resolution_rate": 0,
		"escalation_rate": 0
	}

	resolution_times = []
	ai_resolved = 0
	escalated = 0

	for conv in conversations:
		# Count by channel
		report["by_channel"][conv["channel"]] += 1

		# Count by status
		report["by_status"][conv["status"]] += 1

		# Count by sentiment
		if conv["customer_sentiment"]:
			report["by_sentiment"][conv["customer_sentiment"]] += 1

		# Track AI resolution
		if conv["status"] == "Resolved" and conv["ai_mode"] != "Human Takeover":
			ai_resolved += 1

		if conv["status"] == "Escalated":
			escalated += 1
			if conv["escalation_reason"]:
				report["escalation_reasons"][conv["escalation_reason"]] += 1

		# Track resolution times
		if conv["resolution_time"]:
			resolution_times.append(conv["resolution_time"])

		# Track top customers
		if conv["customer"]:
			report["top_customers"][conv["customer"]] += 1

	# Calculate rates
	if report["total_conversations"] > 0:
		report["ai_resolution_rate"] = (ai_resolved / report["total_conversations"]) * 100
		report["escalation_rate"] = (escalated / report["total_conversations"]) * 100

	# Calculate average resolution time
	if resolution_times:
		report["avg_resolution_time"] = sum(resolution_times) / len(resolution_times)

	# Sort top customers
	report["top_customers"] = dict(sorted(
		report["top_customers"].items(),
		key=lambda x: x[1],
		reverse=True
	)[:10])

	# Save report
	try:
		report_doc = frappe.get_doc({
			"doctype": "Weekly Communication Report",
			"week_start": report["week_start"],
			"week_end": report["week_end"],
			"total_conversations": report["total_conversations"],
			"ai_resolution_rate": report["ai_resolution_rate"],
			"escalation_rate": report["escalation_rate"],
			"avg_resolution_time": report["avg_resolution_time"],
			"report_data": json.dumps(report, indent=2, default=str)
		})
		report_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		print(f"Weekly report generated: {report['total_conversations']} conversations")

	except Exception as e:
		frappe.log_error(f"Error saving weekly report: {str(e)}", "Weekly Report")

	return report


def analyze_ai_performance():
	"""
	Analyze AI agent performance over the past week.
	"""
	week_ago = datetime.now() - timedelta(days=7)

	# Get AI-handled conversations
	ai_conversations = frappe.get_all(
		"Communication Hub",
		filters={
			"creation": [">=", week_ago],
			"ai_mode": ["!=", "Human Takeover"]
		},
		fields=["name", "status", "customer_sentiment", "resolution_time"]
	)

	analysis = {
		"total_ai_handled": len(ai_conversations),
		"successful_resolutions": 0,
		"avg_resolution_time": 0,
		"positive_sentiment": 0,
		"negative_sentiment": 0
	}

	resolution_times = []

	for conv in ai_conversations:
		if conv["status"] == "Resolved":
			analysis["successful_resolutions"] += 1

		if conv["resolution_time"]:
			resolution_times.append(conv["resolution_time"])

		if conv["customer_sentiment"] == "Positive":
			analysis["positive_sentiment"] += 1
		elif conv["customer_sentiment"] == "Negative":
			analysis["negative_sentiment"] += 1

	# Calculate metrics
	if analysis["total_ai_handled"] > 0:
		analysis["success_rate"] = (analysis["successful_resolutions"] / analysis["total_ai_handled"]) * 100
		analysis["positive_sentiment_rate"] = (analysis["positive_sentiment"] / analysis["total_ai_handled"]) * 100

	if resolution_times:
		analysis["avg_resolution_time"] = sum(resolution_times) / len(resolution_times)

	print("AI Performance Analysis:")
	print(f"  Total conversations handled: {analysis['total_ai_handled']}")
	print(f"  Success rate: {analysis.get('success_rate', 0):.1f}%")
	print(f"  Positive sentiment: {analysis.get('positive_sentiment_rate', 0):.1f}%")
	print(f"  Avg resolution time: {analysis['avg_resolution_time']:.0f} seconds")

	return analysis


def identify_knowledge_gaps():
	"""
	Identify topics where AI lacks knowledge (low confidence responses).
	"""
	week_ago = datetime.now() - timedelta(days=7)

	# Get low confidence responses
	low_confidence_messages = frappe.db.sql("""
		SELECT cm.detected_intent, cm.rag_confidence, cm.message_text
		FROM `tabCommunication Message` cm
		WHERE cm.creation >= %s
		AND cm.sender_type = 'AI Agent'
		AND cm.rag_confidence < 0.5
		ORDER BY cm.rag_confidence ASC
		LIMIT 100
	""", (week_ago,), as_dict=True)

	# Group by intent
	gaps = defaultdict(list)

	for msg in low_confidence_messages:
		intent = msg["detected_intent"] or "Unknown"
		gaps[intent].append({
			"confidence": msg["rag_confidence"],
			"message": msg["message_text"][:100]  # First 100 chars
		})

	# Sort by frequency
	sorted_gaps = sorted(gaps.items(), key=lambda x: len(x[1]), reverse=True)

	print("Knowledge Gaps Identified:")
	for intent, messages in sorted_gaps[:5]:
		print(f"  {intent}: {len(messages)} low-confidence responses")

	# Log for review
	if sorted_gaps:
		gap_report = "\n".join([
			f"{intent}: {len(msgs)} occurrences"
			for intent, msgs in sorted_gaps[:10]
		])
		frappe.log_error(gap_report, "Knowledge Gaps - Weekly Review")

	return dict(sorted_gaps)


def generate_customer_insights():
	"""
	Generate insights about customer behavior and preferences.
	"""
	week_ago = datetime.now() - timedelta(days=7)

	# Get customer preferences
	customer_data = frappe.db.sql("""
		SELECT
			ch.customer,
			ch.channel,
			ch.customer_sentiment,
			COUNT(*) as interaction_count
		FROM `tabCommunication Hub` ch
		WHERE ch.creation >= %s
		AND ch.customer IS NOT NULL
		GROUP BY ch.customer, ch.channel, ch.customer_sentiment
	""", (week_ago,), as_dict=True)

	insights = {
		"most_active_customers": defaultdict(int),
		"channel_preferences": defaultdict(lambda: defaultdict(int)),
		"sentiment_by_customer": defaultdict(lambda: defaultdict(int))
	}

	for row in customer_data:
		customer = row["customer"]

		# Track activity
		insights["most_active_customers"][customer] += row["interaction_count"]

		# Track channel preference
		insights["channel_preferences"][customer][row["channel"]] += row["interaction_count"]

		# Track sentiment
		if row["customer_sentiment"]:
			insights["sentiment_by_customer"][customer][row["customer_sentiment"]] += 1

	# Find top 10 most active
	top_customers = sorted(
		insights["most_active_customers"].items(),
		key=lambda x: x[1],
		reverse=True
	)[:10]

	print("Top Active Customers This Week:")
	for customer, count in top_customers:
		print(f"  {customer}: {count} interactions")

	return insights


def all():
	"""
	Run all weekly report tasks.
	"""
	print("Running weekly report tasks...")

	generate_weekly_summary()
	analyze_ai_performance()
	identify_knowledge_gaps()
	generate_customer_insights()

	print("Weekly report tasks completed")
