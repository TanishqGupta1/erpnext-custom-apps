# check_doctypes.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.check_doctypes.check_fields

import frappe

def check_fields():
    """Check key OPS DocType fields for proper linking."""

    doctypes_to_check = ['OPS Customer', 'OPS Product', 'OPS Order', 'OPS Store']

    for dt in doctypes_to_check:
        print(f"\n=== {dt} ===")
        meta = frappe.get_meta(dt)
        for field in meta.fields[:15]:  # First 15 fields
            if field.fieldtype in ['Data', 'Int', 'Link', 'Select', 'Currency', 'Float']:
                print(f"  {field.fieldname}: {field.fieldtype} ({field.label})")

if __name__ == "__main__":
    check_fields()
