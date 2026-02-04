import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate, now_datetime, time_diff_in_seconds
import json
from datetime import datetime, timedelta


@frappe.whitelist()
def get_dashboard_stats(period="today"):
	"""
	Get real-time dashboard statistics for AI Comms Hub.

	Args:
		period: "today", "week", "month", "year", or "all"

	Returns:
		Dictionary with all dashboard metrics
	"""
	filters = get_date_filters(period)

	stats = {
		"summary": get_summary_stats(filters),
		"resolution": get_resolution_stats(filters),
		"hitl": get_hitl_stats(filters),
		"timing": get_timing_stats(filters),
		"channels": get_channel_distribution(filters),
		"ai_modes": get_ai_mode_distribution(filters),
		"status": get_status_distribution(filters),
		"sentiment": get_sentiment_distribution(filters),
		"trends": get_trend_data(period)
	}

	return stats


def get_date_filters(period):
	"""Get date filter based on period."""
	today = nowdate()

	if period == "today":
		return {"created_at": [">=", today]}
	elif period == "week":
		return {"created_at": [">=", add_days(today, -7)]}
	elif period == "month":
		return {"created_at": [">=", add_days(today, -30)]}
	elif period == "year":
		return {"created_at": [">=", add_days(today, -365)]}
	else:
		return {}


def get_summary_stats(filters):
	"""Get summary statistics."""
	base_filters = filters.copy()

	total = frappe.db.count("Communication Hub", filters=base_filters)

	# New conversations (Open status)
	open_filters = base_filters.copy()
	open_filters["status"] = "Open"
	new_count = frappe.db.count("Communication Hub", filters=open_filters)

	# In Progress
	progress_filters = base_filters.copy()
	progress_filters["status"] = "In Progress"
	in_progress = frappe.db.count("Communication Hub", filters=progress_filters)

	# Resolved
	resolved_filters = base_filters.copy()
	resolved_filters["status"] = ["in", ["Resolved", "Closed"]]
	resolved = frappe.db.count("Communication Hub", filters=resolved_filters)

	# Pending Review (HITL)
	pending_filters = base_filters.copy()
	pending_filters["status"] = "Pending Review"
	pending_review = frappe.db.count("Communication Hub", filters=pending_filters)

	# Escalated
	escalated_filters = base_filters.copy()
	escalated_filters["status"] = "Escalated"
	escalated = frappe.db.count("Communication Hub", filters=escalated_filters)

	return {
		"total": total,
		"new": new_count,
		"in_progress": in_progress,
		"resolved": resolved,
		"pending_review": pending_review,
		"escalated": escalated
	}


def get_resolution_stats(filters):
	"""Get resolution statistics."""
	base_filters = filters.copy()

	# Total resolved
	resolved_filters = base_filters.copy()
	resolved_filters["status"] = ["in", ["Resolved", "Closed"]]
	total_resolved = frappe.db.count("Communication Hub", filters=resolved_filters)

	# AI Resolved (Autonomous mode that got resolved)
	ai_resolved_filters = resolved_filters.copy()
	ai_resolved_filters["ai_mode"] = "Autonomous"
	ai_resolved = frappe.db.count("Communication Hub", filters=ai_resolved_filters)

	# Human Resolved (Takeover or Manual mode)
	human_resolved_filters = resolved_filters.copy()
	human_resolved_filters["ai_mode"] = ["in", ["Takeover", "Manual"]]
	human_resolved = frappe.db.count("Communication Hub", filters=human_resolved_filters)

	# HITL Resolved
	hitl_resolved_filters = resolved_filters.copy()
	hitl_resolved_filters["ai_mode"] = "HITL"
	hitl_resolved = frappe.db.count("Communication Hub", filters=hitl_resolved_filters)

	# Escalated count
	escalated_filters = base_filters.copy()
	escalated_filters["status"] = "Escalated"
	escalated = frappe.db.count("Communication Hub", filters=escalated_filters)

	total = frappe.db.count("Communication Hub", filters=base_filters) or 1

	return {
		"total_resolved": total_resolved,
		"ai_resolved": ai_resolved,
		"human_resolved": human_resolved,
		"hitl_resolved": hitl_resolved,
		"escalated": escalated,
		"ai_resolution_rate": round((ai_resolved / total) * 100, 1) if total else 0,
		"human_resolution_rate": round((human_resolved / total) * 100, 1) if total else 0,
		"escalation_rate": round((escalated / total) * 100, 1) if total else 0
	}


