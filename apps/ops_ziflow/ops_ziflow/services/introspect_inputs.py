"""Introspect input types for order mutations."""

import frappe

def introspect_inputs():
    """Get input type fields."""
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    input_types = [
        "UpdateOrderStatusInput",
        "SetOrderProductInput",
    ]

    for input_type in input_types:
        query = f"""
            query {{
                __type(name: "{input_type}") {{
                    name
                    inputFields {{
                        name
                        type {{
                            name
                            kind
                            ofType {{ name }}
                        }}
                    }}
                }}
            }}
        """

        result = client._execute_graphql(query)
        type_info = result.get("data", {}).get("__type", {})

        print(f"\n=== {input_type} ===")
        for field in type_info.get("inputFields", []):
            t = field.get("type", {})
            type_name = t.get("name") or (t.get("ofType") or {}).get("name")
            print(f"  {field['name']}: {type_name}")

    return "done"
