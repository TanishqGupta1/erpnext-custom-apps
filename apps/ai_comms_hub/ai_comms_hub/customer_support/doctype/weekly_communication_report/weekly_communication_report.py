# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WeeklyCommunicationReport(Document):
	def validate(self):
		"""Validate weekly report"""
		if self.week_end and self.week_start and self.week_end < self.week_start:
			frappe.throw("Week end date cannot be before week start date")
