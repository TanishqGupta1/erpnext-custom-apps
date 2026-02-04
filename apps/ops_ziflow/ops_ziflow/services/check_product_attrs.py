"""Check OPS Product Attribute structure."""
import frappe

@frappe.whitelist()
def check():
    # Check parent types
    result = frappe.db.sql("""
        SELECT DISTINCT parenttype, COUNT(*) as cnt
        FROM `tabOPS Product Attribute`
        GROUP BY parenttype
    """, as_dict=True)
    print("Parent types:", result)

    # Sample records
    samples = frappe.db.sql("""
        SELECT name, parent, parenttype, attribute_id, master_attribute, label
        FROM `tabOPS Product Attribute`
        LIMIT 5
    """, as_dict=True)
    print("Samples:", samples)

    return {"parent_types": result, "samples": samples}
