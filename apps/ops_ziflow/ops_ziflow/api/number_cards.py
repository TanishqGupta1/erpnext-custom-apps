import frappe
from frappe.utils import today


@frappe.whitelist()
def get_overdue_proofs_count():
    """Get count of overdue ZiFlow proofs - deadline is before today"""
    count = frappe.db.count(
        "OPS ZiFlow Proof",
        filters={
            "proof_status": ["in", ["Draft", "In Review", "Changes Requested"]],
            "deadline": ["<", today()]
        }
    )
    return {
        "value": count,
        "fieldtype": "Int"
    }
