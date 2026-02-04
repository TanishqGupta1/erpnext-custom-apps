# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CommunicationAnalytics(Document):
	def validate(self):
		"""Validate analytics record"""
		# Ensure date is unique
		if self.is_new():
			existing = frappe.db.exists(
				"Communication Analytics",
				{"date": self.date, "name": ["!=", self.name]}
			)
			if existing:
				frappe.throw(f"Analytics record already exists for {self.date}")

	def before_save(self):
		"""Calculate derived metrics before saving"""
		# Calculate resolution rate if not set
		if self.total_conversations and self.total_conversations > 0:
			if self.ai_resolved is not None and not self.ai_resolution_rate:
				self.ai_resolution_rate = (self.ai_resolved / self.total_conversations) * 100

			if self.escalated is not None and not self.escalation_rate:
				self.escalation_rate = (self.escalated / self.total_conversations) * 100


@frappe.whitelist()
def get_analytics_summary(days=30):
	"""
	Get analytics summary for dashboard.

	Args:
		days (int): Number of days to include

	Returns:
		dict: Summary metrics
	"""
	from datetime import datetime, timedelta

	cutoff_date = datetime.now() - timedelta(days=int(days))

	analytics = frappe.get_all(
		"Communication Analytics",
		filters={"date": [">=", cutoff_date.date()]},
		fields=[
			"date", "total_conversations", "ai_resolved",
			"escalated", "ai_resolution_rate", "escalation_rate",
			"avg_resolution_time"
		],
		order_by="date asc"
	)

	if not analytics:
		return {
			"total_conversations": 0,
			"avg_ai_resolution_rate": 0,
			"avg_escalation_rate": 0,
			"trend": "stable"
		}

	total = sum(a.total_conversations for a in analytics)
	avg_resolution = sum(a.ai_resolution_rate or 0 for a in analytics) / len(analytics)
	avg_escalation = sum(a.escalation_rate or 0 for a in analytics) / len(analytics)

	# Calculate trend
	if len(analytics) >= 7:
		recent = sum(a.total_conversations for a in analytics[-7:])
		previous = sum(a.total_conversations for a in analytics[-14:-7]) if len(analytics) >= 14 else recent
		trend = "increasing" if recent > previous * 1.1 else "decreasing" if recent < previous * 0.9 else "stable"
	else:
		trend = "stable"

	return {
		"total_conversations": total,
		"avg_ai_resolution_rate": round(avg_resolution, 1),
		"avg_escalation_rate": round(avg_escalation, 1),
		"avg_resolution_time": round(sum(a.avg_resolution_time or 0 for a in analytics) / len(analytics), 1),
		"trend": trend,
		"daily_data": analytics
	}