def get_hitl_stats(filters):
	"""Get HITL-specific statistics."""
	base_filters = filters.copy()

	# HITL mode conversations
	hitl_filters = base_filters.copy()
	hitl_filters["ai_mode"] = "HITL"
	hitl_total = frappe.db.count("Communication Hub", filters=hitl_filters)

	# Pending Review
	pending_filters = base_filters.copy()
	pending_filters["status"] = "Pending Review"
	pending_review = frappe.db.count("Communication Hub", filters=pending_filters)

	# Get HITL with draft responses (approved)
	# We'll estimate approved as HITL conversations that moved to Resolved
	hitl_resolved_filters = base_filters.copy()
	hitl_resolved_filters["ai_mode"] = "HITL"
	hitl_resolved_filters["status"] = ["in", ["Resolved", "Closed"]]
	hitl_approved = frappe.db.count("Communication Hub", filters=hitl_resolved_filters)

	# Takeovers (conversations that switched to Takeover mode)
	takeover_filters = base_filters.copy()
	takeover_filters["ai_mode"] = "Takeover"
	takeovers = frappe.db.count("Communication Hub", filters=takeover_filters)

	# Calculate rejection as takeovers from HITL (approximation)
	hitl_rejected = max(0, hitl_total - hitl_approved - pending_review)

	approval_rate = round((hitl_approved / hitl_total) * 100, 1) if hitl_total else 0

	return {
		"total_hitl": hitl_total,
		"pending_review": pending_review,
		"approved": hitl_approved,
		"rejected": hitl_rejected,
		"takeovers": takeovers,
		"approval_rate": approval_rate
	}


def get_timing_stats(filters):
	"""Get timing/response time statistics."""
	# For now, return placeholder values
	# In production, this would calculate from actual message timestamps

	return {
		"avg_response_time": 0,
		"avg_first_response": 0,
		"avg_resolution_time": 0,
		"avg_ai_response_time": 0,
		"avg_hitl_review_time": 0
	}


def get_channel_distribution(filters):
	"""Get conversation distribution by channel."""
	result = frappe.db.sql("""
		SELECT channel, COUNT(*) as count
		FROM `tabCommunication Hub`
		WHERE 1=1
		{date_filter}
		GROUP BY channel
		ORDER BY count DESC
	""".format(date_filter=build_date_filter_sql(filters)), as_dict=True)

	return {row.channel: row.count for row in result if row.channel}


def get_ai_mode_distribution(filters):
	"""Get conversation distribution by AI mode."""
	result = frappe.db.sql("""
		SELECT ai_mode, COUNT(*) as count
		FROM `tabCommunication Hub`
		WHERE 1=1
		{date_filter}
		GROUP BY ai_mode
		ORDER BY count DESC
	""".format(date_filter=build_date_filter_sql(filters)), as_dict=True)

	return {row.ai_mode: row.count for row in result if row.ai_mode}


def get_status_distribution(filters):
	"""Get conversation distribution by status."""
	result = frappe.db.sql("""
		SELECT status, COUNT(*) as count
		FROM `tabCommunication Hub`
		WHERE 1=1
		{date_filter}
		GROUP BY status
		ORDER BY count DESC
	""".format(date_filter=build_date_filter_sql(filters)), as_dict=True)

	return {row.status: row.count for row in result if row.status}


def get_sentiment_distribution(filters):
	"""Get conversation distribution by sentiment."""
	result = frappe.db.sql("""
		SELECT sentiment, COUNT(*) as count
		FROM `tabCommunication Hub`
		WHERE sentiment IS NOT NULL AND sentiment != ''
		{date_filter}
		GROUP BY sentiment
		ORDER BY count DESC
	""".format(date_filter=build_date_filter_sql(filters)), as_dict=True)

	return {row.sentiment: row.count for row in result if row.sentiment}


def get_trend_data(period):
	"""Get trend data for charts."""
	today = getdate(nowdate())

	if period == "today":
		# Hourly data for today
		return get_hourly_trend(today)
	elif period == "week":
		# Daily data for last 7 days
		return get_daily_trend(7)
	elif period == "month":
		# Daily data for last 30 days
		return get_daily_trend(30)
	else:
		# Weekly data for last 12 weeks
		return get_weekly_trend(12)


def get_hourly_trend(date):
	"""Get hourly conversation count for a specific date."""
	result = frappe.db.sql("""
		SELECT HOUR(created_at) as hour, COUNT(*) as count
		FROM `tabCommunication Hub`
		WHERE DATE(created_at) = %s
		GROUP BY HOUR(created_at)
		ORDER BY hour
	""", (date,), as_dict=True)

	# Fill in all 24 hours
	hourly_data = {i: 0 for i in range(24)}
	for row in result:
		hourly_data[row.hour] = row.count

	return {
		"labels": [f"{h:02d}:00" for h in range(24)],
		"data": [hourly_data[h] for h in range(24)]
	}


