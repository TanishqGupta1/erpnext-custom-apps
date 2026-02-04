import frappe

def update_faq(name, answer):
    """Update FAQ answer"""
    doc = frappe.get_doc("Chatwoot FAQ", name)
    doc.answer = answer
    doc.sync_status = "Not Synced"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return f"Updated {name}: {doc.question[:50]}..."
