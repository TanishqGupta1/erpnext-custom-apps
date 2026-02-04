"""Fix all OPS master option links."""
import frappe
from frappe.utils import cint

@frappe.whitelist()
def check_order_options():
    """Check Order Product Option structure and potential matches."""
    print("=" * 60)
    print("Analyzing OPS Order Product Option Links")
    print("=" * 60)

    # Get column structure
    cols = frappe.db.sql("DESCRIBE `tabOPS Order Product Option`", as_dict=True)
    print("\nColumns in OPS Order Product Option:")
    for c in cols:
        if 'option' in c['Field'].lower() or 'master' in c['Field'].lower():
            print(f"  - {c['Field']}: {c['Type']}")

    # Sample unlinked records
    print("\nSample unlinked records:")
    samples = frappe.db.sql("""
        SELECT name, option_name, option_id, option_group, master_option
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
        LIMIT 10
    """, as_dict=True)
    for s in samples:
        print(f"  option_id={s.option_id}, name='{s.option_name}', group='{s.option_group}'")

    # Check Master Options available
    print("\nSample Master Options:")
    masters = frappe.db.sql("""
        SELECT name, master_option_id, title, option_key
        FROM `tabOPS Master Option`
        LIMIT 10
    """, as_dict=True)
    for m in masters:
        print(f"  name={m.name}, master_option_id={m.master_option_id}, title='{m.title}'")

    # Check if option_id matches any master
    print("\nChecking match potential:")
    match_by_id = frappe.db.sql("""
        SELECT COUNT(DISTINCT opo.name)
        FROM `tabOPS Order Product Option` opo
        WHERE (opo.master_option IS NULL OR opo.master_option = '')
        AND EXISTS (SELECT 1 FROM `tabOPS Master Option` mo WHERE mo.name = opo.option_id)
    """)[0][0]
    print(f"  Matchable by option_id = master.name: {match_by_id}")

    match_by_id2 = frappe.db.sql("""
        SELECT COUNT(DISTINCT opo.name)
        FROM `tabOPS Order Product Option` opo
        WHERE (opo.master_option IS NULL OR opo.master_option = '')
        AND EXISTS (SELECT 1 FROM `tabOPS Master Option` mo WHERE mo.master_option_id = opo.option_id)
    """)[0][0]
    print(f"  Matchable by option_id = master.master_option_id: {match_by_id2}")

    return {"match_by_id": match_by_id, "match_by_id2": match_by_id2}


@frappe.whitelist()
def fix_order_product_options():
    """Fix OPS Order Product Option → OPS Master Option links."""
    print("=" * 60)
    print("Fixing OPS Order Product Option → OPS Master Option Links")
    print("=" * 60)

    # Build master option lookup
    print("\n[Step 1] Building master option lookup...")
    masters = frappe.get_all(
        "OPS Master Option",
        fields=["name", "master_option_id", "option_key"],
        limit_page_length=0
    )

    # Create lookups
    lookup_by_id = {}
    lookup_by_key = {}
    for m in masters:
        lookup_by_id[cint(m.master_option_id)] = m.name
        lookup_by_id[cint(m.name) if m.name.isdigit() else 0] = m.name
        if m.option_key:
            lookup_by_key[m.option_key.lower()] = m.name

    print(f"   {len(masters)} master options loaded")
    print(f"   ID lookup: {len(lookup_by_id)} entries")
    print(f"   Key lookup: {len(lookup_by_key)} entries")

    # Get unlinked order product options
    print("\n[Step 2] Finding unlinked order product options...")
    unlinked = frappe.db.sql("""
        SELECT name, option_id, option_name, option_group
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
    """, as_dict=True)
    print(f"   Found {len(unlinked)} unlinked records")

    if not unlinked:
        print("\n[Done] No records need fixing!")
        return {"fixed": 0, "skipped": 0}

    # Fix records
    print("\n[Step 3] Fixing records...")
    fixed = 0
    skipped = 0
    batch_size = 1000

    for i, rec in enumerate(unlinked):
        master_name = None

        # Try to match by option_id
        option_id = cint(rec.option_id)
        if option_id and option_id in lookup_by_id:
            master_name = lookup_by_id[option_id]

        # Try to match by option_group (option_key)
        if not master_name and rec.option_group:
            key = rec.option_group.lower().strip()
            if key in lookup_by_key:
                master_name = lookup_by_key[key]

        if master_name:
            frappe.db.set_value(
                "OPS Order Product Option",
                rec.name,
                "master_option",
                master_name,
                update_modified=False
            )
            fixed += 1
        else:
            skipped += 1

        # Commit in batches
        if (i + 1) % batch_size == 0:
            frappe.db.commit()
            print(f"   Progress: {i + 1}/{len(unlinked)} ({fixed} fixed, {skipped} skipped)")

    frappe.db.commit()

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"   Fixed: {fixed}")
    print(f"   Skipped: {skipped}")

    return {"fixed": fixed, "skipped": skipped}


