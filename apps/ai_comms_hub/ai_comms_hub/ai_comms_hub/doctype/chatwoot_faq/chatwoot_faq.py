# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ChatwootFAQ(Document):
    """
    Chatwoot FAQ DocType with automatic Qdrant vector sync.

    On save: Generates embedding and upserts to Qdrant "chatwoot_knowledge_v2" collection
    On delete: Removes point from Qdrant
    """

    def validate(self):
        """Validate FAQ before save."""
        self.validate_question()
        self.validate_answer()

    def validate_question(self):
        """Ensure question is not too short."""
        if len(self.question.strip()) < 10:
            frappe.throw(_("Question must be at least 10 characters long"))

    def validate_answer(self):
        """Ensure answer is not empty after stripping HTML."""
        clean_answer = frappe.utils.strip_html_tags(self.answer or "")
        if len(clean_answer.strip()) < 20:
            frappe.throw(_("Answer must be at least 20 characters long"))

    def before_save(self):
        """Mark as pending sync if content changed."""
        if self.has_value_changed("question") or self.has_value_changed("answer") or self.has_value_changed("tags") or self.has_value_changed("category"):
            self.sync_status = "Pending"
            self.sync_error = None

    @frappe.whitelist()
    def sync_now(self):
        """
        Manually trigger immediate sync (not queued).

        Returns:
            dict: Sync result
        """
        from ai_comms_hub.services.qdrant_faq_sync import sync_faq
        from frappe.utils import now_datetime

        try:
            result = sync_faq(self)

            if result.get("status") == "success":
                self.sync_status = "Synced"
                self.last_synced = now_datetime()
                self.qdrant_point_id = result.get("point_id")
                self.sync_error = ""
            else:
                self.sync_status = "Failed"
                self.sync_error = result.get("error", "Unknown error")[:500]

            self.save(ignore_permissions=True)
            return result

        except Exception as e:
            frappe.log_error(f"Manual FAQ sync failed: {str(e)}", "Chatwoot FAQ")
            return {"status": "error", "message": str(e)}
