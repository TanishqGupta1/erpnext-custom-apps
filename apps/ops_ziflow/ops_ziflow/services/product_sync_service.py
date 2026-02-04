"""Product Catalog Sync Service.

Syncs OPS Product catalog including:
- Products with their options and attributes
- Links to master options and master attributes

Run full sync:
    bench --site erp.visualgraphx.com execute ops_ziflow.services.product_sync_service.sync_all_products

Sync single product:
    bench --site erp.visualgraphx.com execute ops_ziflow.services.product_sync_service.sync_product --args="[140]"
"""

import json
import traceback
from typing import Dict, List, Optional, Any

import frappe
from frappe.utils import cint, flt, now_datetime


def _log_ops_error(
    error_title: str,
    error_message: str,
    error_type: str = "Sync Error",
    severity: str = "Medium",
    source_doctype: str = None,
    source_document: str = None,
    service_name: str = "product_sync_service",
    function_name: str = None,
    request_data: str = None,
    response_data: str = None,
    auto_retry: bool = False,
):
    """Log error to OPS Error Log."""
    try:
        from ops_ziflow.ops_integration.doctype.ops_error_log.ops_error_log import log_error
        log_error(
            error_title=error_title,
            error_message=error_message,
            error_type=error_type,
            severity=severity,
            source_doctype=source_doctype,
            source_document=source_document,
            service_name=service_name,
            function_name=function_name,
            traceback=traceback.format_exc(),
            request_data=request_data,
            response_data=response_data,
            auto_retry=auto_retry,
        )
    except Exception:
        frappe.log_error(f"{error_title}: {error_message}", "OPS Product Sync Error")


def get_product_options_from_api(product_id: int) -> List[Dict]:
    """Fetch product additional options from OPS API.

    Args:
        product_id: The OPS product ID

    Returns:
        List of product options with their attributes
    """
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    query = '''
    query($products_id: Int) {
        product_additional_options(products_id: $products_id, limit: 200) {
            product_additional_options {
                prod_add_opt_id
                products_id
                title
                master_option_id
                option_key
                options_type
                sort_order
                status
                attributes
            }
            total_product_additional_options
        }
    }
    '''

    result = client._execute_graphql(query, {'products_id': int(product_id)})
    return result.get('data', {}).get('product_additional_options', {}).get('product_additional_options', [])


@frappe.whitelist()
def sync_product(product_id: int, update_product: bool = False) -> Dict[str, Any]:
    """Sync a single product's options and attributes from OPS API.

    Args:
        product_id: The OPS product ID
        update_product: If True, also update the OPS Product document

    Returns:
        Sync result with counts
    """
    result = {
        "product_id": product_id,
        "options_synced": 0,
        "attributes_synced": 0,
        "master_links_created": 0,
        "errors": []
    }

    # Check if product exists in Frappe
    product_name = str(product_id)
    if not frappe.db.exists("OPS Product", product_name):
        result["errors"].append(f"OPS Product {product_name} not found in Frappe")
        return result

    try:
        # Fetch options from API
        api_options = get_product_options_from_api(product_id)

        for api_opt in api_options:
            prod_add_opt_id = api_opt.get('prod_add_opt_id')
            master_option_id = api_opt.get('master_option_id')

            if not prod_add_opt_id:
                continue

            # Find or create OPS Product Option
            option_name = frappe.db.get_value(
                "OPS Product Option",
                {"prod_add_opt_id": prod_add_opt_id, "parent": product_name},
                "name"
            )

            if option_name:
                # Update master_option link if missing
                current_master = frappe.db.get_value("OPS Product Option", option_name, "master_option")
                if not current_master and master_option_id:
                    master_option_name = str(master_option_id)
                    if frappe.db.exists("OPS Master Option", master_option_name):
                        frappe.db.set_value(
                            "OPS Product Option",
                            option_name,
                            "master_option",
                            master_option_name,
                            update_modified=False
                        )
                        result["master_links_created"] += 1

                result["options_synced"] += 1

            # Process attributes
            attrs = api_opt.get('attributes', [])
            if not isinstance(attrs, list):
                continue

            for api_attr in attrs:
                attr_id = api_attr.get('attribute_id')
                master_attr_id = api_attr.get('master_attribute_id')

                if not attr_id:
                    continue

                # Find OPS Product Attribute by attribute_id
                # Attributes are children of OPS Product Option
                frappe_attrs = frappe.db.sql("""
                    SELECT pa.name, pa.master_attribute
                    FROM `tabOPS Product Attribute` pa
                    JOIN `tabOPS Product Option` po ON pa.parent = po.name
                    WHERE pa.attribute_id = %s AND po.parent = %s
                """, (attr_id, product_name), as_dict=True)

                for fa in frappe_attrs:
                    if not fa.master_attribute and master_attr_id:
                        master_attr_name = str(master_attr_id)
                        if frappe.db.exists("OPS Master Option Attribute", master_attr_name):
                            frappe.db.set_value(
                                "OPS Product Attribute",
                                fa.name,
                                "master_attribute",
                                master_attr_name,
                                update_modified=False
                            )
                            result["master_links_created"] += 1

                    result["attributes_synced"] += 1

        frappe.db.commit()

    except Exception as e:
        result["errors"].append(str(e))
        _log_ops_error(
            error_title=f"Failed to sync product {product_id}",
            error_message=str(e),
            error_type="Sync Error",
            severity="High",
            source_doctype="OPS Product",
            source_document=product_name,
            function_name="sync_product",
        )

    return result


