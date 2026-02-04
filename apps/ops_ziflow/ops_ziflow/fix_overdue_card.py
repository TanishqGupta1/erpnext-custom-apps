# fix_overdue_card.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.fix_overdue_card.fix_card

import frappe
from frappe.utils import today
import json

def fix_card():
    """Fix Overdue ZiFlow Proofs Number Card filter"""

    card_name = "Overdue ZiFlow Proofs"

    if not frappe.db.exists('Number Card', card_name):
        print(f"Card '{card_name}' not found")
        return

    card = frappe.get_doc('Number Card', card_name)

    print(f"Current filters_json: {card.filters_json}")

    # Fix the filter - use proper Frappe date format
    # Instead of literal "Today", use the actual date or dynamic filter
    new_filters = [
        ["OPS ZiFlow Proof", "proof_status", "in", ["Draft", "In Review", "Changes Requested"]],
        ["OPS ZiFlow Proof", "deadline", "<", today()]
    ]

    card.filters_json = json.dumps(new_filters)
    card.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"Updated filters_json: {card.filters_json}")
    print("Done!")


def fix_card_dynamic():
    """Fix using dynamic date filter"""

    card_name = "Overdue ZiFlow Proofs"

    if not frappe.db.exists('Number Card', card_name):
        print(f"Card '{card_name}' not found")
        return

    card = frappe.get_doc('Number Card', card_name)

    # Use dynamic_filters_json instead for "Today" comparison
    # This allows the date to be evaluated at runtime
    card.filters_json = '[["OPS ZiFlow Proof","proof_status","in",["Draft","In Review","Changes Requested"]]]'
    card.dynamic_filters_json = '[["OPS ZiFlow Proof","deadline","<","frappe.utils.today()"]]'

    card.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"Updated card with dynamic filter")
    print(f"filters_json: {card.filters_json}")
    print(f"dynamic_filters_json: {card.dynamic_filters_json}")
    print("Done!")


if __name__ == "__main__":
    fix_card()
