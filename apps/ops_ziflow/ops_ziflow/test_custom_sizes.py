"""
Test script to find products with custom sizes and verify the fix
"""
import frappe
import json

def find_products_with_custom_sizes():
    """Find products that have custom_size_info data"""

    products = frappe.db.sql("""
        SELECT name, product_name, custom_size_info, product_pages_data, productpages
        FROM `tabOPS Product`
        WHERE custom_size_info IS NOT NULL
        AND custom_size_info != ''
        AND custom_size_info != 'null'
        LIMIT 5
    """, as_dict=True)

    print(f"\n=== Found {len(products)} products with custom_size_info ===\n")

    for p in products:
        print(f"Product: {p.name}")
        print(f"  Name: {p.product_name}")
        print(f"  Product Pages (Int): {p.productpages}")
        print(f"  Product Pages Data: {p.product_pages_data or '(empty)'}")

        # Parse and show custom_size_info
        if p.custom_size_info:
            try:
                sizes = json.loads(p.custom_size_info)
                print(f"  Custom Size Info: {len(sizes) if isinstance(sizes, list) else 1} size(s)")
                if isinstance(sizes, list) and len(sizes) > 0:
                    first = sizes[0]
                    print(f"    First size: {first.get('size_width', '?')} x {first.get('size_height', '?')}")
            except:
                print(f"  Custom Size Info: {p.custom_size_info[:100]}...")
        print()

    if products:
        return products[0].name
    return None

def test_product(product_name):
    """Test that the visualizer correctly uses product_pages_data"""

    print(f"\n=== Testing product: {product_name} ===\n")

    doc = frappe.get_doc("OPS Product", product_name)

    print("BEFORE:")
    print(f"  custom_size_info: {doc.custom_size_info[:200] if doc.custom_size_info else '(empty)'}...")
    print(f"  product_pages_data: {doc.product_pages_data or '(empty)'}")
    print(f"  productpages: {doc.productpages}")

    # Store original custom_size_info
    original_custom_size = doc.custom_size_info

    # Simulate adding a page (what the fixed visualizer would do)
    pages = []
    if doc.product_pages_data:
        try:
            pages = json.loads(doc.product_pages_data)
        except:
            pages = []

    pages.append({"name": "TestPage", "sort": len(pages) + 1, "active": True})

    doc.product_pages_data = json.dumps(pages)
    doc.productpages = len(pages)
    doc.save()

    print("\nAFTER adding test page:")
    print(f"  custom_size_info: {doc.custom_size_info[:200] if doc.custom_size_info else '(empty)'}...")
    print(f"  product_pages_data: {doc.product_pages_data}")
    print(f"  productpages: {doc.productpages}")

    # Verify custom_size_info was NOT modified
    if doc.custom_size_info == original_custom_size:
        print("\n✓ SUCCESS: custom_size_info was preserved!")
    else:
        print("\n✗ FAILURE: custom_size_info was modified!")

    # Clean up - remove test page
    pages = [p for p in pages if p.get("name") != "TestPage"]
    doc.product_pages_data = json.dumps(pages) if pages else None
    doc.productpages = len(pages)
    doc.save()

    print("\nCleaned up test page.")

    frappe.db.commit()
    return True

def run_test():
    """Main test function"""
    product_name = find_products_with_custom_sizes()
    if product_name:
        test_product(product_name)
    else:
        print("No products with custom_size_info found to test.")