def get_daily_trend(days):
	"""Get daily conversation count for last N days."""
	today = getdate(nowdate())
	start_date = add_days(today, -days + 1)

	result = frappe.db.sql("""
		SELECT DATE(created_at) as date, COUNT(*) as count
		FROM `tabCommunication Hub`
		WHERE DATE(created_at) >= %s
		GROUP BY DATE(created_at)
		ORDER BY date
	""", (start_date,), as_dict=True)

	# Create a dict for quick lookup
	daily_data = {str(row.date): row.count for row in result}

	# Generate all dates
	labels = []
	data = []
	for i in range(days):
		date = add_days(start_date, i)
		date_str = str(date)
		labels.append(date_str)
		data.append(daily_data.get(date_str, 0))

	return {
		"labels": labels,
		"data": data
	}


def get_weekly_trend(weeks):
	"""Get weekly conversation count for last N weeks."""
	today = getdate(nowdate())

	result = frappe.db.sql("""
		SELECT
			YEARWEEK(created_at, 1) as year_week,
			MIN(DATE(created_at)) as week_start,
			COUNT(*) as count
		FROM `tabCommunication Hub`
		WHERE created_at >= DATE_SUB(%s, INTERVAL %s WEEK)
		GROUP BY YEARWEEK(created_at, 1)
		ORDER BY year_week
	""", (today, weeks), as_dict=True)

	return {
		"labels": [str(row.week_start) for row in result],
		"data": [row.count for row in result]
	}


def build_date_filter_sql(filters):
	"""Build SQL date filter string."""
	if not filters:
		return ""

	for key, value in filters.items():
		if key == "created_at" and isinstance(value, list):
			operator, date_value = value
			return f"AND created_at {operator} '{date_value}'"

	return ""


@frappe.whitelist()
def get_number_card_data(card_name):
	"""
	Get data for a specific number card.

	Args:
		card_name: Name of the number card

	Returns:
		Dictionary with value and comparison data
	"""
	today = nowdate()
	yesterday = add_days(today, -1)

	card_configs = {
		"total_conversations": {
			"filters": {},
			"label": "Total Conversations"
		},
		"open_conversations": {
			"filters": {"status": "Open"},
			"label": "Open Conversations"
		},
		"pending_review": {
			"filters": {"status": "Pending Review"},
			"label": "Pending HITL Review"
		},
		"escalated": {
			"filters": {"status": "Escalated"},
			"label": "Escalated"
		},
		"ai_resolution_rate": {
			"type": "percentage",
			"label": "AI Resolution Rate"
		},
		"hitl_approval_rate": {
			"type": "percentage",
			"label": "HITL Approval Rate"
		}
	}

	if card_name not in card_configs:
		return {"value": 0, "label": card_name}

	config = card_configs[card_name]

	if config.get("type") == "percentage":
		stats = get_dashboard_stats("all")
		if card_name == "ai_resolution_rate":
			value = stats["resolution"]["ai_resolution_rate"]
		elif card_name == "hitl_approval_rate":
			value = stats["hitl"]["approval_rate"]
		else:
			value = 0

		return {
			"value": value,
			"label": config["label"],
			"suffix": "%"
		}
	else:
		# Today's count
		today_filters = config["filters"].copy()
		today_filters["created_at"] = [">=", today]
		today_count = frappe.db.count("Communication Hub", filters=today_filters)

		# Yesterday's count for comparison
		yesterday_filters = config["filters"].copy()
		yesterday_filters["created_at"] = ["between", [yesterday, today]]
		yesterday_count = frappe.db.count("Communication Hub", filters=yesterday_filters)

		# Total count
		total_count = frappe.db.count("Communication Hub", filters=config["filters"])

		# Calculate change percentage
		if yesterday_count > 0:
			change = round(((today_count - yesterday_count) / yesterday_count) * 100, 1)
		else:
			change = 100 if today_count > 0 else 0

		return {
			"value": total_count,
			"today": today_count,
			"yesterday": yesterday_count,
			"change": change,
			"label": config["label"]
		}


