import json
import frappe

def check_api_fields(order_id=2302):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()
    order = client.get_order(order_id)

    if not order:
        print(f"Order {order_id} not found")
        return

    print("=== Delivery Detail Fields ===")
    delivery = order.get("delivery_detail", {})
    for key, value in delivery.items():
        print(f"  {key}: {value}")

    print("\n=== Billing Detail Fields ===")
    billing = order.get("billing_detail", {})
    for key, value in billing.items():
        print(f"  {key}: {value}")

    print("\n=== Customer Fields ===")
    customer = order.get("customer", {})
    for key, value in customer.items():
        print(f"  {key}: {value}")

    return "Done"
