"""List all available GraphQL queries."""

import frappe
import json

@frappe.whitelist()
def list_queries():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    # Get all query fields
    query = '''
    {
        __schema {
            queryType {
                fields {
                    name
                    args {
                        name
                        type { name kind }
                    }
                }
            }
        }
    }
    '''

    result = client._execute_graphql(query)
    fields = result.get('data', {}).get('__schema', {}).get('queryType', {}).get('fields', [])

    # Filter for product/option related queries
    relevant = [f for f in fields if any(k in f['name'].lower() for k in ['product', 'option', 'master', 'attribute', 'quote', 'order'])]
    return {'queries': [{'name': f['name'], 'args': [a['name'] for a in f.get('args', [])]} for f in relevant]}
