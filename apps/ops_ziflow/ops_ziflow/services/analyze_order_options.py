"""Analyze Order Product Options in detail."""
import frappe

@frappe.whitelist()
def analyze():
    print("=" * 70)
    print("DETAILED ANALYSIS OF OPS ORDER PRODUCT OPTIONS")
    print("=" * 70)

    # 1. Distribution of option_id values
    print("\n1. Distribution of option_id values (unlinked only):")
    dist = frappe.db.sql("""
        SELECT option_id, COUNT(*) as cnt
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
        GROUP BY option_id
        ORDER BY cnt DESC
        LIMIT 10
    """, as_dict=True)
    for d in dist:
        print(f"   option_id={d.option_id}: {d.cnt} records")

    # 2. Distribution of option_name values (unlinked)
    print("\n2. Distribution of option_name values (unlinked):")
    names = frappe.db.sql("""
        SELECT option_name, COUNT(*) as cnt
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
        GROUP BY option_name
        ORDER BY cnt DESC
        LIMIT 15
    """, as_dict=True)
    for n in names:
        print(f"   '{n.option_name}': {n.cnt} records")

    # 3. Sample LINKED records (to see pattern)
    print("\n3. Sample LINKED records (showing pattern):")
    linked = frappe.db.sql("""
        SELECT option_id, option_name, option_group, master_option
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NOT NULL AND master_option != ''
        LIMIT 10
    """, as_dict=True)
    for l in linked:
        print(f"   option_id={l.option_id}, name='{l.option_name}', master_option={l.master_option}")

    # 4. Check if linked records have option_id populated
    print("\n4. Linked records option_id distribution:")
    linked_dist = frappe.db.sql("""
        SELECT
            CASE WHEN option_id > 0 THEN 'Has option_id' ELSE 'No option_id' END as status,
            COUNT(*) as cnt
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NOT NULL AND master_option != ''
        GROUP BY CASE WHEN option_id > 0 THEN 'Has option_id' ELSE 'No option_id' END
    """, as_dict=True)
    for d in linked_dist:
        print(f"   {d.status}: {d.cnt}")

    # 5. Check option_group values
    print("\n5. Option group distribution (unlinked):")
    groups = frappe.db.sql("""
        SELECT option_group, COUNT(*) as cnt
        FROM `tabOPS Order Product Option`
        WHERE master_option IS NULL OR master_option = ''
        GROUP BY option_group
        ORDER BY cnt DESC
        LIMIT 10
    """, as_dict=True)
    for g in groups:
        print(f"   group='{g.option_group}': {g.cnt} records")

    # 6. Check what master options exist for common option names
    print("\n6. Master Options that might match common names:")
    for name in ['Width', 'Height', 'Quantity', 'Size']:
        matches = frappe.db.sql("""
            SELECT name, title, option_key
            FROM `tabOPS Master Option`
            WHERE title LIKE %s OR option_key LIKE %s
            LIMIT 3
        """, (f'%{name}%', f'%{name}%'), as_dict=True)
        if matches:
            print(f"   '{name}' matches:")
            for m in matches:
                print(f"      - {m.name}: '{m.title}' (key={m.option_key})")

    return "Analysis complete"
