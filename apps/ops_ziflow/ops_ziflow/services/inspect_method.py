"""Inspect get_orders method source."""

import frappe
import inspect

@frappe.whitelist()
def inspect_get_orders():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    source = inspect.getsource(OnPrintShopClient.get_orders)
    # Get first 30 lines
    lines = source.split('\n')[:30]
    return {'source_lines': lines}
