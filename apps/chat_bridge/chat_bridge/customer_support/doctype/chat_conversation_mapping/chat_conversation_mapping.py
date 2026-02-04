import frappe
from frappe.model.document import Document
from datetime import datetime

class ChatConversationMapping(Document):
	"""Map Chat conversations to ERPNext records"""
	
	def validate(self):
		"""Validate mapping"""
		# Ensure at least one ERPNext record is linked
		if not self.erpnext_contact and not self.erpnext_lead:
			frappe.throw("Must link to either an ERPNext Contact or Lead")
	
	def update_last_message(self, timestamp=None):
		"""Update last message timestamp"""
		self.last_message_at = timestamp or datetime.now()
		self.save(ignore_permissions=True)

