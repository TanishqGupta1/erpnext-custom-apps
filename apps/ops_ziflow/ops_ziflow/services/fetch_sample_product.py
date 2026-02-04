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
            product_size {
                size_id
                products_id
                size_name
                width
                height
            }
        }
    }
    '''

    variables = {'product_id': int(product_id) if product_id else None}
    result = client._execute_graphql(query, variables)
    return result.get('data', {})

@frappe.whitelist()
def fetch_master_option(option_id=None):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    # Query for master option with attributes
    query = '''
    query($master_option_id: Int) {
        getMasterOption(master_option_id: $master_option_id) {
            masterOption {
                master_option_id
                title
                description
                option_key
                options_type
                status
                pricing_method
                attributes
            }
        }
    }
    '''

    variables = {'master_option_id': int(option_id) if option_id else None}
    result = client._execute_graphql(query, variables)
    return result.get('data', {})
