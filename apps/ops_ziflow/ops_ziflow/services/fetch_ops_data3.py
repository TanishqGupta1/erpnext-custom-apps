"""Fetch actual OPS data for analysis."""

import frappe
import json

@frappe.whitelist()
def fetch_product_options(products_id):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    query = '''
    query($products_id: Int) {
        product_additional_options(products_id: $products_id, limit: 50) {
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

    variables = {'products_id': int(products_id)}
    result = client._execute_graphql(query, variables)
    return result

@frappe.whitelist()
def fetch_product_details(products_id):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    query = '''
    query($products_id: Int) {
        products_details(products_id: $products_id) {
            product_id
            product_name
            main_sku
            default_category_id
            product_additional_options {
                prod_add_opt_id
                products_id
                title
                master_option_id
                option_key
                options_type
                attributes
            }
        }
    }
    '''

    variables = {'products_id': int(products_id)}
    result = client._execute_graphql(query, variables)
    return result
