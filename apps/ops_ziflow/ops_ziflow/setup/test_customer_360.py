# Test script for Customer 360 API

import frappe
from ops_ziflow.api.customer_360 import (
    get_customer_360_summary,
    get_customer_orders,
    get_customer_proofs,
    get_customer_timeline
)


def test():
    # Test with Skyline Schools (has ops_corporate_id = 270)
    customer = "Skyline Schools"

    print(f"\n=== Testing Customer 360 for: {customer} ===\n")

    # Get ops_corporate_id
    ops_id = frappe.db.get_value("Customer", customer, "ops_corporate_id")
    print(f"OPS Corporate ID: {ops_id}")

    # Test summary
    print("\n--- Summary ---")
    summary = get_customer_360_summary(customer)
    print(f"Orders: {summary.get('orders')}")
    print(f"Proofs: {summary.get('proofs')}")
    print(f"Communications: {summary.get('communications')}")

    # Test orders
    print("\n--- Orders (first 3) ---")
    orders_result = get_customer_orders(customer, limit=3)
    print(f"Total orders: {orders_result.get('total')}")
    for o in orders_result.get('data', []):
        print(f"  - {o.get('ops_order_id')}: {o.get('order_status')} - {o.get('total_amount')}")

    # Test proofs
    print("\n--- Proofs (first 3) ---")
    proofs_result = get_customer_proofs(customer, limit=3)
    print(f"Total proofs: {proofs_result.get('total')}")
    for p in proofs_result.get('data', []):
        print(f"  - {p.get('proof_name')}: {p.get('proof_status')}")

    # Test timeline
    print("\n--- Timeline (first 3) ---")
    timeline_result = get_customer_timeline(customer, limit=3)
    print(f"Total communications: {timeline_result.get('total')}")
    for c in timeline_result.get('data', []):
        print(f"  - {c.get('channel')}: {c.get('subject', 'No subject')}")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test()
