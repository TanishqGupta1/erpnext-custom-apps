"""Check attribute ID mapping between product and master."""
import frappe

@frappe.whitelist()
def check():
    # Get sample product attributes with their attribute_id
    prod_attrs = frappe.db.sql("""
        SELECT attribute_id, label, COUNT(*) as cnt
        FROM `tabOPS Product Attribute`
        WHERE attribute_id IS NOT NULL AND attribute_id > 0
        GROUP BY attribute_id, label
        ORDER BY cnt DESC
        LIMIT 10
    """, as_dict=True)
    print("Sample Product Attributes (by attribute_id):")
    for a in prod_attrs:
        print(f"  attribute_id={a.attribute_id}, label='{a.label}', count={a.cnt}")

    # Get sample master attributes with their master_attribute_id
    master_attrs = frappe.db.sql("""
        SELECT name, master_attribute_id, label, master_option_id
        FROM `tabOPS Master Option Attribute`
        LIMIT 10
    """, as_dict=True)
    print("\nSample Master Attributes:")
    for m in master_attrs:
        print(f"  name={m.name}, master_attribute_id={m.master_attribute_id}, label='{m.label}'")

    # Check if any product attribute_id matches master_attribute_id
    matches = frappe.db.sql("""
        SELECT pa.attribute_id, pa.label as prod_label, ma.master_attribute_id, ma.label as master_label, ma.name as master_name
        FROM `tabOPS Product Attribute` pa
        JOIN `tabOPS Master Option Attribute` ma ON pa.attribute_id = ma.master_attribute_id
        LIMIT 5
    """, as_dict=True)
    print(f"\nMatches found (attribute_id = master_attribute_id): {len(matches)}")
    for m in matches:
        print(f"  attribute_id={m.attribute_id} -> master_attribute_id={m.master_attribute_id} (name={m.master_name})")

    # Count potential matches
    match_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT pa.name)
        FROM `tabOPS Product Attribute` pa
        JOIN `tabOPS Master Option Attribute` ma ON pa.attribute_id = ma.master_attribute_id
        WHERE pa.master_attribute IS NULL
    """)[0][0]
    print(f"\nTotal matchable records: {match_count}")

    return {"match_count": match_count}
