"""
Migration script to fix OPS Product Attribute → OPS Master Option Attribute links.

This script:
1. Fetches all OPS Product Attributes that have attribute_id but no master_attribute link
2. For each attribute, queries the OPS API to get the master_attribute_id
3. Updates the master_attribute link in Frappe

Run with:
    bench --site erp.visualgraphx.com execute ops_ziflow.patches.fix_product_attribute_links.run
"""

import frappe
from frappe.utils import cint


def run():
    """Main migration function."""
    print("=" * 60)
    print("OPS Product Attribute Migration - Fixing master_attribute links")
    print("=" * 60)

    # Step 1: Get all OPS Master Option Attributes for lookup
    print("\n[Step 1] Building master attribute lookup table...")
    master_attrs = frappe.get_all(
        "OPS Master Option Attribute",
        fields=["name", "master_attribute_id", "label", "attribute_key"],
        limit_page_length=0
    )

    # Create lookup by master_attribute_id
    master_lookup = {}
    for attr in master_attrs:
        # The document name should equal master_attribute_id
        master_lookup[cint(attr.master_attribute_id)] = attr.name
        # Also map by name in case it's numeric
        if attr.name.isdigit():
            master_lookup[cint(attr.name)] = attr.name

    print(f"   Found {len(master_attrs)} master attributes")
    print(f"   Lookup table has {len(master_lookup)} entries")

    # Step 2: Get all OPS Product Attributes without master_attribute link
    print("\n[Step 2] Finding product attributes without master_attribute link...")
    product_attrs = frappe.get_all(
        "OPS Product Attribute",
        filters=[
            ["master_attribute", "is", "not set"]
        ],
        fields=["name", "attribute_id", "parent", "parenttype", "label", "attribute_key"],
        limit_page_length=0
    )

    print(f"   Found {len(product_attrs)} product attributes without master_attribute link")

    if not product_attrs:
        print("\n[Done] No product attributes need fixing!")
        return {"fixed": 0, "skipped": 0, "errors": 0}

    # Step 3: Try to match using attribute_id directly (if stored)
    # The attribute_id in Product Attribute might map to master_attribute_id
    print("\n[Step 3] Attempting direct attribute_id matching...")

    fixed = 0
    skipped = 0
    errors = 0

    # Process in batches
    batch_size = 500
    total = len(product_attrs)

    for i in range(0, total, batch_size):
        batch = product_attrs[i:i + batch_size]
        print(f"\n   Processing batch {i // batch_size + 1} ({i + 1}-{min(i + batch_size, total)} of {total})...")

        for attr in batch:
            try:
                attr_id = cint(attr.attribute_id)

                # Try to find master attribute
                master_name = None

                # First, check if attribute_id exists as a master attribute
                if attr_id in master_lookup:
                    master_name = master_lookup[attr_id]

                if master_name:
                    # Update the record
                    frappe.db.set_value(
                        "OPS Product Attribute",
                        attr.name,
                        "master_attribute",
                        master_name,
                        update_modified=False
                    )
                    fixed += 1
                else:
                    skipped += 1

            except Exception as e:
                errors += 1
                if errors <= 10:  # Only log first 10 errors
                    print(f"   Error processing {attr.name}: {e}")

        # Commit after each batch
        frappe.db.commit()
        print(f"   Batch complete: {fixed} fixed, {skipped} skipped, {errors} errors so far")

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"   Fixed:   {fixed}")
    print(f"   Skipped: {skipped} (no matching master attribute)")
    print(f"   Errors:  {errors}")

    return {"fixed": fixed, "skipped": skipped, "errors": errors}


def run_with_api():
    """
    Alternative migration that fetches master_attribute_id from OPS API.
    Use this if direct matching doesn't work.

    Run with:
        bench --site erp.visualgraphx.com execute ops_ziflow.patches.fix_product_attribute_links.run_with_api
    """
    print("=" * 60)
    print("OPS Product Attribute Migration - Using API to fetch master_attribute_id")
    print("=" * 60)

    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    # Get all products that have options
    print("\n[Step 1] Getting all products with options...")
    products = frappe.db.sql("""
        SELECT DISTINCT parent as product_id
        FROM `tabOPS Product Option`
        WHERE parent IS NOT NULL
    """, as_dict=True)

    print(f"   Found {len(products)} products with options")

    client = OnPrintShopClient()
    fixed = 0
    skipped = 0
    errors = 0

    for idx, prod in enumerate(products):
        product_id = prod.product_id
        print(f"\n[{idx + 1}/{len(products)}] Processing product {product_id}...")

        try:
            # Fetch options from API
            query = '''
            query($products_id: Int) {
                product_additional_options(products_id: $products_id, limit: 100) {
                    product_additional_options {
                        prod_add_opt_id
                        master_option_id
                        attributes
                    }
                }
            }
            '''

            result = client._execute_graphql(query, {'products_id': int(product_id)})
            options = result.get('data', {}).get('product_additional_options', {}).get('product_additional_options', [])

            for opt in options:
                attrs = opt.get('attributes', [])
                if not isinstance(attrs, list):
                    continue

                for api_attr in attrs:
                    attr_id = api_attr.get('attribute_id')
                    master_attr_id = api_attr.get('master_attribute_id')

                    if not attr_id or not master_attr_id:
                        continue

                    # Find the Frappe record
                    frappe_attrs = frappe.get_all(
                        "OPS Product Attribute",
                        filters={"attribute_id": attr_id},
                        fields=["name", "master_attribute"]
                    )

                    for fa in frappe_attrs:
                        if not fa.master_attribute:
                            # Check if master attribute exists
                            master_name = str(master_attr_id)
                            if frappe.db.exists("OPS Master Option Attribute", master_name):
                                frappe.db.set_value(
                                    "OPS Product Attribute",
                                    fa.name,
                                    "master_attribute",
                                    master_name,
                                    update_modified=False
                                )
                                fixed += 1
                            else:
                                skipped += 1

            frappe.db.commit()

        except Exception as e:
            errors += 1
            print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"   Fixed:   {fixed}")
    print(f"   Skipped: {skipped}")
    print(f"   Errors:  {errors}")

    return {"fixed": fixed, "skipped": skipped, "errors": errors}


def verify():
    """
    Verify the migration results.

    Run with:
        bench --site erp.visualgraphx.com execute ops_ziflow.patches.fix_product_attribute_links.verify
    """
    total = frappe.db.count("OPS Product Attribute")
    linked = frappe.db.count("OPS Product Attribute", filters=[["master_attribute", "is", "set"]])
    not_linked = frappe.db.count("OPS Product Attribute", filters=[["master_attribute", "is", "not set"]])

    print("\nOPS Product Attribute Status:")
    print(f"   Total:      {total}")
    print(f"   Linked:     {linked} ({linked * 100 / total:.1f}%)")
    print(f"   Not Linked: {not_linked} ({not_linked * 100 / total:.1f}%)")

    return {"total": total, "linked": linked, "not_linked": not_linked}
