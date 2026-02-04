"""Check unlinked OPS Product Attributes."""
import frappe

@frappe.whitelist()
def check():
    # Get unlinked attributes grouped by product
    unlinked = frappe.db.sql("""
        SELECT
            p.name as product_name,
            p.product_id,
            COUNT(*) as unlinked_count
        FROM `tabOPS Product` p
        JOIN `tabOPS Product Option` po ON po.parent = p.name
        JOIN `tabOPS Product Attribute` pa ON pa.parent = po.name
        WHERE pa.master_attribute IS NULL
        GROUP BY p.name, p.product_id
        ORDER BY unlinked_count DESC
        LIMIT 10
    """, as_dict=True)

    print("\nProducts with unlinked attributes:")
    for u in unlinked:
        print(f"  Product {u.product_id}: {u.unlinked_count} unlinked")

    # Sample unlinked attributes
    samples = frappe.db.sql("""
        SELECT pa.attribute_id, pa.label, pa.attribute_key
        FROM `tabOPS Product Attribute` pa
        WHERE pa.master_attribute IS NULL
        LIMIT 10
    """, as_dict=True)

    print("\nSample unlinked attributes:")
    for s in samples:
        print(f"  attribute_id={s.attribute_id}, label='{s.label}'")

    return {"unlinked_by_product": unlinked, "samples": samples}