@frappe.whitelist()
def generate_daily_analytics(date=None):
	"""
	Generate or update daily analytics record.

	Args:
		date: Date to generate analytics for (defaults to today)

	Returns:
		Name of the created/updated analytics record
	"""
	if not date:
		date = nowdate()

	date = getdate(date)

	# Get stats for the specific date
	date_filters = {
		"created_at": ["between", [date, add_days(date, 1)]]
	}

	stats = {
		"summary": get_summary_stats(date_filters),
		"resolution": get_resolution_stats(date_filters),
		"hitl": get_hitl_stats(date_filters),
		"timing": get_timing_stats(date_filters),
		"channels": get_channel_distribution(date_filters),
		"ai_modes": get_ai_mode_distribution(date_filters),
		"status": get_status_distribution(date_filters),
		"sentiment": get_sentiment_distribution(date_filters)
	}

	# Check if record exists for this date
	existing = frappe.db.exists("Communication Analytics", {"date": date})

	if existing:
		doc = frappe.get_doc("Communication Analytics", existing)
	else:
		doc = frappe.new_doc("Communication Analytics")
		doc.date = date

	# Update fields
	doc.total_conversations = stats["summary"]["total"]
	doc.new_conversations = stats["summary"]["new"]
	doc.ai_resolved = stats["resolution"]["ai_resolved"]
	doc.human_resolved = stats["resolution"]["human_resolved"]
	doc.escalated = stats["resolution"]["escalated"]
	doc.ai_resolution_rate = stats["resolution"]["ai_resolution_rate"]
	doc.human_resolution_rate = stats["resolution"]["human_resolution_rate"]
	doc.escalation_rate = stats["resolution"]["escalation_rate"]

	# HITL metrics
	doc.hitl_reviews = stats["hitl"]["total_hitl"]
	doc.hitl_approved = stats["hitl"]["approved"]
	doc.hitl_rejected = stats["hitl"]["rejected"]
	doc.hitl_approval_rate = stats["hitl"]["approval_rate"]
	doc.takeovers = stats["hitl"]["takeovers"]

	# Timing (placeholder for now)
	doc.avg_response_time = stats["timing"]["avg_response_time"]
	doc.avg_resolution_time = stats["timing"]["avg_resolution_time"]
	doc.first_response_time = stats["timing"]["avg_first_response"]
	doc.avg_ai_response_time = stats["timing"]["avg_ai_response_time"]
	doc.avg_hitl_review_time = stats["timing"]["avg_hitl_review_time"]

	# Distribution data as JSON
	doc.by_channel = json.dumps(stats["channels"])
	doc.by_sentiment = json.dumps(stats["sentiment"])
	doc.by_ai_mode = json.dumps(stats["ai_modes"])
	doc.by_status = json.dumps(stats["status"])

	# Full metrics JSON
	doc.metrics_json = json.dumps(stats)

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return doc.name


@frappe.whitelist()
def get_chart_data(chart_type, period="week"):
	"""
	Get data for specific chart types.

	Args:
		chart_type: Type of chart (conversations_trend, channel_pie, status_pie, ai_mode_pie, sentiment_pie)
		period: Time period for data

	Returns:
		Chart data in Frappe chart format
	"""
	if chart_type == "conversations_trend":
		trend = get_trend_data(period)
		return {
			"labels": trend["labels"],
			"datasets": [
				{"name": "Conversations", "values": trend["data"]}
			]
		}

	elif chart_type == "channel_pie":
		filters = get_date_filters(period)
		data = get_channel_distribution(filters)
		return {
			"labels": list(data.keys()),
			"datasets": [
				{"name": "Channels", "values": list(data.values())}
			]
		}

	elif chart_type == "status_pie":
		filters = get_date_filters(period)
		data = get_status_distribution(filters)
		return {
			"labels": list(data.keys()),
			"datasets": [
				{"name": "Status", "values": list(data.values())}
			]
		}

	elif chart_type == "ai_mode_pie":
		filters = get_date_filters(period)
		data = get_ai_mode_distribution(filters)
		return {
			"labels": list(data.keys()),
			"datasets": [
				{"name": "AI Mode", "values": list(data.values())}
			]
		}

	elif chart_type == "sentiment_pie":
		filters = get_date_filters(period)
		data = get_sentiment_distribution(filters)
		return {
			"labels": list(data.keys()),
			"datasets": [
				{"name": "Sentiment", "values": list(data.values())}
			]
		}

	elif chart_type == "resolution_comparison":
		filters = get_date_filters(period)
		resolution = get_resolution_stats(filters)
		return {
			"labels": ["AI Resolved", "Human Resolved", "HITL Resolved", "Escalated"],
			"datasets": [
				{
					"name": "Resolution",
					"values": [
						resolution["ai_resolved"],
						resolution["human_resolved"],
						resolution["hitl_resolved"],
						resolution["escalated"]
					]
				}
			]
		}

	return {"labels": [], "datasets": []}
