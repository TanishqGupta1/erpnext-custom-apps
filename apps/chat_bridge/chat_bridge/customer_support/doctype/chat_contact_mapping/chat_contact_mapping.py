import frappe
from frappe.model.document import Document
from datetime import datetime

class ChatContactMapping(Document):
	"""Map ERPNext Contacts to Chat Contacts"""
	
	def validate(self):
		"""Validate mapping"""
		# Check for duplicate mappings
		existing = frappe.db.exists("Chat Contact Mapping", {
			"chat_contact_id": self.chat_contact_id,
			"chat_account_id": self.chat_account_id,
			"name": ["!=", self.name]
		})
		if existing:
			frappe.throw(f"Contact ID {self.chat_contact_id} already mapped in account {self.chat_account_id}")
		
		# Check for duplicate ERPNext contact mappings
		existing_erpnext = frappe.db.exists("Chat Contact Mapping", {
			"erpnext_contact": self.erpnext_contact,
			"name": ["!=", self.name]
		})
		if existing_erpnext:
			frappe.throw(f"ERPNext Contact {self.erpnext_contact} already has a Chat mapping")
	
	def update_last_synced(self):
		"""Update last synced timestamp"""
		self.last_synced = datetime.now()
		self.save(ignore_permissions=True)

