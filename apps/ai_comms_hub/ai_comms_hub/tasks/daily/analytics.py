#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Generate daily analytics and metrics.

Scheduled: Daily at 1:00 AM
Purpose: Calculate KPIs, update dashboards, generate insights
"""

import frappe
from frappe import _
from datetime import datetime, timedelta
from collections import defaultdict


def calculate_daily_metrics():
	"""
	Calculate key metrics for the past 24 hours.
	"""
	yesterday = datetime.now() - timedelta(days=1)

	metrics = {
		"date": yesterday.date(),
		"total_conversations": 0,
		"ai_resolved": 0,
		"escalated": 0,
		"avg_response_time": 0,
		"avg_resolution_time": 0,
		"customer_satisfaction": 0,
		"by_channel": defaultdict(int),
		"by_sentiment": defaultdict(int),
		"top_intents": defaultdict(int)
	}

	# Get all conversations from yesterday
	conversations = frappe.get_all(
		"Communication Hub",
		filters={"creation": [">=", yesterday]},
		fields=[
			"name", "channel", "status", "ai_mode",
			"customer_sentiment", "resolution_time", "escalation_reason"
		]
	)

	metrics["total_conversations"] = len(conversations)

	for conv in conversations:
		# Count by channel
		metrics["by_channel"][conv["channel"]] += 1

		# Count by status
		if conv["status"] == "Resolved" and conv["ai_mode"] != "Human Takeover":
			metrics["ai_resolved"] += 1
		elif conv["status"] == "Escalated":
			metrics["escalated"] += 1

		# Count by sentiment
		if conv["customer_sentiment"]:
			metrics["by_sentiment"][conv["customer_sentiment"]] += 1

		# Average resolution time
		if conv["resolution_time"]:
			metrics["avg_resolution_time"] += conv["resolution_time"]

	# Calculate averages
	if metrics["total_conversations"] > 0:
		metrics["ai_resolution_rate"] = (metrics["ai_resolved"] / metrics["total_conversations"]) * 100
		metrics["escalation_rate"] = (metrics["escalated"] / metrics["total_conversations"]) * 100

		if metrics["ai_resolved"] > 0:
			metrics["avg_resolution_time"] = metrics["avg_resolution_time"] / metrics["ai_resolved"]

	# Save metrics
	try:
		metrics_doc = frappe.get_doc({
			"doctype": "Communication Analytics",
			"date": metrics["date"],
			"total_conversations": metrics["total_conversations"],
			"ai_resolved": metrics["ai_resolved"],
			"escalated": metrics["escalated"],
			"ai_resolution_rate": metrics.get("ai_resolution_rate", 0),
			"escalation_rate": metrics.get("escalation_rate", 0),
			"avg_resolution_time": metrics["avg_resolution_time"],
			"metrics_json": frappe.as_json(metrics)
		})
		metrics_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		print(f"Daily metrics calculated: {metrics['total_conversations']} conversations")

	except Exception as e:
		frappe.log_error(f"Error saving daily metrics: {str(e)}", "Daily Analytics")

	return metrics


def update_customer_metrics():
	"""
	Update AI-related metrics for all active customers.
	"""
	# Get customers with recent interactions
	yesterday = datetime.now() - timedelta(days=1)

	customers = frappe.get_all(
		"Customer",
		filters={"modified": [">=", yesterday]},
		limit=1000
	)

	updated = 0

	for customer in customers:
		try:
			# Get customer's conversations
			conversations = frappe.get_all(
				"Communication Hub",
				filters={"customer": customer.name},
				fields=["status", "ai_mode", "customer_sentiment", "creation"]
			)

			if not conversations:
				continue

			# Calculate metrics
			total = len(conversations)
			ai_resolved = len([c for c in conversations if c["status"] == "Resolved" and c["ai_mode"] != "Human Takeover"])
			resolution_rate = (ai_resolved / total) * 100 if total > 0 else 0

			# Average sentiment score
			sentiments = [c["customer_sentiment"] for c in conversations if c["customer_sentiment"]]
			sentiment_map = {"Positive": 1, "Neutral": 0, "Negative": -1}
			avg_sentiment = sum(sentiment_map.get(s, 0) for s in sentiments) / len(sentiments) if sentiments else 0

			# Last interaction
			last_interaction = max(c["creation"] for c in conversations) if conversations else None

			# Update customer
			frappe.db.set_value(
				"Customer",
				customer.name,
				{
					"total_ai_conversations": total,
					"ai_resolution_rate": resolution_rate,
					"avg_sentiment_score": avg_sentiment,
					"last_ai_interaction": last_interaction
				},
				update_modified=False
			)

			updated += 1

		except Exception as e:
			frappe.log_error(
				f"Error updating metrics for customer {customer.name}: {str(e)}",
				"Customer Metrics Update"
			)

	frappe.db.commit()
	print(f"Updated metrics for {updated} customers")


def identify_trends():
	"""
	Identify trends and anomalies in the data.
	"""
	# Get last 7 days of metrics
	week_ago = datetime.now() - timedelta(days=7)

	metrics = frappe.get_all(
		"Communication Analytics",
		filters={"date": [">=", week_ago.date()]},
		fields=["date", "total_conversations", "ai_resolution_rate", "escalation_rate"],
		order_by="date asc"
	)

	if len(metrics) < 3:
		return  # Need at least 3 days to identify trends

	# Calculate trend direction
	recent_conversations = sum(m["total_conversations"] for m in metrics[-3:])
	previous_conversations = sum(m["total_conversations"] for m in metrics[-6:-3]) if len(metrics) >= 6 else recent_conversations

	trend = "increasing" if recent_conversations > previous_conversations * 1.1 else \
	        "decreasing" if recent_conversations < previous_conversations * 0.9 else \
	        "stable"

	# Calculate average metrics
	avg_resolution = sum(m["ai_resolution_rate"] for m in metrics) / len(metrics)
	avg_escalation = sum(m["escalation_rate"] for m in metrics) / len(metrics)

	# Identify anomalies
	anomalies = []
	for m in metrics:
		if m["ai_resolution_rate"] < avg_resolution * 0.8:
			anomalies.append(f"Low AI resolution rate on {m['date']}: {m['ai_resolution_rate']:.1f}%")
		if m["escalation_rate"] > avg_escalation * 1.5:
			anomalies.append(f"High escalation rate on {m['date']}: {m['escalation_rate']:.1f}%")

	# Log findings
	if anomalies:
		frappe.log_error("\n".join(anomalies), "Analytics Anomalies")

	print(f"Trend analysis: Conversation volume is {trend}")
	print(f"Average AI resolution rate: {avg_resolution:.1f}%")
	print(f"Average escalation rate: {avg_escalation:.1f}%")


def generate_top_intents_report():
	"""
	Identify most common customer intents from the past day.
	"""
	yesterday = datetime.now() - timedelta(days=1)

	# Get all messages with detected intents
	messages = frappe.get_all(
		"Communication Message",
		filters={
			"creation": [">=", yesterday],
			"detected_intent": ["!=", ""]
		},
		fields=["detected_intent"],
		limit=10000
	)

	# Count intents
	intent_counts = defaultdict(int)
	for msg in messages:
		if msg["detected_intent"]:
			intent_counts[msg["detected_intent"]] += 1

	# Sort by frequency
	sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)

	print("Top customer intents from yesterday:")
	for intent, count in sorted_intents[:10]:
		print(f"  {intent}: {count} occurrences")

	return sorted_intents[:10]


def all():
	"""
	Run all daily analytics tasks.
	"""
	print("Running daily analytics tasks...")

	calculate_daily_metrics()
	update_customer_metrics()
	identify_trends()
	generate_top_intents_report()

	print("Daily analytics tasks completed")
