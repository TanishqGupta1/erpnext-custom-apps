import frappe
from frappe.model.document import Document


class KnowledgeBaseCategory(Document):
	def validate(self):
		self.validate_circular_reference()
		self.validate_priority()

	def validate_circular_reference(self):
		"""Ensure no circular reference in parent category."""
		if self.parent_category:
			if self.parent_category == self.name:
				frappe.throw("Category cannot be its own parent")

			# Check for circular reference
			parent = frappe.get_doc("Knowledge Base Category", self.parent_category)
			visited = {self.name}
			while parent.parent_category:
				if parent.parent_category in visited:
					frappe.throw("Circular reference detected in category hierarchy")
				visited.add(parent.parent_category)
				parent = frappe.get_doc("Knowledge Base Category", parent.parent_category)

	def validate_priority(self):
		"""Ensure priority is within valid range."""
		if self.priority < 1:
			self.priority = 1
		elif self.priority > 10:
			self.priority = 10
