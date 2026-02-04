"""Introspect all order-related mutations in OPS API."""

import frappe

def introspect_order_mutations():
    """Get all mutations related to orders."""
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    # Get setShipment mutation
    query1 = """
        query {
            __type(name: "Mutation") {
                fields {
                    name
                    args {
                        name
                        type {
                            name
                            kind
                            ofType { name kind }
                        }
                    }
                }
            }
        }
    """

    result = client._execute_graphql(query1)
    fields = result.get("data", {}).get("__type", {}).get("fields", [])

    # Find order-related mutations
    order_mutations = []
    for f in fields:
        name = f.get("name", "")
        if any(x in name.lower() for x in ["order", "shipment", "product"]):
            order_mutations.append(f)
            print(f"\n=== {name} ===")
            for arg in f.get("args", []):
                t = arg.get("type", {})
                type_name = t.get("name") or (t.get("ofType") or {}).get("name")
                print(f"  {arg['name']}: {type_name}")

    return order_mutations
