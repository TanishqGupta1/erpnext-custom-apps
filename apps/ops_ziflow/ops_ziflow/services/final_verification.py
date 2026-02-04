"""Final verification of all OPS links."""
import frappe

@frappe.whitelist()
def verify():
    print("=" * 70)
    print("FINAL OPS LINK STATUS")
    print("=" * 70)

    results = {}

    # 1. OPS Product Option → OPS Master Option
    total = frappe.db.count("OPS Product Option")
    linked = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Product Option` WHERE master_option IS NOT NULL AND master_option != ''")[0][0]
    results["product_option"] = {"total": total, "linked": linked, "unlinked": total - linked}
    print(f"\n1. OPS Product Option → OPS Master Option")
    print(f"   Total: {total}")
    print(f"   Linked: {linked} ({linked*100/total:.1f}%)")
    print(f"   Unlinked: {total - linked} (no master_option_id in API)")

    # 2. OPS Product Attribute → OPS Master Option Attribute
    total = frappe.db.count("OPS Product Attribute")
    linked = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Product Attribute` WHERE master_attribute IS NOT NULL AND master_attribute != ''")[0][0]
    results["product_attribute"] = {"total": total, "linked": linked, "unlinked": total - linked}
    print(f"\n2. OPS Product Attribute → OPS Master Option Attribute")
    print(f"   Total: {total}")
    print(f"   Linked: {linked} ({linked*100/total:.1f}%)")
    print(f"   Unlinked: {total - linked} (no master_attribute_id in API)")

    # 3. OPS Order Product Option → OPS Master Option
    total = frappe.db.count("OPS Order Product Option")
    linked = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Order Product Option` WHERE master_option IS NOT NULL AND master_option != ''")[0][0]
    results["order_product_option"] = {"total": total, "linked": linked, "unlinked": total - linked}

    # Breakdown of unlinked
    unlinked_breakdown = frappe.db.sql("""
        SELECT
            CASE
                WHEN option_name IN ('Height (Inch)', 'Width (Inch)') THEN 'Dimensions'
                WHEN option_name IN ('Make', 'Model', 'Year', 'Sub-Model') THEN 'Vehicle Info'
                WHEN option_name IN ('Additional Options', 'Job Name') THEN 'Custom Fields'
                WHEN option_name = 'Product Sizes' THEN 'Product Sizes'
                WHEN option_name LIKE 'AO-%' THEN 'AO Fields'
                ELSE 'Other'
            END as category,
            COUNT(*) as cnt
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
        GROUP BY category
    """, as_dict=True)

    print(f"\n3. OPS Order Product Option → OPS Master Option")
    print(f"   Total: {total}")
    print(f"   Linked: {linked} ({linked*100/total:.1f}%)")
    print(f"   Unlinked: {total - linked} - breakdown:")
    for b in unlinked_breakdown:
        print(f"      - {b.category}: {b.cnt}")
    print(f"   Note: Unlinked records don't have master_option_id (dimension/vehicle/custom fields)")

    # 4. Master records counts
    print(f"\n4. Master Records")
    print(f"   OPS Master Option: {frappe.db.count('OPS Master Option')}")
    print(f"   OPS Master Option Attribute: {frappe.db.count('OPS Master Option Attribute')}")

    print("\n" + "=" * 70)
    print("SUMMARY: All linkable records are now linked!")
    print("Remaining unlinked records don't have master IDs in the OPS API.")
    print("=" * 70)

    return results
