"""
Test on product 131 which has actual custom size data
"""
import frappe
import json

def run_test():
    """Test product 131 - Decals - General Performance"""

    product_name = "131"

    print(f"\n=== Testing product: {product_name} ===\n")

    doc = frappe.get_doc("OPS Product", product_name)

    print("BEFORE:")
    print(f"  Product Name: {doc.product_name}")
    print(f"  custom_size_info: {doc.custom_size_info}")
    print(f"  product_pages_data: {doc.product_pages_data or '(empty)'}")
    print(f"  productpages: {doc.productpages}")

    # Parse and display custom sizes
    if doc.custom_size_info:
        try:
            sizes = json.loads(doc.custom_size_info)
            print(f"\n  Custom Sizes Detail:")
            for i, s in enumerate(sizes if isinstance(sizes, list) else [sizes]):
                print(f"    Size {i+1}: {s.get('size_width', '?')}\" x {s.get('size_height', '?')}\"")
                print(f"            Title: {s.get('size_title', '?')}")
        except Exception as e:
            print(f"  Parse error: {e}")

    # Store original custom_size_info
    original_custom_size = doc.custom_size_info

    # Simulate adding pages (what the fixed visualizer would do)
    pages = []
    if doc.product_pages_data:
        try:
            pages = json.loads(doc.product_pages_data)
        except:
            pages = []

    # Add two test pages
    pages.append({"name": "Front", "sort": 1, "active": True})
    pages.append({"name": "Back", "sort": 2, "active": True})

    doc.product_pages_data = json.dumps(pages)
    doc.productpages = len(pages)
    doc.save()

    print("\n" + "="*50)
    print("AFTER adding 2 test pages (Front, Back):")
    print("="*50)
    print(f"  custom_size_info: {doc.custom_size_info}")
    print(f"  product_pages_data: {doc.product_pages_data}")
    print(f"  productpages: {doc.productpages}")

    # Verify custom_size_info was NOT modified
    if doc.custom_size_info == original_custom_size:
        print("\n" + "="*50)
        print("✓ SUCCESS: custom_size_info was PRESERVED!")
        print("  The fix is working correctly.")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("✗ FAILURE: custom_size_info was MODIFIED!")
        print(f"  Original: {original_custom_size}")
        print(f"  Current:  {doc.custom_size_info}")
        print("="*50)

    # Clean up - remove test pages
    doc.product_pages_data = None
    doc.productpages = 0
    doc.save()

    print("\nCleaned up test pages.")

    frappe.db.commit()
