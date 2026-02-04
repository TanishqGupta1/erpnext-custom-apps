"""Full OPS GraphQL API introspection for all types."""

import frappe
import json

@frappe.whitelist()
def introspect_all():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    # First, get a list of all types
    schema_query = '''
    {
      __schema {
        types {
          name
          kind
        }
      }
    }
    '''

    schema_result = client._execute_graphql(schema_query)
    types = schema_result.get('data', {}).get('__schema', {}).get('types', [])

    # Filter for interesting types (not built-in)
    interesting = [t['name'] for t in types if not t['name'].startswith('__') and t['kind'] in ['OBJECT', 'INPUT_OBJECT']]

    # Get product-related types
    product_types = [t for t in interesting if any(k in t.lower() for k in ['product', 'option', 'attribute', 'master', 'price', 'order', 'quote'])]

    return {'types': sorted(product_types)}

@frappe.whitelist()
def introspect_type(type_name):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    client = OnPrintShopClient()

    query = f'''
    {{
      __type(name: "{type_name}") {{
        name
        kind
        fields {{
          name
          type {{
            name
            kind
            ofType {{
              name
              kind
              ofType {{
                name
              }}
            }}
          }}
        }}
        inputFields {{
          name
          type {{
            name
            kind
            ofType {{
              name
            }}
          }}
        }}
      }}
    }}
    '''

    result = client._execute_graphql(query)
    type_data = result.get('data', {}).get('__type', {})

    if not type_data:
        return {'error': f'Type {type_name} not found'}

    output = {'name': type_data.get('name'), 'kind': type_data.get('kind'), 'fields': []}

    fields = type_data.get('fields') or type_data.get('inputFields') or []
    for f in fields:
        type_info = f.get('type', {})
        type_str = type_info.get('name')
        if not type_str:
            of_type = type_info.get('ofType', {})
            type_str = of_type.get('name')
            if not type_str and of_type.get('ofType'):
                type_str = f"[{of_type['ofType'].get('name')}]"
        output['fields'].append({'name': f['name'], 'type': type_str or type_info.get('kind')})

    return output
