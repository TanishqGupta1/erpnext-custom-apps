"""Trace sync function."""

import frappe
from frappe.utils import now_datetime, cint, flt

@frappe.whitelist()
def trace_sync():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()
    orders_id = 1130  # Test with first order

    debug = {'steps': []}

    # Step 1: Check if order exists
    existing_name = frappe.db.get_value("OPS Order", {"ops_order_id": str(orders_id)}, "name")
    debug['steps'].append({'step': 'check_existing', 'existing': existing_name})

    # Step 2: Get order data
    order_data = client.get_order(orders_id)
    debug['steps'].append({'step': 'get_order', 'success': order_data is not None, 'keys': list(order_data.keys()) if order_data else None})

    if not order_data:
        return debug

    # Step 3: Create or get doc
    if existing_name:
        doc = frappe.get_doc("OPS Order", existing_name)
    else:
        doc = frappe.new_doc("OPS Order")
        doc.ops_order_id = str(orders_id)

    debug['steps'].append({'step': 'get_doc', 'is_new': doc.is_new()})

    # Step 4: Try to map fields
    try:
        doc.order_name = order_data.get("order_name") or "Order " + str(orders_id)
        doc.order_status = order_data.get("order_status") or "Pending"
        doc.orders_status_id = cint(order_data.get("orders_status_id", 0))
        doc.total_amount = flt(order_data.get("total_amount", 0))
        doc.order_amount = flt(order_data.get("order_amount", 0))
        doc.shipping_amount = flt(order_data.get("shipping_amount", 0))
        doc.tax_amount = flt(order_data.get("tax_amount", 0))
        doc.coupon_amount = flt(order_data.get("coupon_amount", 0))
        doc.payment_method_name = order_data.get("payment_method_name") or ""
        # Set defaults for mandatory fields
        doc.tracking_url = "N/A"
        doc.carrier_raw_response = "{}"
        debug['steps'].append({'step': 'map_fields', 'success': True})
    except Exception as e:
        debug['steps'].append({'step': 'map_fields', 'success': False, 'error': str(e)})
        return debug

    # Step 5: Try to map products
    try:
        products = order_data.get("product", [])
        doc.ops_order_products = []
        for product in products:
            row = doc.append("ops_order_products", {})
            row.orders_products_id = cint(product.get("orders_products_id", 0))
            row.product_id = cint(product.get("product_id", 0))
            row.products_name = product.get("products_name") or ""
            row.products_title = product.get("products_title") or ""
            row.products_quantity = cint(product.get("products_quantity", 1))
            row.products_price = flt(product.get("products_price", 0))
            row.final_price = flt(product.get("products_unit_price", 0))
            row.product_status = product.get("product_status") or "Pending"
            row.product_status_id = cint(product.get("product_status_id", 0))
        debug['steps'].append({'step': 'map_products', 'success': True, 'count': len(products)})
    except Exception as e:
        debug['steps'].append({'step': 'map_products', 'success': False, 'error': str(e)})
        return debug

    # Step 6: Try to save
    try:
        doc.sync_in_progress = 1
        doc.sync_status = "Synced"
        doc.sync_error = ""

        if doc.is_new():
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)

        debug['steps'].append({'step': 'save', 'success': True, 'doc_name': doc.name})
        frappe.db.commit()
    except Exception as e:
        debug['steps'].append({'step': 'save', 'success': False, 'error': str(e)})
        import traceback
        debug['traceback'] = traceback.format_exc()

    return debug