@frappe.whitelist()
def sync_all_products(batch_size: int = 10) -> Dict[str, Any]:
    """Sync all products that have options needing master_attribute links.

    Args:
        batch_size: Number of products to process per batch

    Returns:
        Overall sync result
    """
    print("=" * 60)
    print("OPS Product Catalog Sync - Linking master attributes")
    print("=" * 60)

    # Get all products that have options with unlinked attributes
    products = frappe.db.sql("""
        SELECT DISTINCT p.name as product_name, p.product_id
        FROM `tabOPS Product` p
        JOIN `tabOPS Product Option` po ON po.parent = p.name
        JOIN `tabOPS Product Attribute` pa ON pa.parent = po.name
        WHERE pa.master_attribute IS NULL
        ORDER BY p.product_id
    """, as_dict=True)

    print(f"\nFound {len(products)} products with unlinked attributes")

    result = {
        "total_products": len(products),
        "products_synced": 0,
        "total_master_links": 0,
        "errors": []
    }

    for idx, prod in enumerate(products):
        product_id = prod.product_id or prod.product_name
        print(f"\n[{idx + 1}/{len(products)}] Syncing product {product_id}...")

        try:
            sync_result = sync_product(int(product_id))
            result["products_synced"] += 1
            result["total_master_links"] += sync_result.get("master_links_created", 0)

            if sync_result.get("errors"):
                result["errors"].extend(sync_result["errors"])

            print(f"   Links created: {sync_result.get('master_links_created', 0)}")

        except Exception as e:
            result["errors"].append(f"Product {product_id}: {str(e)}")
            print(f"   Error: {e}")

        # Commit after each batch
        if (idx + 1) % batch_size == 0:
            frappe.db.commit()
            print(f"   Batch committed ({idx + 1} products processed)")

    frappe.db.commit()

    print("\n" + "=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"   Products synced: {result['products_synced']}/{result['total_products']}")
    print(f"   Master links created: {result['total_master_links']}")
    print(f"   Errors: {len(result['errors'])}")

    return result


@frappe.whitelist()
def fix_all_attribute_links() -> Dict[str, Any]:
    """Fix all OPS Product Attribute → OPS Master Option Attribute links.

    This function fetches master_attribute_id from the API for each product
    and updates the master_attribute links in bulk.

    Run with:
        bench --site erp.visualgraphx.com execute ops_ziflow.services.product_sync_service.fix_all_attribute_links
    """
    return sync_all_products()


def update_product_option_with_attributes(
    product_doc,
    option_data: Dict,
    master_lookup: Dict[int, str]
) -> tuple:
    """Update or create a product option with its attributes.

    Args:
        product_doc: The OPS Product document
        option_data: Option data from API
        master_lookup: Dict mapping master_attribute_id to OPS Master Option Attribute name

    Returns:
        Tuple of (options_updated, attributes_updated)
    """
    options_updated = 0
    attributes_updated = 0

    prod_add_opt_id = option_data.get('prod_add_opt_id')
    master_option_id = option_data.get('master_option_id')

    if not prod_add_opt_id:
        return options_updated, attributes_updated

    # Find existing option or create new
    existing_option = None
    for opt in product_doc.get('product_options', []):
        if cint(opt.prod_add_opt_id) == cint(prod_add_opt_id):
            existing_option = opt
            break

    if existing_option:
        # Update master_option link if missing
        if not existing_option.master_option and master_option_id:
            master_option_name = str(master_option_id)
            if frappe.db.exists("OPS Master Option", master_option_name):
                existing_option.master_option = master_option_name
                options_updated += 1

        option_doc = existing_option
    else:
        # Create new option
        option_doc = product_doc.append('product_options', {
            'prod_add_opt_id': prod_add_opt_id,
            'master_option': str(master_option_id) if master_option_id else None,
            'title': option_data.get('title', ''),
            'options_type': option_data.get('options_type', ''),
            'sort_order': cint(option_data.get('sort_order', 0)),
            'status': option_data.get('status', '1'),
        })
        options_updated += 1

    # Process attributes
    attrs = option_data.get('attributes', [])
    if not isinstance(attrs, list):
        return options_updated, attributes_updated

    for api_attr in attrs:
        attr_id = api_attr.get('attribute_id')
        master_attr_id = api_attr.get('master_attribute_id')

        if not attr_id:
            continue

        # Find existing attribute
        existing_attr = None
        for attr in option_doc.get('product_attributes', []):
            if cint(attr.attribute_id) == cint(attr_id):
                existing_attr = attr
                break

        if existing_attr:
            # Update master_attribute link if missing
            if not existing_attr.master_attribute and master_attr_id:
                master_name = master_lookup.get(cint(master_attr_id)) or str(master_attr_id)
                if frappe.db.exists("OPS Master Option Attribute", master_name):
                    existing_attr.master_attribute = master_name
                    attributes_updated += 1
        else:
            # Create new attribute
            master_name = master_lookup.get(cint(master_attr_id)) or str(master_attr_id) if master_attr_id else None
            option_doc.append('product_attributes', {
                'attribute_id': attr_id,
                'master_attribute': master_name if master_name and frappe.db.exists("OPS Master Option Attribute", master_name) else None,
                'attribute_key': api_attr.get('attribute_key', ''),
                'label': api_attr.get('label', ''),
                'default_attribute': api_attr.get('default_attribute', '0'),
                'sort_order': cint(api_attr.get('sort_order', 0)),
                'status': api_attr.get('status', '1'),
                'multiplier': flt(api_attr.get('multiplier', 0)),
                'setup_cost': flt(api_attr.get('setup_cost', 0)),
            })
            attributes_updated += 1

    return options_updated, attributes_updated
