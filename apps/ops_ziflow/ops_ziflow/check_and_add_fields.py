#!/usr/bin/env python3
"""
Check for duplicates and add missing HTML fields to OPS Order
Run with: bench --site erp.visualgraphx.com execute check_and_add_fields.execute
"""
import frappe

def execute():
    # Check for field duplicates
    duplicates = frappe.db.sql("""
        SELECT fieldname, COUNT(*) as cnt
        FROM (
            SELECT fieldname FROM `tabDocField` WHERE parent='OPS Order'
            UNION ALL
            SELECT fieldname FROM `tabCustom Field` WHERE dt='OPS Order'
        ) t
        GROUP BY fieldname
        HAVING cnt > 1
    """, as_dict=True)

    if duplicates:
        print("Found duplicate fields:")
        for d in duplicates:
            print(f"  - {d.fieldname}: {d.cnt} occurrences")

        # Delete duplicate custom fields
        for d in duplicates:
            cfs = frappe.get_all("Custom Field",
                filters={"dt": "OPS Order", "fieldname": d.fieldname})
            if cfs:
                for cf in cfs:
                    print(f"  Deleting Custom Field: {cf.name}")
                    frappe.delete_doc("Custom Field", cf.name, force=True)

    frappe.db.commit()

    # Now add the missing HTML fields
    fields = [
        {
            "doctype": "Custom Field",
            "dt": "OPS Order",
            "fieldname": "customer_panel_section",
            "fieldtype": "Section Break",
            "label": "Customer Overview",
            "insert_after": "orders_info_tab",
            "collapsible": 0
        },
        {
            "doctype": "Custom Field",
            "dt": "OPS Order",
            "fieldname": "customer_panel_html",
            "fieldtype": "HTML",
            "label": "Customer Panel",
            "insert_after": "customer_panel_section"
        },
        {
            "doctype": "Custom Field",
            "dt": "OPS Order",
            "fieldname": "order_actions_html",
            "fieldtype": "HTML",
            "label": "Quick Actions",
            "insert_after": "customer_panel_html"
        },
        {
            "doctype": "Custom Field",
            "dt": "OPS Order",
            "fieldname": "order_summary_html",
            "fieldtype": "HTML",
            "label": "Order Summary",
            "insert_after": "order_actions_html"
        }
    ]

    for field_data in fields:
        fname = field_data["fieldname"]
        existing = frappe.db.exists("Custom Field", {"dt": "OPS Order", "fieldname": fname})

        if existing:
            print(f"Field {fname} already exists, skipping")
            continue

        try:
            doc = frappe.get_doc(field_data)
            doc.insert(ignore_permissions=True)
            print(f"Added: {fname}")
        except Exception as e:
            print(f"Error adding {fname}: {e}")

    frappe.db.commit()

    # Verify
    result = frappe.get_all("Custom Field",
        filters={"dt": "OPS Order", "fieldtype": "HTML"},
        fields=["fieldname", "label"])
    print("\nHTML fields in OPS Order:")
    for r in result:
        print(f"  - {r.fieldname}: {r.label}")

    return "Done"
