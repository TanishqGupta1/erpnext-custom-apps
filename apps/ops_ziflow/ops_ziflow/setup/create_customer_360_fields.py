# Copyright (c) 2024, Visual Graphx and contributors
# For license information, please see license.txt

"""
Script to create Customer 360 View custom fields on Customer doctype.
Run via: bench execute ops_ziflow.setup.create_customer_360_fields.create_fields
"""

import frappe


def create_fields():
    """Create custom fields for Customer 360 View on Customer doctype."""

    custom_fields = [
        {
            "dt": "Customer",
            "fieldname": "customer_360_tab",
            "label": "Customer 360",
            "fieldtype": "Tab Break",
            "insert_after": "default_receivable_account",  # After Accounting tab fields
            "module": "OPS Integration"
        },
        {
            "dt": "Customer",
            "fieldname": "orders_section",
            "label": "Recent Orders",
            "fieldtype": "Section Break",
            "insert_after": "customer_360_tab",
            "collapsible": 0,
            "module": "OPS Integration"
        },
        {
            "dt": "Customer",
            "fieldname": "customer_orders_html",
            "label": "",
            "fieldtype": "HTML",
            "insert_after": "orders_section",
            "options": "<div class='orders-placeholder text-muted'>Orders will load here...</div>",
            "module": "OPS Integration"
        },
        {
            "dt": "Customer",
            "fieldname": "proofs_section",
            "label": "ZiFlow Proofs",
            "fieldtype": "Section Break",
            "insert_after": "customer_orders_html",
            "collapsible": 0,
            "module": "OPS Integration"
        },
        {
            "dt": "Customer",
            "fieldname": "customer_proofs_html",
            "label": "",
            "fieldtype": "HTML",
            "insert_after": "proofs_section",
            "options": "<div class='proofs-placeholder text-muted'>Proofs will load here...</div>",
            "module": "OPS Integration"
        },
        {
            "dt": "Customer",
            "fieldname": "timeline_section",
            "label": "Unified Timeline",
            "fieldtype": "Section Break",
            "insert_after": "customer_proofs_html",
            "collapsible": 0,
            "module": "OPS Integration"
        },
        {
            "dt": "Customer",
            "fieldname": "customer_timeline_html",
            "label": "",
            "fieldtype": "HTML",
            "insert_after": "timeline_section",
            "options": "<div class='timeline-placeholder text-muted'>Timeline will load here...</div>",
            "module": "OPS Integration"
        },
    ]

    for field_def in custom_fields:
        fieldname = field_def["fieldname"]
        dt = field_def["dt"]

        # Check if field already exists
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
            print(f"Custom Field '{fieldname}' already exists on '{dt}', updating...")
            doc = frappe.get_doc("Custom Field", {"dt": dt, "fieldname": fieldname})
            for key, value in field_def.items():
                if key not in ["dt", "fieldname"]:
                    setattr(doc, key, value)
            doc.save()
        else:
            print(f"Creating Custom Field '{fieldname}' on '{dt}'...")
            doc = frappe.get_doc({
                "doctype": "Custom Field",
                **field_def
            })
            doc.insert()

    frappe.db.commit()
    print("\n✅ Customer 360 View fields created successfully!")
    print("Please rebuild assets: bench build --app ops_ziflow")
    print("Then reload the Customer form to see the new tabs.")


def remove_fields():
    """Remove Customer 360 View custom fields if needed."""

    fieldnames = [
        "customer_360_tab",
        "orders_section",
        "customer_orders_html",
        "proofs_section",
        "customer_proofs_html",
        "timeline_section",
        "customer_timeline_html"
    ]

    for fieldname in fieldnames:
        if frappe.db.exists("Custom Field", {"dt": "Customer", "fieldname": fieldname}):
            print(f"Removing Custom Field '{fieldname}'...")
            frappe.delete_doc("Custom Field", {"dt": "Customer", "fieldname": fieldname})

    frappe.db.commit()
    print("\n✅ Customer 360 View fields removed.")


if __name__ == "__main__":
    create_fields()
