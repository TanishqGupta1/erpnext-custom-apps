"""Test product options sort order"""
import frappe

def run_test():
    # Find a product with options
    products_with_options = frappe.db.sql("""
        SELECT DISTINCT parent
        FROM `tabOPS Product Option`
        LIMIT 1
    """, as_dict=True)

    if not products_with_options:
        print("No products with options found")
        return

    product_name = products_with_options[0].parent
    print(f"\n=== Product: {product_name} ===\n")

    # Get options with sort_order
    options = frappe.db.sql("""
        SELECT name, title, sort_order, idx
        FROM `tabOPS Product Option`
        WHERE parent = %s
        ORDER BY idx
        LIMIT 15
    """, (product_name,), as_dict=True)

    print("Current order (by idx):")
    print("-" * 60)
    for opt in options:
        print(f"  idx={opt.idx}, sort_order={opt.sort_order}, title={opt.title[:40] if opt.title else 'N/A'}")

    print("\n" + "-" * 60)
    print("Expected order (by sort_order):")
    print("-" * 60)
    sorted_options = sorted(options, key=lambda x: int(x.sort_order or 0))
    for i, opt in enumerate(sorted_options, 1):
        print(f"  #{i}, sort_order={opt.sort_order}, title={opt.title[:40] if opt.title else 'N/A'}")

    print("\n✓ Client Script will sort the table by sort_order on form load")
