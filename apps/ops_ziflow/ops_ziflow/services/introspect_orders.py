"""Introspect GraphQL schema to find order query names."""

import frappe

@frappe.whitelist()
def get_order_queries():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    # Try to get schema introspection
    query = '''
    {
      __schema {
        queryType {
          fields {
            name
            description
          }
        }
      }
    }
    '''

    try:
        result = client._execute_graphql(query)
        fields = result.get('data', {}).get('__schema', {}).get('queryType', {}).get('fields', [])
        order_queries = []
        for f in fields:
            if 'order' in f['name'].lower():
                order_queries.append({'name': f['name'], 'description': f.get('description', '')})
        return {'success': True, 'order_queries': order_queries}
    except Exception as e:
        return {'success': False, 'error': str(e)}
