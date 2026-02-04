"""Check OPS Product structure."""
import frappe

@frappe.whitelist()
def check():
    # Describe OPS Product table
    cols = frappe.db.sql("DESCRIBE `tabOPS Product`", as_dict=True)
    print("OPS Product columns:")
    for c in cols:
        print(f"  - {c['Field']}: {c['Type']}")

    # Get sample products
    samples = frappe.db.sql("""
        SELECT name, product_id
        FROM `tabOPS Product`
        LIMIT 5
    """, as_dict=True)
    print("\nSample products:")
    for s in samples:
        print(f"  name={s.name}, product_id={s.product_id}")

    return {"cols": [c['Field'] for c in cols], "samples": samples}
