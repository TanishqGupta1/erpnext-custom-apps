"""Fetch sample product from OPS API."""

import frappe
import json

@frappe.whitelist()
def fetch_product(product_id=None):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    # Query for product details with options and attributes
    query = '''
    query($product_id: Int) {
        productsDetails(product_id: $product_id) {
            product_id
            product_name
            main_sku
            default_category_id
            product_additional_options {
                prod_add_opt_id
                products_id
                title
                description
                master_option_id
                option_key
                options_type
                sort_order
                status
                attributes
            }
        }
    }
    '''

    variables = {'product_id': int(product_id) if product_id else None}
    result = client._execute_graphql(query, variables)
    data = result.get('data', {})

    # Simplify output - just show structure
    output = {'productsDetails': []}
    for prod in data.get('productsDetails', []):
        prod_info = {
            'product_id': prod.get('product_id'),
            'product_name': prod.get('product_name'),
            'options_count': len(prod.get('product_additional_options', [])),
            'sample_option': None
        }

        options = prod.get('product_additional_options', [])
        if options:
            opt = options[0]
            attrs = opt.get('attributes', [])
            prod_info['sample_option'] = {
                'prod_add_opt_id': opt.get('prod_add_opt_id'),
                'master_option_id': opt.get('master_option_id'),
                'title': opt.get('title'),
                'option_key': opt.get('option_key'),
                'attributes_count': len(attrs) if isinstance(attrs, list) else 0,
                'sample_attribute': attrs[0] if isinstance(attrs, list) and attrs else None
            }

        output['productsDetails'].append(prod_info)

    return output
