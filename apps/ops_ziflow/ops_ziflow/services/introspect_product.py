"""Introspect OrderProduct type fields."""

import frappe

@frappe.whitelist()
def get_product_fields():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    import time

    time.sleep(2)
    client = OnPrintShopClient()

    # Get OrderProduct type fields with full type info
    query = '''
    {
      orderProduct: __type(name: "OrderProduct") {
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
      productAttribute: __type(name: "ProductAttribute") {
        name
        fields { name }
      }
      orderProductAttribute: __type(name: "OrderProductAttribute") {
        name
        fields { name }
      }
    }
    '''

    try:
        result = client._execute_graphql(query)
        data = result.get('data', {})

        response = {}

        op = data.get('orderProduct')
        if op:
            response['OrderProduct'] = []
            for f in op.get('fields', []):
                type_info = f.get('type', {})
                type_name = type_info.get('name')
                if not type_name and type_info.get('ofType'):
                    type_name = type_info['ofType'].get('name')
                response['OrderProduct'].append({
                    'name': f['name'],
                    'type': type_name or type_info.get('kind')
                })

        pa = data.get('productAttribute')
        if pa:
            response['ProductAttribute'] = [f['name'] for f in pa.get('fields', [])]

        opa = data.get('orderProductAttribute')
        if opa:
            response['OrderProductAttribute'] = [f['name'] for f in opa.get('fields', [])]

        return response
    except Exception as e:
        import traceback
        return {'error': str(e), 'traceback': traceback.format_exc()}
