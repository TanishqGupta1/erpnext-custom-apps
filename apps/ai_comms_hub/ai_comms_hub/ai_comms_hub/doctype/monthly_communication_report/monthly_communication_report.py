# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MonthlyCommunicationReport(Document):
	def validate(self):
		"""Validate monthly report"""
		if self.month and (self.month < 1 or self.month > 12):
			frappe.throw("Month must be between 1 and 12")

		if self.year and self.year < 2000:
			frappe.throw("Invalid year")
