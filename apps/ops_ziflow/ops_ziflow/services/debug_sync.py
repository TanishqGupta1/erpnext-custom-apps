"""Debug order sync date fields."""

import frappe

def debug_order_sync():
    """Debug why date_purchased and delivery_date are not being saved."""
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from ops_ziflow.services.order_sync_service import _safe_date

    # Get order from API
    client = OnPrintShopClient()
    order_data = client.get_order(1146)

    # Check the raw date values
    print("=" * 50)
    print("API Response for order 1146:")
    print(f"  orders_date_finished: {repr(order_data.get('orders_date_finished'))}")
    print(f"  orders_due_date: {repr(order_data.get('orders_due_date'))}")

    # Check what _safe_date returns
    date_finished = order_data.get("orders_date_finished")
    due_date = order_data.get("orders_due_date")

    print(f"\n_safe_date results:")
    print(f"  _safe_date(orders_date_finished): {repr(_safe_date(date_finished))}")
    print(f"  _safe_date(orders_due_date): {repr(_safe_date(due_date))}")

    # Now get the existing doc and try to set values
    doc = frappe.get_doc("OPS Order", "1146")
    print(f"\nExisting doc values:")
    print(f"  orders_date_finished: {repr(doc.orders_date_finished)}")
    print(f"  date_purchased: {repr(doc.date_purchased)}")
    print(f"  orders_due_date: {repr(doc.orders_due_date)}")
    print(f"  delivery_date: {repr(doc.delivery_date)}")

    # Try setting the values
    doc.date_purchased = _safe_date(date_finished)
    doc.delivery_date = _safe_date(due_date)

    print(f"\nAfter setting:")
    print(f"  date_purchased: {repr(doc.date_purchased)}")
    print(f"  delivery_date: {repr(doc.delivery_date)}")

    # Save and check
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # Re-fetch to verify
    doc2 = frappe.get_doc("OPS Order", "1146")
    print(f"\nAfter save and re-fetch:")
    print(f"  date_purchased: {repr(doc2.date_purchased)}")
    print(f"  delivery_date: {repr(doc2.delivery_date)}")

    print("=" * 50)
    return {"status": "done"}
