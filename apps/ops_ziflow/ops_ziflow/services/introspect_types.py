"""Introspect OPS GraphQL API types for updateOrderStatus."""

import frappe

def introspect_types():
    """Query the GraphQL schema for order status types."""
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    # Introspection query for OrderStatusUpdateTypeEnum
    query1 = """
        query {
            __type(name: "OrderStatusUpdateTypeEnum") {
                name
                kind
                enumValues {
                    name
                    description
                }
            }
        }
    """

    result1 = client._execute_graphql(query1)
    print("OrderStatusUpdateTypeEnum values:")
    enum_values = result1.get("data", {}).get("__type", {}).get("enumValues", [])
    for v in enum_values:
        print(f"  - {v['name']}: {v.get('description', '')}")

    # Introspection query for UpdateOrderStatusInput
    query2 = """
        query {
            __type(name: "UpdateOrderStatusInput") {
                name
                kind
                inputFields {
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
    """

    result2 = client._execute_graphql(query2)
    print("\nUpdateOrderStatusInput fields:")
    fields = result2.get("data", {}).get("__type", {}).get("inputFields", [])
    for f in fields:
        type_info = f.get("type", {})
        type_name = type_info.get("name") or (type_info.get("ofType", {}) or {}).get("name")
        print(f"  - {f['name']}: {type_name}")

    return {"enum": result1, "input": result2}