@frappe.whitelist()
def fix_product_options():
    """Fix OPS Product Option → OPS Master Option links."""
    print("=" * 60)
    print("Fixing OPS Product Option → OPS Master Option Links")
    print("=" * 60)

    # Build master option lookup
    masters = frappe.get_all(
        "OPS Master Option",
        fields=["name", "master_option_id"],
        limit_page_length=0
    )

    lookup = {}
    for m in masters:
        lookup[cint(m.master_option_id)] = m.name
        if m.name.isdigit():
            lookup[cint(m.name)] = m.name

    print(f"   {len(masters)} master options loaded")

    # Get unlinked product options
    unlinked = frappe.db.sql("""
        SELECT name, prod_add_opt_id
        FROM `tabOPS Product Option`
        WHERE master_option IS NULL OR master_option = ''
    """, as_dict=True)
    print(f"   Found {len(unlinked)} unlinked records")

    if not unlinked:
        print("\n[Done] No records need fixing!")
        return {"fixed": 0, "skipped": 0}

    # These need API call to get master_option_id
    # For now, try direct matching
    fixed = 0
    skipped = 0

    for rec in unlinked:
        opt_id = cint(rec.prod_add_opt_id)
        if opt_id in lookup:
            frappe.db.set_value(
                "OPS Product Option",
                rec.name,
                "master_option",
                lookup[opt_id],
                update_modified=False
            )
            fixed += 1
        else:
            skipped += 1

    frappe.db.commit()

    print(f"   Fixed: {fixed}")
    print(f"   Skipped: {skipped} (need API sync)")

    return {"fixed": fixed, "skipped": skipped}


@frappe.whitelist()
def fix_all():
    """Fix all master option links."""
    print("\n" + "=" * 70)
    print("FIXING ALL OPS MASTER OPTION LINKS")
    print("=" * 70)

    results = {}

    # 1. Fix Order Product Options
    print("\n>>> Fixing Order Product Options...")
    results["order_product_options"] = fix_order_product_options()

    # 2. Fix Product Options
    print("\n>>> Fixing Product Options...")
    results["product_options"] = fix_product_options()

    print("\n" + "=" * 70)
    print("ALL FIXES COMPLETE")
    print("=" * 70)

    return results


@frappe.whitelist()
def verify_all():
    """Verify all link statuses."""
    print("=" * 70)
    print("OPS LINK STATUS VERIFICATION")
    print("=" * 70)

    results = {}

    # 1. OPS Product Option → OPS Master Option
    total = frappe.db.count("OPS Product Option")
    linked = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Product Option` WHERE master_option IS NOT NULL AND master_option != ''")[0][0]
    results["product_option"] = {"total": total, "linked": linked, "pct": round(linked*100/total, 1) if total else 0}
    print(f"\n1. OPS Product Option → OPS Master Option")
    print(f"   {linked}/{total} linked ({results['product_option']['pct']}%)")

    # 2. OPS Product Attribute → OPS Master Option Attribute
    total = frappe.db.count("OPS Product Attribute")
    linked = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Product Attribute` WHERE master_attribute IS NOT NULL AND master_attribute != ''")[0][0]
    results["product_attribute"] = {"total": total, "linked": linked, "pct": round(linked*100/total, 1) if total else 0}
    print(f"\n2. OPS Product Attribute → OPS Master Option Attribute")
    print(f"   {linked}/{total} linked ({results['product_attribute']['pct']}%)")

    # 3. OPS Order Product Option → OPS Master Option
    total = frappe.db.count("OPS Order Product Option")
    linked = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Order Product Option` WHERE master_option IS NOT NULL AND master_option != ''")[0][0]
    results["order_product_option"] = {"total": total, "linked": linked, "pct": round(linked*100/total, 1) if total else 0}
    print(f"\n3. OPS Order Product Option → OPS Master Option")
    print(f"   {linked}/{total} linked ({results['order_product_option']['pct']}%)")

    print("\n" + "=" * 70)

    return results
