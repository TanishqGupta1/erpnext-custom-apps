# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AICommunicationsHubSettings(Document):
	"""Settings for AI Communications Hub"""

	def validate(self):
		"""Validate settings before save"""
		# Validate LLM settings
		if not self.llm_api_key:
			frappe.msgprint("LLM API Key is required for AI functionality", indicator="orange")

		# Validate Qdrant settings
		if not self.qdrant_url:
			frappe.msgprint("Qdrant URL is required for knowledge base", indicator="orange")

		# Validate autonomy level
		if self.ai_autonomy_level < 0 or self.ai_autonomy_level > 100:
			frappe.throw("Autonomy level must be between 0 and 100")

		# Validate RAG threshold
		if self.rag_confidence_threshold < 0 or self.rag_confidence_threshold > 100:
			frappe.throw("RAG confidence threshold must be between 0 and 100")
