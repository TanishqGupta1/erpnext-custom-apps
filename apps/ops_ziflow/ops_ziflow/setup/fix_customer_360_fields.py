# Copyright (c) 2024, Visual Graphx and contributors
# Script to fix Customer 360 View custom fields positioning

import frappe


def fix_fields():
    """Fix the insert_after position for Customer 360 fields."""

    # The customer_360_tab should be inserted after the last field (disabled)
    # This will create a new tab at the end of the form

    fields_to_fix = [
        ("customer_360_tab", "disabled"),  # After the last field
        ("orders_section", "customer_360_tab"),
        ("customer_orders_html", "orders_section"),
        ("proofs_section", "customer_orders_html"),
        ("customer_proofs_html", "proofs_section"),
        ("timeline_section", "customer_proofs_html"),
        ("customer_timeline_html", "timeline_section"),
    ]

    for fieldname, insert_after in fields_to_fix:
        cf_name = frappe.db.get_value("Custom Field", {"dt": "Customer", "fieldname": fieldname})
        if cf_name:
            frappe.db.set_value("Custom Field", cf_name, "insert_after", insert_after)
            print(f"Updated {fieldname} -> insert_after: {insert_after}")
        else:
            print(f"Field {fieldname} not found!")

    frappe.db.commit()

    # Clear cache to apply changes
    frappe.clear_cache(doctype="Customer")

    print("\nDone! Please reload the Customer form.")


if __name__ == "__main__":
    fix_fields()
