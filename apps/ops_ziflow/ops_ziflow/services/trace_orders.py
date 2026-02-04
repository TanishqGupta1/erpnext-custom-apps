"""Trace get_orders call in detail."""

import frappe

@frappe.whitelist()
def trace_orders():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from datetime import datetime, timedelta

    client = OnPrintShopClient()

    # Manually set date range
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # Call get_orders with explicit dates
    result_with_dates = client.get_orders(limit=5, from_date=from_date, to_date=to_date)

    # Call get_orders without dates (should auto-generate them)
    result_no_dates = client.get_orders(limit=5)

    return {
        'explicit_dates': {
            'from_date': from_date,
            'to_date': to_date,
            'result': result_with_dates
        },
        'auto_dates': {
            'result': result_no_dates
        }
    }
