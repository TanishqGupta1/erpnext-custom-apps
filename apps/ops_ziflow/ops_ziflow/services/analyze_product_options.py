"""Analyze Product Options."""
import frappe
from frappe.utils import cint

@frappe.whitelist()
def analyze():
    print("=" * 70)
    print("ANALYZING OPS PRODUCT OPTIONS")
    print("=" * 70)

    # Unlinked records
    unlinked = frappe.db.sql("""
        SELECT po.name, po.prod_add_opt_id, po.title, po.parent, p.product_id
        FROM `tabOPS Product Option` po
        JOIN `tabOPS Product` p ON po.parent = p.name
        WHERE po.master_option IS NULL OR po.master_option = ''
        ORDER BY p.product_id
    """, as_dict=True)

    print(f"\nUnlinked Product Options: {len(unlinked)}")
    print("\nBreakdown by product:")

    products = {}
    for u in unlinked:
        pid = u.product_id
        if pid not in products:
            products[pid] = []
        products[pid].append(u)

    for pid, opts in sorted(products.items()):
        print(f"\n   Product {pid}: {len(opts)} unlinked options")
        for opt in opts[:3]:
            print(f"      - prod_add_opt_id={opt.prod_add_opt_id}, title='{opt.title}'")

    return {"total": len(unlinked), "by_product": {k: len(v) for k, v in products.items()}}


@frappe.whitelist()
def fix_via_api():
    """Fix Product Options by fetching master_option_id from API."""
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    print("=" * 70)
    print("FIXING OPS PRODUCT OPTIONS VIA API")
    print("=" * 70)

    # Get products with unlinked options
    products = frappe.db.sql("""
        SELECT DISTINCT p.name, p.product_id
        FROM `tabOPS Product` p
        JOIN `tabOPS Product Option` po ON po.parent = p.name
        WHERE po.master_option IS NULL OR po.master_option = ''
    """, as_dict=True)

    print(f"\n   {len(products)} products with unlinked options")

    client = OnPrintShopClient()
    fixed = 0
    errors = 0

    for prod in products:
        product_id = prod.product_id
        print(f"\n   Fetching product {product_id}...")

        try:
            query = '''
            query($products_id: Int) {
                product_additional_options(products_id: $products_id, limit: 200) {
                    product_additional_options {
                        prod_add_opt_id
                        master_option_id
                    }
                }
            }
            '''

            result = client._execute_graphql(query, {'products_id': int(product_id)})
            api_options = result.get('data', {}).get('product_additional_options', {}).get('product_additional_options', [])

            # Create lookup
            api_lookup = {}
            for opt in api_options:
                if opt.get('prod_add_opt_id') and opt.get('master_option_id'):
                    api_lookup[cint(opt['prod_add_opt_id'])] = str(opt['master_option_id'])

            # Update Frappe records
            frappe_options = frappe.get_all(
                "OPS Product Option",
                filters={"parent": prod.name, "master_option": ["is", "not set"]},
                fields=["name", "prod_add_opt_id"]
            )

            for fo in frappe_options:
                opt_id = cint(fo.prod_add_opt_id)
                if opt_id in api_lookup:
                    master_name = api_lookup[opt_id]
                    if frappe.db.exists("OPS Master Option", master_name):
                        frappe.db.set_value(
                            "OPS Product Option",
                            fo.name,
                            "master_option",
                            master_name,
                            update_modified=False
                        )
                        fixed += 1
                        print(f"      Fixed: prod_add_opt_id={opt_id} -> master_option={master_name}")

            frappe.db.commit()

        except Exception as e:
            errors += 1
            print(f"      Error: {e}")

    print("\n" + "=" * 70)
    print(f"   Fixed: {fixed}")
    print(f"   Errors: {errors}")

    return {"fixed": fixed, "errors": errors}
