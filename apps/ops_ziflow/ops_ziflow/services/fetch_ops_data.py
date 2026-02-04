"""Fetch actual OPS data for analysis."""

import frappe
import json

@frappe.whitelist()
def fetch_master_options(limit=5):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    query = '''
    query($limit: Int) {
        product_master_options(limit: $limit) {
            masterOption {
                master_option_id
                title
                option_key
                options_type
                status
                pricing_method
                attributes
            }
            totalMasterOption
        }
    }
    '''

    variables = {'limit': int(limit)}
    result = client._execute_graphql(query, variables)
    return result

@frappe.whitelist()
def fetch_attributes(prod_add_opt_id):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    query = '''
    query($prod_add_opt_id: Int) {
        attributes(prod_add_opt_id: $prod_add_opt_id) {
            attributes {
                auto_id
                attribute_id
                prod_add_opt_id
                label
                default_attribute
                sort_order
                status
                attributes_image
                setup_cost
                attribute_key
                master_attribute_id
                multiplier
            }
            totalAttributes
        }
    }
    '''

    variables = {'prod_add_opt_id': int(prod_add_opt_id)}
    result = client._execute_graphql(query, variables)
    return result

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
    return result
