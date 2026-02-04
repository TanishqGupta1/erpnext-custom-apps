"""
OPS Orders List API
Provides backend functionality for the OPS Orders List page
"""
import frappe
from frappe import _


@frappe.whitelist()
def bulk_update_status(orders, status):
    """
    Bulk update order status for multiple orders

    Args:
        orders: List of order names (JSON array)
        status: New status to set

    Returns:
        dict with updated count
    """
    import json

    if isinstance(orders, str):
        orders = json.loads(orders)

    if not orders:
        return {"updated": 0}

    updated = 0
    for order_name in orders:
        try:
            doc = frappe.get_doc("OPS Order", order_name)
            doc.order_status = status
            doc.save(ignore_permissions=True)
            updated += 1
        except Exception as e:
            frappe.log_error(f"Failed to update order {order_name}: {str(e)}")

    frappe.db.commit()
    return {"updated": updated}


@frappe.whitelist()
def get_orders_with_details(filters=None, limit=20, offset=0, order_by="date_purchased desc"):
    """
    Get orders with expanded details including products and proofs

    Args:
        filters: Filter conditions (JSON)
        limit: Number of records to fetch
        offset: Starting offset
        order_by: Sort order

    Returns:
        dict with orders list and total count
    """
    import json

    if isinstance(filters, str) and filters:
        filters = json.loads(filters)
    else:
        filters = {}

    # Build filter conditions
    conditions = []
    values = {}

    if filters.get("status"):
        if filters["status"] == "active":
            conditions.append("order_status NOT IN ('Order Completed', 'Fulfilled', 'Cancelled', 'Refunded')")
        else:
            conditions.append("order_status = %(status)s")
            values["status"] = filters["status"]

    if filters.get("from_date"):
        conditions.append("DATE(date_purchased) >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("DATE(date_purchased) <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    if filters.get("search"):
        conditions.append("(ops_order_id LIKE %(search)s OR customer_name LIKE %(search)s)")
        values["search"] = f"%{filters['search']}%"

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get orders
    orders = frappe.db.sql(f"""
        SELECT
            name, ops_order_id, customer_name, customer_email, customer_telephone,
            customer_company, order_status, order_amount, total_amount, date_purchased,
            production_due_date, delivery_date, payment_status_title,
            delivery_city, delivery_state, delivery_country, delivery_street_address,
            pending_proof_count, all_proofs_approved, tracking_number, shipping_status,
            shipping_amount, tax_amount, coupon_amount
        FROM `tabOPS Order`
        WHERE {where_clause}
        ORDER BY {order_by}
        LIMIT %(limit)s OFFSET %(offset)s
    """, {**values, "limit": int(limit), "offset": int(offset)}, as_dict=True)

    # Get total count
    total = frappe.db.sql(f"""
        SELECT COUNT(*) as count
        FROM `tabOPS Order`
        WHERE {where_clause}
    """, values, as_dict=True)[0].count

    # Enrich with products and proofs
    for order in orders:
        # Get products
        order["products"] = frappe.db.sql("""
            SELECT
                products_name, products_title, products_sku, products_quantity,
                products_price, final_price, product_width, product_height, product_size_unit
            FROM `tabOPS Order Product`
            WHERE parent = %s
            ORDER BY idx
        """, order.name, as_dict=True)

        # Get proofs
        order["proofs"] = frappe.db.sql("""
            SELECT
                name, proof_name, proof_status, ziflow_url, preview_url
            FROM `tabOPS ZiFlow Proof`
            WHERE ops_order = %s
        """, order.name, as_dict=True)

    return {
        "orders": orders,
        "total": total
    }


@frappe.whitelist()
def get_order_full_details(order_name):
    """
    Get complete order details including all child tables and related records

    Args:
        order_name: OPS Order name

    Returns:
        dict with complete order data
    """
    doc = frappe.get_doc("OPS Order", order_name)

    # Get all proofs for this order
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={"ops_order": order_name},
        fields=["name", "proof_name", "proof_status", "ziflow_url", "preview_url", "deadline", "approved_at"]
    )

    # Get customer details if linked
    customer = None
    if doc.customer_company:
        try:
            customer = frappe.get_doc("OPS Customer", doc.customer_company)
        except Exception:
            pass

    return {
        "order": doc.as_dict(),
        "proofs": proofs,
        "customer": customer.as_dict() if customer else None
    }


@frappe.whitelist()
def quick_actions(order_name, action, **kwargs):
    """
    Perform quick actions on an order

    Args:
        order_name: OPS Order name
        action: Action to perform (update_status, mark_shipped, add_note, etc.)
        **kwargs: Action-specific parameters
    """
    doc = frappe.get_doc("OPS Order", order_name)

    if action == "update_status":
        doc.order_status = kwargs.get("status")
        doc.save(ignore_permissions=True)
        return {"success": True, "message": f"Status updated to {kwargs.get('status')}"}

    elif action == "mark_shipped":
        doc.shipping_status = "Shipped"
        doc.tracking_number = kwargs.get("tracking_number", "")
        doc.tracking_url = kwargs.get("tracking_url", "")
        doc.save(ignore_permissions=True)
        return {"success": True, "message": "Order marked as shipped"}

    elif action == "add_tracking":
        doc.tracking_number = kwargs.get("tracking_number", "")
        doc.tracking_url = kwargs.get("tracking_url", "")
        doc.save(ignore_permissions=True)
        return {"success": True, "message": "Tracking info added"}

    else:
        return {"success": False, "message": f"Unknown action: {action}"}
