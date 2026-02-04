"""Introspect Order type fields."""

import frappe

@frappe.whitelist()
def get_order_fields():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    # Get Order type fields
    query = '''
    {
      __type(name: "Order") {
        name
        fields {
          name
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
        }
      }
    }
    '''

    try:
        result = client._execute_graphql(query)
        fields = result.get('data', {}).get('__type', {}).get('fields', [])
        return {'success': True, 'fields': [f['name'] for f in fields]}
    except Exception as e:
        return {'success': False, 'error': str(e)}
