"""Introspect all nested types."""

import frappe

@frappe.whitelist()
def get_all_fields():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    types = ['DeliveryDetail', 'BillingDetail']
    results = {}

    for type_name in types:
        query = f'''
        {{
          __type(name: "{type_name}") {{
            name
            fields {{
              name
            }}
          }}
        }}
        '''

        result = client._execute_graphql(query)
        fields = result.get('data', {}).get('__type', {}).get('fields', [])
        results[type_name] = [f['name'] for f in fields]

    return results
