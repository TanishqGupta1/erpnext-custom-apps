import frappe
from frappe.model.document import Document


class ChatConversation(Document):
	"""Container DocType that mirrors a Chat conversation thread inside ERPNext.

	The document itself stores only metadata (status, assignment, preview, etc.).
	Individual messages belong in the Communication timeline so we inherit ERPNext's
	native messaging UI, permissions, and theming for both light and dark modes.
	"""

	def before_insert(self):
		# Guard rails so data coming from background sync can't accidentally create duplicates
		if not self.chat_conversation_id:
			frappe.throw("Chat Conversation ID is required.")

	def validate(self):
		# Ensure document title stays meaningful in list views/timelines
		self.title = self.get_title()

	def get_title(self):
		contact = self.contact or self.lead or ""
		if contact:
			return f"{contact} ({self.chat_conversation_id})"
		return f"Conversation {self.chat_conversation_id}"
