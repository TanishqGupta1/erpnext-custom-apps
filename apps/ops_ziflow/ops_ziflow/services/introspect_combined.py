"""Introspect all types in one query."""

import frappe

@frappe.whitelist()
def introspect_types():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    import time

    # Wait a bit to avoid rate limiting
    time.sleep(2)

    client = OnPrintShopClient()

    # Single query with all types
    query = '''
    {
      customer: __type(name: "Customer") {
        fields { name }
      }
      delivery: __type(name: "DeliveryDetail") {
        fields { name }
      }
      billing: __type(name: "BillingDetail") {
        fields { name }
      }
      product: __type(name: "OrderProduct") {
        fields { name }
      }
    }
    '''

    try:
        result = client._execute_graphql(query)
        data = result.get('data', {})
        return {
            'Customer': [f['name'] for f in (data.get('customer') or {}).get('fields', [])] if data.get('customer') else 'Not found',
            'DeliveryDetail': [f['name'] for f in (data.get('delivery') or {}).get('fields', [])] if data.get('delivery') else 'Not found',
            'BillingDetail': [f['name'] for f in (data.get('billing') or {}).get('fields', [])] if data.get('billing') else 'Not found',
            'OrderProduct': [f['name'] for f in (data.get('product') or {}).get('fields', [])] if data.get('product') else 'Not found',
        }
    except Exception as e:
        return {'error': str(e)}
