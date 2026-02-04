"""Debug sync process - detailed."""

import frappe

@frappe.whitelist()
def debug_sync():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    # Get orders
    result = client.get_orders(limit=3)
    orders = result.get("orders", [])

    debug_info = {
        'total_fetched': len(orders),
        'order_details': []
    }

    for order in orders:
        orders_id = order.get("orders_id")
        if not orders_id:
            continue

        # Check if order has product
        has_product = "product" in order

        # Try to fetch full details
        try:
            full_order = client.get_order(orders_id)
            debug_info['order_details'].append({
                'orders_id': orders_id,
                'from_list_has_product': has_product,
                'full_order_success': full_order is not None,
                'full_order_has_product': 'product' in (full_order or {}),
                'full_order_keys': list(full_order.keys()) if full_order else None
            })
        except Exception as e:
            debug_info['order_details'].append({
                'orders_id': orders_id,
                'error': str(e)
            })

    return debug_info
