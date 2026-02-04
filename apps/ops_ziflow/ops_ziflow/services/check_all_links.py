"""Check all OPS link statuses."""
import frappe

@frappe.whitelist()
def check():
    print("=" * 70)
    print("OPS DATA INTEGRITY CHECK")
    print("=" * 70)

    # 1. OPS Product Option → OPS Master Option
    print("\n1. OPS Product Option → OPS Master Option")
    total_po = frappe.db.count("OPS Product Option")
    linked_po = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Product Option` WHERE master_option IS NOT NULL AND master_option != ''")[0][0]
    print(f"   Total: {total_po}")
    print(f"   Linked: {linked_po} ({linked_po*100/total_po:.1f}%)" if total_po else "   No records")
    print(f"   Unlinked: {total_po - linked_po}")

    # 2. OPS Product Attribute → OPS Master Option Attribute
    print("\n2. OPS Product Attribute → OPS Master Option Attribute")
    total_pa = frappe.db.count("OPS Product Attribute")
    linked_pa = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Product Attribute` WHERE master_attribute IS NOT NULL AND master_attribute != ''")[0][0]
    print(f"   Total: {total_pa}")
    print(f"   Linked: {linked_pa} ({linked_pa*100/total_pa:.1f}%)" if total_pa else "   No records")
    print(f"   Unlinked: {total_pa - linked_pa}")

    # 3. OPS Order Product Option → OPS Master Option
    print("\n3. OPS Order Product Option → OPS Master Option")
    total_opo = frappe.db.count("OPS Order Product Option")
    linked_opo = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Order Product Option` WHERE master_option IS NOT NULL AND master_option != ''")[0][0]
    print(f"   Total: {total_opo}")
    print(f"   Linked: {linked_opo} ({linked_opo*100/total_opo:.1f}%)" if total_opo else "   No records")
    print(f"   Unlinked: {total_opo - linked_opo}")

    # 4. OPS Quote Product Option → OPS Master Option
    print("\n4. OPS Quote Product Option → OPS Master Option")
    total_qpo = frappe.db.count("OPS Quote Product Option")
    if total_qpo:
        linked_qpo = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Quote Product Option` WHERE master_option IS NOT NULL AND master_option != ''")[0][0]
        print(f"   Total: {total_qpo}")
        print(f"   Linked: {linked_qpo} ({linked_qpo*100/total_qpo:.1f}%)")
        print(f"   Unlinked: {total_qpo - linked_qpo}")
    else:
        print("   No records")

    # 5. OPS Master Option Attribute (standalone check)
    print("\n5. OPS Master Option Attribute Records")
    total_moa = frappe.db.count("OPS Master Option Attribute")
    print(f"   Total: {total_moa}")

    # 6. OPS Master Option Records
    print("\n6. OPS Master Option Records")
    total_mo = frappe.db.count("OPS Master Option")
    print(f"   Total: {total_mo}")

    # 7. Sample unlinked Order Product Options
    print("\n7. Sample Unlinked Order Product Options:")
    samples = frappe.db.sql("""
        SELECT name, option_name, option_id, master_option, parent
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
        LIMIT 5
    """, as_dict=True)
    for s in samples:
        print(f"   option_id={s.option_id}, name='{s.option_name}', master_option={s.master_option}")

    # 8. Check if option_id maps to master_option_id
    print("\n8. Checking potential matches for Order Product Options:")
    match_count = frappe.db.sql("""
        SELECT COUNT(*)
        FROM `tabOPS Order Product Option` opo
        JOIN `tabOPS Master Option` mo ON opo.option_id = mo.name
        WHERE (opo.master_option IS NULL OR opo.master_option = '')
    """)[0][0]
    print(f"   Matchable by option_id: {match_count}")

    print("\n" + "=" * 70)

    return {
        "product_option": {"total": total_po, "linked": linked_po},
        "product_attribute": {"total": total_pa, "linked": linked_pa},
        "order_product_option": {"total": total_opo, "linked": linked_opo},
        "master_option_attribute": total_moa,
        "master_option": total_mo
    }
