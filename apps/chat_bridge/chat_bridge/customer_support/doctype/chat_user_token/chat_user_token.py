import frappe
from frappe.model.document import Document
from datetime import datetime

class ChatUserToken(Document):
	"""Store Chat API tokens per ERPNext user"""
	
	def validate(self):
		"""Validate token data"""
		if self.user and self.api_access_token:
			# Check if another token exists for this user
			existing = frappe.get_all(
				"Chat User Token",
				filters={
					"user": self.user,
					"name": ["!=", self.name]
				},
				fields=["name"],
				limit=1,
				ignore_permissions=True
			)
			if existing:
				frappe.throw(f"User {self.user} already has a Chat token configured")
	
	def update_last_sync(self):
		"""Update last sync timestamp"""
		self.last_sync = datetime.now()
		self.save(ignore_permissions=True)


def has_permission(doc, ptype, user):
	"""
	Custom permission check: Users can read/write their own tokens
	System Managers can access all tokens
	"""
	# System Managers have full access
	if "System Manager" in frappe.get_roles(user):
		return True

	# Users can access their own token
	if doc and doc.user == user and ptype in ["read", "write"]:
		return True

	return False

