import frappe
from frappe.tests.utils import FrappeTestCase


class TestChatConversation(FrappeTestCase):
	def test_title_generation(self):
		doc = frappe.new_doc("Chat Conversation")
		doc.chat_conversation_id = "12345"
		doc.account_id = 1
		doc.insert(ignore_permissions=True)
		self.assertIn("12345", doc.title)
