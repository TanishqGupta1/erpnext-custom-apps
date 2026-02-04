"""Fetch sample product from OPS API."""

import frappe
import json

@frappe.whitelist()
def list_products(limit=5):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    # First try to list products
    query = '''
    query($limit: Int) {
        products(limit: $limit) {
            products {
                product_id
                product_name
                main_sku
            }
            totalProducts
        }
    }
    '''

    variables = {'limit': int(limit)}
    result = client._execute_graphql(query, variables)
    return result

@frappe.whitelist()
def fetch_master_options(limit=5):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    # Try to get master options
    query = '''
    query($limit: Int) {
        getMasterOption(limit: $limit) {
            masterOption {
                master_option_id
                title
                option_key
                options_type
                status
                attributes
            }
            totalMasterOption
        }
    }
    '''

    variables = {'limit': int(limit)}
    result = client._execute_graphql(query, variables)
    return result
