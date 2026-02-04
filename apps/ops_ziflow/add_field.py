#!/usr/bin/env python
import frappe

def add_html_field():
    # Check if field already exists
    if frappe.db.exists('Custom Field', {'dt': 'OPS Order', 'fieldname': 'customer_panel_html'}):
        print("customer_panel_html already exists")
        return

    # Create new custom field
    doc = frappe.new_doc('Custom Field')
    doc.dt = 'OPS Order'
    doc.fieldname = 'customer_panel_html'
    doc.fieldtype = 'HTML'
    doc.label = 'Customer Panel'
    doc.insert_after = 'order_status'
    doc.read_only = 1
    doc.flags.ignore_validate = True
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print("Created customer_panel_html field successfully")

add_html_field()
