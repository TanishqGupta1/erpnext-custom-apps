"""Introspect all nested types for Order."""

import frappe

@frappe.whitelist()
def introspect_types():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()
    results = {}

    # List of types to introspect
    type_queries = [
        ('Customer', 'Customer'),
        ('DeliveryDetail', 'DeliveryDetail'),
        ('BillingDetail', 'BillingDetail'),
        ('OrderProduct', 'OrderProduct'),
        ('Order', 'Order'),
    ]

    for name, type_name in type_queries:
        query = '''
        {
          __type(name: "''' + type_name + '''") {
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

        try:
            result = client._execute_graphql(query)
            type_data = result.get('data', {}).get('__type')
            if type_data:
                results[name] = [f['name'] for f in type_data.get('fields', [])]
            else:
                results[name] = 'Type not found'
        except Exception as e:
            results[name] = f'Error: {str(e)}'

    return results
