"""Introspect OPS GraphQL API to find updateOrderStatus mutation signature."""

import frappe

def introspect_update_order_status():
    """Query the GraphQL schema for updateOrderStatus mutation."""
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    # Introspection query for updateOrderStatus mutation
    query = """
        query {
            __type(name: "Mutation") {
                fields {
                    name
                    args {
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
        }
    """

    result = client._execute_graphql(query)

    # Find updateOrderStatus
    fields = result.get("data", {}).get("__type", {}).get("fields", [])

    for field in fields:
        if "order" in field.get("name", "").lower() and "status" in field.get("name", "").lower():
            print(f"\nMutation: {field['name']}")
            print("Arguments:")
            for arg in field.get("args", []):
                arg_type = arg.get("type", {})
                type_name = arg_type.get("name") or (arg_type.get("ofType", {}) or {}).get("name")
                type_kind = arg_type.get("kind")
                print(f"  - {arg['name']}: {type_name} ({type_kind})")

    return result
