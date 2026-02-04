#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Monthly scheduled tasks.

Exports:
- archive_old_data: Archive conversations older than 6 months
- generate_monthly_report: Comprehensive monthly performance report
"""

from __future__ import unicode_literals

from ai_comms_hub.tasks.monthly.archive import (
	archive_old_conversations,
	generate_monthly_report,
	calculate_cost_metrics,
	update_knowledge_base_metrics,
	generate_compliance_report
)


def archive_old_data():
	"""
	Archive old data - wrapper for hooks.py compatibility.
	"""
	archive_old_conversations()


__all__ = [
	"archive_old_data",
	"archive_old_conversations",
	"generate_monthly_report",
	"calculate_cost_metrics",
	"update_knowledge_base_metrics",
	"generate_compliance_report"
]
