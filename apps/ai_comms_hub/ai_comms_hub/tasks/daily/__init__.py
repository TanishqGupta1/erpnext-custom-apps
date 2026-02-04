#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Daily scheduled tasks.

Exports:
- generate_analytics_report: Calculate and store daily metrics
- cleanup_old_conversations: Archive old resolved conversations
- sync_knowledge_base: Sync ERPNext data to Qdrant
"""

from __future__ import unicode_literals

from ai_comms_hub.tasks.daily.analytics import (
	calculate_daily_metrics,
	update_customer_metrics,
	identify_trends,
	generate_top_intents_report
)
from ai_comms_hub.tasks.daily.cleanup import (
	cleanup_old_conversations,
	cleanup_error_logs,
	cleanup_temporary_files,
	cleanup_vector_database
)


def generate_analytics_report():
	"""
	Generate daily analytics report.
	Wrapper for calculate_daily_metrics for hooks.py compatibility.
	"""
	calculate_daily_metrics()
	update_customer_metrics()
	identify_trends()
	generate_top_intents_report()


def sync_knowledge_base():
	"""
	Sync ERPNext knowledge to Qdrant vector database.
	"""
	from ai_comms_hub.api.rag import sync_erpnext_knowledge
	sync_erpnext_knowledge()


__all__ = [
	"generate_analytics_report",
	"cleanup_old_conversations",
	"sync_knowledge_base",
	"calculate_daily_metrics",
	"update_customer_metrics",
	"identify_trends",
	"cleanup_error_logs",
	"cleanup_temporary_files",
	"cleanup_vector_database"
]
