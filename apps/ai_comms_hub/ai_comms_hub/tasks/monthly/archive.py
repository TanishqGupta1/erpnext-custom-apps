#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Archive old data and generate monthly reports.

Scheduled: 1st of every month at 3:00 AM
Purpose: Long-term data archival, monthly performance reports, compliance
"""

import frappe
from frappe import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import gzip
import os


def archive_old_conversations():
	"""
	Move conversations older than 6 months to archive table.
	"""
	cutoff_date = datetime.now() - relativedelta(months=6)

	# Find conversations to archive
	conversations = frappe.get_all(
		"Communication Hub",
		filters={
			"status": ["in", ["Resolved", "Closed"]],
			"modified": ["<", cutoff_date],
			"is_archived": 0
		},
		limit=5000
	)

	archived = 0

	for conv in conversations:
		try:
			# Get full conversation data
			conv_doc = frappe.get_doc("Communication Hub", conv.name)

			# Export to JSON
			conv_json = conv_doc.as_dict()

			# Get all messages
			messages = frappe.get_all(
				"Communication Message",
				filters={"parent": conv.name},
				fields="*"
			)
			conv_json["messages"] = messages

			# Save to archive file
			archive_path = frappe.get_site_path("private", "archives", "conversations")
			os.makedirs(archive_path, exist_ok=True)

			year_month = conv_doc.creation.strftime("%Y-%m")
			archive_file = os.path.join(archive_path, f"{year_month}.jsonl.gz")

			# Append to compressed file
			with gzip.open(archive_file, "at") as f:
				f.write(json.dumps(conv_json, default=str) + "\n")

			# Mark as archived
			frappe.db.set_value(
				"Communication Hub",
				conv.name,
				"is_archived",
				1,
				update_modified=False
			)

			archived += 1

			# Commit every 100 records
			if archived % 100 == 0:
				frappe.db.commit()

		except Exception as e:
			frappe.log_error(
				f"Error archiving conversation {conv.name}: {str(e)}",
				"Monthly Archive"
			)

	frappe.db.commit()
	print(f"Archived {archived} conversations")


def generate_monthly_report():
	"""
	Generate comprehensive monthly performance report.
	"""
	# Get last month's data
	today = datetime.now()
	last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
	last_month_end = today.replace(day=1) - timedelta(days=1)

	conversations = frappe.get_all(
		"Communication Hub",
		filters={
			"creation": ["between", [last_month_start, last_month_end]]
		},
		fields=[
			"name", "channel", "status", "ai_mode", "customer_sentiment",
			"resolution_time", "escalation_reason", "customer"
		]
	)

	report = {
		"month": last_month_start.strftime("%B %Y"),
		"start_date": last_month_start.date(),
		"end_date": last_month_end.date(),
		"total_conversations": len(conversations),
		"by_channel": {},
		"by_status": {},
		"by_sentiment": {},
		"escalation_reasons": {},
		"metrics": {
			"ai_resolution_rate": 0,
			"escalation_rate": 0,
			"avg_resolution_time": 0,
			"customer_satisfaction": 0
		}
	}

	# Count by channel
	from collections import Counter

	report["by_channel"] = dict(Counter(c["channel"] for c in conversations))
	report["by_status"] = dict(Counter(c["status"] for c in conversations))
	report["by_sentiment"] = dict(Counter(c["customer_sentiment"] for c in conversations if c["customer_sentiment"]))

	# Calculate metrics
	ai_resolved = len([c for c in conversations if c["status"] == "Resolved" and c["ai_mode"] != "Human Takeover"])
	escalated = len([c for c in conversations if c["status"] == "Escalated"])

	if report["total_conversations"] > 0:
		report["metrics"]["ai_resolution_rate"] = (ai_resolved / report["total_conversations"]) * 100
		report["metrics"]["escalation_rate"] = (escalated / report["total_conversations"]) * 100

	# Average resolution time
	resolution_times = [c["resolution_time"] for c in conversations if c["resolution_time"]]
	if resolution_times:
		report["metrics"]["avg_resolution_time"] = sum(resolution_times) / len(resolution_times)

	# Save report
	try:
		report_doc = frappe.get_doc({
			"doctype": "Monthly Communication Report",
			"month": last_month_start.month,
			"year": last_month_start.year,
			"start_date": report["start_date"],
			"end_date": report["end_date"],
			"total_conversations": report["total_conversations"],
			"ai_resolution_rate": report["metrics"]["ai_resolution_rate"],
			"escalation_rate": report["metrics"]["escalation_rate"],
			"avg_resolution_time": report["metrics"]["avg_resolution_time"],
			"report_data": json.dumps(report, indent=2, default=str)
		})
		report_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		print(f"Monthly report generated for {report['month']}")

	except Exception as e:
		frappe.log_error(f"Error saving monthly report: {str(e)}", "Monthly Report")

	return report


def calculate_cost_metrics():
	"""
	Calculate monthly costs for AI operations (LLM API usage, etc.).
	"""
	last_month_start = (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1)
	last_month_end = datetime.now().replace(day=1) - timedelta(days=1)

	# Get all AI messages from last month
	messages = frappe.db.sql("""
		SELECT
			COUNT(*) as total_messages,
			SUM(token_count) as total_tokens,
			AVG(token_count) as avg_tokens_per_message
		FROM `tabCommunication Message`
		WHERE sender_type = 'AI Agent'
		AND creation BETWEEN %s AND %s
	""", (last_month_start, last_month_end), as_dict=True)[0]

	# Estimate costs (using naga.ac pricing: ~$0.50 per 1M tokens)
	cost_per_million_tokens = 0.50
	total_tokens = messages["total_tokens"] or 0
	estimated_cost = (total_tokens / 1_000_000) * cost_per_million_tokens

	# Get conversation count
	conversations = frappe.db.count(
		"Communication Hub",
		filters={"creation": ["between", [last_month_start, last_month_end]]}
	)

	cost_per_conversation = estimated_cost / conversations if conversations > 0 else 0

	print("Monthly Cost Analysis:")
	print(f"  Total AI messages: {messages['total_messages']}")
	print(f"  Total tokens: {total_tokens:,}")
	print(f"  Estimated LLM cost: ${estimated_cost:.2f}")
	print(f"  Cost per conversation: ${cost_per_conversation:.4f}")

	return {
		"month": last_month_start.strftime("%B %Y"),
		"total_messages": messages["total_messages"],
		"total_tokens": total_tokens,
		"estimated_cost": estimated_cost,
		"cost_per_conversation": cost_per_conversation
	}


def update_knowledge_base_metrics():
	"""
	Calculate knowledge base effectiveness metrics.
	"""
	last_month_start = (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1)
	last_month_end = datetime.now().replace(day=1) - timedelta(days=1)

	# Get RAG usage stats
	rag_stats = frappe.db.sql("""
		SELECT
			AVG(rag_confidence) as avg_confidence,
			COUNT(CASE WHEN rag_confidence >= 0.8 THEN 1 END) as high_confidence_count,
			COUNT(CASE WHEN rag_confidence < 0.5 THEN 1 END) as low_confidence_count,
			COUNT(*) as total_rag_queries
		FROM `tabCommunication Message`
		WHERE sender_type = 'AI Agent'
		AND rag_confidence IS NOT NULL
		AND creation BETWEEN %s AND %s
	""", (last_month_start, last_month_end), as_dict=True)[0]

	# Get most-accessed articles
	popular_articles = frappe.db.sql("""
		SELECT
			kb.title,
			kb.access_count,
			kb.category
		FROM `tabKnowledge Base Article` kb
		ORDER BY kb.access_count DESC
		LIMIT 10
	""", as_dict=True)

	print("Knowledge Base Metrics:")
	print(f"  Avg RAG confidence: {rag_stats['avg_confidence']:.2f}")
	print(f"  High confidence responses: {rag_stats['high_confidence_count']}")
	print(f"  Low confidence responses: {rag_stats['low_confidence_count']}")
	print(f"  Total RAG queries: {rag_stats['total_rag_queries']}")

	return {
		"stats": rag_stats,
		"popular_articles": popular_articles
	}


def generate_compliance_report():
	"""
	Generate compliance report (GDPR, data retention, opt-outs).
	"""
	last_month_start = (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1)
	last_month_end = datetime.now().replace(day=1) - timedelta(days=1)

	report = {
		"month": last_month_start.strftime("%B %Y"),
		"data_processed": 0,
		"opt_outs": 0,
		"data_deletion_requests": 0,
		"archived_conversations": 0
	}

	# Count conversations (data processed)
	report["data_processed"] = frappe.db.count(
		"Communication Hub",
		filters={"creation": ["between", [last_month_start, last_month_end]]}
	)

	# Count SMS opt-outs
	report["opt_outs"] = frappe.db.count(
		"Communication Hub",
		filters={
			"creation": ["between", [last_month_start, last_month_end]],
			"channel": "SMS",
			"sms_opt_out": 1
		}
	)

	# Count archived conversations
	report["archived_conversations"] = frappe.db.count(
		"Communication Hub",
		filters={
			"modified": ["between", [last_month_start, last_month_end]],
			"is_archived": 1
		}
	)

	print("Compliance Report:")
	print(f"  Data records processed: {report['data_processed']}")
	print(f"  SMS opt-outs: {report['opt_outs']}")
	print(f"  Conversations archived: {report['archived_conversations']}")

	# Log for audit trail
	frappe.log_error(json.dumps(report, indent=2), "Monthly Compliance Report")

	return report


def all():
	"""
	Run all monthly archive tasks.
	"""
	print("Running monthly archive tasks...")

	archive_old_conversations()
	generate_monthly_report()
	calculate_cost_metrics()
	update_knowledge_base_metrics()
	generate_compliance_report()

	print("Monthly archive tasks completed")
