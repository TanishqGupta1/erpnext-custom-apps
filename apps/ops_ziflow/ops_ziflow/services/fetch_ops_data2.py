"""Fetch actual OPS data for analysis."""

import frappe
import json

@frappe.whitelist()
def fetch_master_options(limit=5, master_option_id=None):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    query = '''
    query($limit: Int, $master_option_id: Int) {
        product_master_options(limit: $limit, master_option_id: $master_option_id) {
            product_master_options {
                master_option_id
                title
                option_key
                options_type
                status
                pricing_method
                attributes
            }
            total_product_master_options
        }
    }
    '''

    variables = {'limit': int(limit)}
    if master_option_id:
        variables['master_option_id'] = int(master_option_id)

    result = client._execute_graphql(query, variables)

    # Simplify output
    data = result.get('data', {}).get('product_master_options', {})
    options = data.get('product_master_options', [])

    output = {
        'total': data.get('total_product_master_options'),
        'options': []
    }

    for opt in options[:limit]:
        attrs = opt.get('attributes', [])
        output['options'].append({
            'master_option_id': opt.get('master_option_id'),
            'title': opt.get('title'),
            'option_key': opt.get('option_key'),
            'options_type': opt.get('options_type'),
            'attributes_count': len(attrs) if isinstance(attrs, list) else 0,
            'sample_attribute': attrs[0] if isinstance(attrs, list) and attrs else None
        })

    return output

@frappe.whitelist()
def fetch_product_options(products_id):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    query = '''
    query($products_id: Int) {
        product_additional_options(products_id: $products_id) {
            productAdditionalOptions {
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
            totalProductAdditionalOptions
        }
    }
    '''

    variables = {'products_id': int(products_id)}
    result = client._execute_graphql(query, variables)

    # Simplify output
    data = result.get('data', {}).get('product_additional_options', {})
    options = data.get('productAdditionalOptions', [])

    output = {
        'products_id': products_id,
        'total': data.get('totalProductAdditionalOptions'),
        'options': []
    }

    for opt in options:
        attrs = opt.get('attributes', [])
        output['options'].append({
            'prod_add_opt_id': opt.get('prod_add_opt_id'),
            'master_option_id': opt.get('master_option_id'),
            'title': opt.get('title'),
            'option_key': opt.get('option_key'),
            'attributes_count': len(attrs) if isinstance(attrs, list) else 0,
            'sample_attribute': attrs[0] if isinstance(attrs, list) and attrs else None
        })

    return output
