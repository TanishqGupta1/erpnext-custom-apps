"""Debug poll function."""

import frappe

@frappe.whitelist()
def debug_poll():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()

    # Test get_orders directly
    result = client.get_orders(limit=5)

    return {
        'result_type': type(result).__name__,
        'result_keys': list(result.keys()) if isinstance(result, dict) else None,
        'orders_list': result.get('orders', []),
        'total_orders': result.get('totalOrders', 0),
        'raw_result': result
    }
