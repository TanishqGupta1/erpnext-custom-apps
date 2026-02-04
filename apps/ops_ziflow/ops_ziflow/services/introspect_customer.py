"""Introspect Customer type fields."""

import frappe

@frappe.whitelist()
def get_customer_fields():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    # Get Customer type fields
    query = '''
    {
      __type(name: "Customer") {
        name
        fields {
          name
          type {
            name
            kind
          }
        }
      }
    }
    '''

    result = client._execute_graphql(query)
    fields = result.get('data', {}).get('__type', {}).get('fields', [])
    return {'fields': [f['name'] for f in fields]}
