"""Fix only the linkable Order Product Options."""
import frappe
from frappe.utils import cint

@frappe.whitelist()
def analyze_linkable():
    """Find records that have option_id > 0 but no master_option."""
    print("=" * 70)
    print("ANALYZING LINKABLE ORDER PRODUCT OPTIONS")
    print("=" * 70)

    # Records with option_id > 0 but no master_option
    linkable = frappe.db.sql("""
        SELECT opo.option_id, opo.option_name, COUNT(*) as cnt,
               (SELECT mo.name FROM `tabOPS Master Option` mo WHERE mo.name = opo.option_id LIMIT 1) as potential_master
        FROM `tabOPS Order Product Option` opo
        WHERE (opo.master_option IS NULL OR opo.master_option = '')
        AND opo.option_id > 0
        GROUP BY opo.option_id, opo.option_name
        ORDER BY cnt DESC
        LIMIT 20
    """, as_dict=True)

    print(f"\nRecords with option_id > 0 but no master_option link:")
    total_linkable = 0
    for l in linkable:
        print(f"   option_id={l.option_id}, name='{l.option_name}', count={l.cnt}, potential_master={l.potential_master}")
        if l.potential_master:
            total_linkable += l.cnt

    # Total count
    total_with_id = frappe.db.sql("""
        SELECT COUNT(*)
        FROM `tabOPS Order Product Option`
        WHERE (master_option IS NULL OR master_option = '')
        AND option_id > 0
    """)[0][0]

    print(f"\n   Total unlinked with option_id > 0: {total_with_id}")

    # Check actual matches
    matches = frappe.db.sql("""
        SELECT COUNT(*)
        FROM `tabOPS Order Product Option` opo
        WHERE (opo.master_option IS NULL OR opo.master_option = '')
        AND opo.option_id > 0
        AND EXISTS (SELECT 1 FROM `tabOPS Master Option` mo WHERE mo.name = opo.option_id)
    """)[0][0]

    print(f"   Actually matchable to existing masters: {matches}")

    return {"total_with_id": total_with_id, "matchable": matches}


@frappe.whitelist()
def fix_linkable():
    """Fix only the records that have option_id matching a master option."""
    print("=" * 70)
    print("FIXING LINKABLE ORDER PRODUCT OPTIONS")
    print("=" * 70)

    # Build master option lookup
    masters = frappe.get_all(
        "OPS Master Option",
        fields=["name"],
        limit_page_length=0
    )
    master_set = set(str(m.name) for m in masters)
    print(f"\n   {len(master_set)} master options loaded")

    # Get unlinked records with option_id > 0
    unlinked = frappe.db.sql("""
        SELECT name, option_id
        FROM `tabOPS Order Product Option`
        WHERE (master_option IS NULL OR master_option = '')
        AND option_id > 0
    """, as_dict=True)
    print(f"   {len(unlinked)} unlinked records with option_id > 0")

    fixed = 0
    skipped = 0

    for rec in unlinked:
        option_id_str = str(rec.option_id)
        if option_id_str in master_set:
            frappe.db.set_value(
                "OPS Order Product Option",
                rec.name,
                "master_option",
                option_id_str,
                update_modified=False
            )
            fixed += 1
        else:
            skipped += 1

    frappe.db.commit()

    print(f"\n   Fixed: {fixed}")
    print(f"   Skipped: {skipped} (no matching master option)")

    return {"fixed": fixed, "skipped": skipped}


@frappe.whitelist()
def summary():
    """Show summary of all unlinked records."""
    print("=" * 70)
    print("UNLINKED RECORDS SUMMARY")
    print("=" * 70)

    # Total unlinked
    total = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
    """)[0][0]

    # Breakdown by category
    categories = frappe.db.sql("""
        SELECT
            CASE
                WHEN option_name IN ('Height (Inch)', 'Width (Inch)') THEN 'Dimensions'
                WHEN option_name IN ('Make', 'Model', 'Year', 'Sub-Model') THEN 'Vehicle Info'
                WHEN option_name IN ('Additional Options', 'Job Name') THEN 'Custom Fields'
                WHEN option_name = 'Product Sizes' THEN 'Product Sizes'
                WHEN option_name LIKE 'AO-%' THEN 'AO Fields'
                WHEN option_id > 0 THEN 'Has option_id (fixable)'
                ELSE 'Other'
            END as category,
            COUNT(*) as cnt
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
        GROUP BY
            CASE
                WHEN option_name IN ('Height (Inch)', 'Width (Inch)') THEN 'Dimensions'
                WHEN option_name IN ('Make', 'Model', 'Year', 'Sub-Model') THEN 'Vehicle Info'
                WHEN option_name IN ('Additional Options', 'Job Name') THEN 'Custom Fields'
                WHEN option_name = 'Product Sizes' THEN 'Product Sizes'
                WHEN option_name LIKE 'AO-%' THEN 'AO Fields'
                WHEN option_id > 0 THEN 'Has option_id (fixable)'
                ELSE 'Other'
            END
        ORDER BY cnt DESC
    """, as_dict=True)

    print(f"\nTotal unlinked: {total}")
    print("\nBreakdown by category:")
    for c in categories:
        print(f"   {c.category}: {c.cnt}")

    return {"total": total, "categories": categories}
