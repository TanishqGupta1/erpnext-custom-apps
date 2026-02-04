"""Check for Ziflow links in products."""

import frappe

@frappe.whitelist()
def check_ziflow():
    result = frappe.db.sql("""
        SELECT parent, products_title, ziflow_proof_url
        FROM `tabOPS Order Product`
        WHERE ziflow_proof_url IS NOT NULL AND ziflow_proof_url != ''
        LIMIT 5
    """, as_dict=True)
    return result
