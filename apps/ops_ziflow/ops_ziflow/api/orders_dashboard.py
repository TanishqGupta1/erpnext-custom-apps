"""Dashboard statistics API for OPS Orders."""

from typing import Any, Dict

import frappe


@frappe.whitelist()
def get_orders_dashboard_stats(from_date=None, to_date=None, status=None, customer=None) -> Dict[str, Any]:
    """Get OPS Orders dashboard statistics with optional filters."""

    # Build date and status conditions
    conditions = []
    values = {}

    if from_date:
        conditions.append("DATE(date_purchased) >= %(from_date)s")
        values["from_date"] = from_date
    if to_date:
        conditions.append("DATE(date_purchased) <= %(to_date)s")
        values["to_date"] = to_date
    if status:
        conditions.append("order_status = %(status)s")
        values["status"] = status
    if customer:
        conditions.append("(customer_name LIKE %(customer)s OR ops_order_id LIKE %(customer)s)")
        values["customer"] = f"%{customer}%"

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Orders by status (with filters)
    status_counts = frappe.db.sql(f"""
        SELECT order_status, COUNT(*) as count
        FROM `tabOPS Order`
        WHERE {where_clause}
        GROUP BY order_status
    """, values, as_dict=True)

    by_status = {row.order_status or "Unknown": row.count for row in status_counts}
    total_orders = sum(by_status.values())

    # Key status counts
    new_orders = by_status.get("New Order", 0)
    in_production = by_status.get("In Production", 0)
    ready_fulfillment = by_status.get("Ready for Fulfillment", 0)
    fulfilled = by_status.get("Fulfilled", 0)
    completed = by_status.get("Order Completed", 0)
    cancelled = by_status.get("Cancelled", 0) + by_status.get("Refunded", 0)

    # Active orders (not completed/cancelled)
    active_statuses = ["New Order", "In Design", "Order Processing", "Order Review",
                       "In Production", "Ready for Fulfillment", "Materials on Order", "Reprint Order"]
    active_orders = sum(by_status.get(s, 0) for s in active_statuses)

    # Completed orders count
    completed_orders = by_status.get("Order Completed", 0) + by_status.get("Fulfilled", 0)

    # Orders pending proofs (with filters)
    pending_conditions = conditions.copy() if conditions else []
    pending_conditions.append("all_proofs_approved = 0")
    pending_conditions.append("pending_proof_count > 0")
    pending_where = " AND ".join(pending_conditions)

    pending_proofs_result = frappe.db.sql(f"""
        SELECT COUNT(*) as cnt FROM `tabOPS Order`
        WHERE {pending_where}
    """, values, as_dict=True)
    pending_proofs = pending_proofs_result[0].cnt if pending_proofs_result else 0

    # Revenue stats (with filters)
    revenue_stats = frappe.db.sql(f"""
        SELECT
            SUM(order_amount) as total_revenue,
            SUM(CASE WHEN order_status = 'Order Completed' THEN order_amount ELSE 0 END) as completed_revenue,
            AVG(order_amount) as avg_order_value
        FROM `tabOPS Order`
        WHERE {where_clause}
        AND order_status NOT IN ('Cancelled', 'Refunded')
    """, values, as_dict=True)[0]

    # Orders this month (always show regardless of filter)
    this_month_start = frappe.utils.get_first_day(frappe.utils.nowdate())
    orders_this_month = frappe.db.count("OPS Order", filters={
        "date_purchased": [">=", this_month_start]
    })

    # Revenue this month (always show regardless of filter)
    monthly_revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(order_amount), 0) as revenue
        FROM `tabOPS Order`
        WHERE date_purchased >= %s
        AND order_status NOT IN ('Cancelled', 'Refunded')
    """, (this_month_start,), as_dict=True)[0]

    # Orders today (always show regardless of filter)
    orders_today = frappe.db.count("OPS Order", filters={
        "date_purchased": [">=", frappe.utils.nowdate()]
    })

    # Today's revenue
    today_revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(order_amount), 0) as revenue
        FROM `tabOPS Order`
        WHERE DATE(date_purchased) = %s
        AND order_status NOT IN ('Cancelled', 'Refunded')
    """, (frappe.utils.nowdate(),), as_dict=True)[0].revenue or 0

    # Overdue orders (with filters)
    overdue_conditions = conditions.copy() if conditions else []
    overdue_conditions.append("production_due_date IS NOT NULL")
    overdue_conditions.append("production_due_date < %(today)s")
    overdue_conditions.append("order_status NOT IN ('Order Completed', 'Fulfilled', 'Cancelled', 'Refunded')")
    overdue_where = " AND ".join(overdue_conditions)
    overdue_values = {**values, "today": frappe.utils.nowdate()}

    overdue_result = frappe.db.sql(f"""
        SELECT COUNT(*) as cnt FROM `tabOPS Order`
        WHERE {overdue_where}
    """, overdue_values, as_dict=True)
    overdue_orders = overdue_result[0].cnt if overdue_result else 0

    return {
        "total_orders": total_orders,
        "active_orders": active_orders,
        "completed_orders": completed_orders,
        "new_orders": new_orders,
        "in_production": in_production,
        "ready_fulfillment": ready_fulfillment,
        "fulfilled": fulfilled,
        "completed": completed,
        "cancelled": cancelled,
        "pending_proofs": pending_proofs,
        "overdue_orders": overdue_orders,
        "orders_today": orders_today,
        "today_revenue": today_revenue,
        "orders_this_month": orders_this_month,
        "total_revenue": revenue_stats.total_revenue or 0,
        "completed_revenue": revenue_stats.completed_revenue or 0,
        "avg_order_value": round(revenue_stats.avg_order_value or 0, 2),
        "monthly_revenue": monthly_revenue.revenue or 0,
        "by_status": by_status,
    }


@frappe.whitelist()
def get_orders_timeline(days: int = 30) -> Dict[str, Any]:
    """Get order creation timeline for charts."""
    start_date = frappe.utils.add_days(frappe.utils.nowdate(), -int(days))

    timeline = frappe.db.sql("""
        SELECT DATE(date_purchased) as date, COUNT(*) as count, SUM(order_amount) as revenue
        FROM `tabOPS Order`
        WHERE date_purchased >= %s
        GROUP BY DATE(date_purchased)
        ORDER BY date
    """, (start_date,), as_dict=True)

    completed = frappe.db.sql("""
        SELECT DATE(orders_date_finished) as date, COUNT(*) as count
        FROM `tabOPS Order`
        WHERE orders_date_finished >= %s AND orders_date_finished IS NOT NULL
        GROUP BY DATE(orders_date_finished)
        ORDER BY date
    """, (start_date,), as_dict=True)

    return {"created": timeline, "completed": completed}


@frappe.whitelist()
def get_recent_orders(limit: int = 20, from_date=None, to_date=None, status=None, customer=None) -> Dict[str, Any]:
    """Get recently created orders with optional filters."""

    # Build filters
    filters = {}
    if from_date:
        filters["date_purchased"] = [">=", from_date]
    if to_date:
        if "date_purchased" in filters:
            # Need to use SQL for range
            pass
        else:
            filters["date_purchased"] = ["<=", to_date + " 23:59:59"]
    if status:
        filters["order_status"] = status

    # If we have both from_date and to_date, use SQL
    if from_date and to_date:
        conditions = ["DATE(date_purchased) >= %(from_date)s", "DATE(date_purchased) <= %(to_date)s"]
        values = {"from_date": from_date, "to_date": to_date}

        if status:
            conditions.append("order_status = %(status)s")
            values["status"] = status
        if customer:
            conditions.append("(customer_name LIKE %(customer)s OR ops_order_id LIKE %(customer)s)")
            values["customer"] = f"%{customer}%"

        where_clause = " AND ".join(conditions)

        orders = frappe.db.sql(f"""
            SELECT name, ops_order_id, customer_name, order_status, order_amount,
                   date_purchased, pending_proof_count, all_proofs_approved
            FROM `tabOPS Order`
            WHERE {where_clause}
            ORDER BY date_purchased DESC
            LIMIT %(limit)s
        """, {**values, "limit": int(limit)}, as_dict=True)
    else:
        if customer:
            # Use SQL for LIKE search
            conditions = []
            values = {}
            if from_date:
                conditions.append("DATE(date_purchased) >= %(from_date)s")
                values["from_date"] = from_date
            if to_date:
                conditions.append("DATE(date_purchased) <= %(to_date)s")
                values["to_date"] = to_date
            if status:
                conditions.append("order_status = %(status)s")
                values["status"] = status
            conditions.append("(customer_name LIKE %(customer)s OR ops_order_id LIKE %(customer)s)")
            values["customer"] = f"%{customer}%"

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            orders = frappe.db.sql(f"""
                SELECT name, ops_order_id, customer_name, order_status, order_amount,
                       date_purchased, pending_proof_count, all_proofs_approved
                FROM `tabOPS Order`
                WHERE {where_clause}
                ORDER BY date_purchased DESC
                LIMIT %(limit)s
            """, {**values, "limit": int(limit)}, as_dict=True)
        else:
            orders = frappe.get_all(
                "OPS Order",
                filters=filters,
                fields=["name", "ops_order_id", "customer_name", "order_status", "order_amount",
                        "date_purchased", "pending_proof_count", "all_proofs_approved"],
                order_by="date_purchased desc",
                limit=int(limit)
            )

    return {"orders": orders, "count": len(orders)}


@frappe.whitelist()
def get_orders_needing_attention(limit: int = 15) -> Dict[str, Any]:
    """Get orders that need attention (pending proofs, overdue, etc.)."""

    # Orders with pending proofs
    pending_proofs = frappe.get_all(
        "OPS Order",
        filters={
            "all_proofs_approved": 0,
            "pending_proof_count": [">", 0],
            "order_status": ["not in", ["Order Completed", "Cancelled", "Refunded"]]
        },
        fields=["name", "ops_order_id", "customer_name", "order_status", "pending_proof_count", "date_purchased"],
        order_by="date_purchased asc",
        limit=int(limit)
    )

    # Overdue orders (must have a production_due_date set and be past due)
    # Sorted DESC so most recently overdue appear first
    overdue = frappe.db.sql("""
        SELECT name, ops_order_id, customer_name, order_status, production_due_date, date_purchased
        FROM `tabOPS Order`
        WHERE production_due_date IS NOT NULL
        AND production_due_date < %s
        AND order_status NOT IN ('Order Completed', 'Fulfilled', 'Cancelled', 'Refunded')
        ORDER BY production_due_date DESC
        LIMIT %s
    """, (frappe.utils.nowdate(), int(limit)), as_dict=True)

    return {
        "pending_proofs": pending_proofs,
        "overdue": overdue
    }


@frappe.whitelist()
def get_top_customers(limit: int = 10) -> Dict[str, Any]:
    """Get top customers by order count and revenue."""
    customers = frappe.db.sql("""
        SELECT
            customer_name,
            customer_company,
            COUNT(*) as order_count,
            SUM(order_amount) as total_revenue
        FROM `tabOPS Order`
        WHERE order_status NOT IN ('Cancelled', 'Refunded')
        AND customer_name IS NOT NULL AND customer_name != ''
        GROUP BY customer_name, customer_company
        ORDER BY total_revenue DESC
        LIMIT %s
    """, (int(limit),), as_dict=True)

    return {"customers": customers}


@frappe.whitelist()
def get_production_pipeline() -> Dict[str, Any]:
    """Get orders in production pipeline."""
    pipeline_statuses = ["New Order", "In Design", "Order Processing", "Order Review",
                         "In Production", "Ready for Fulfillment"]

    pipeline = {}
    for status in pipeline_statuses:
        orders = frappe.get_all(
            "OPS Order",
            filters={"order_status": status},
            fields=["name", "ops_order_id", "customer_name", "order_amount", "production_due_date"],
            order_by="production_due_date asc",
            limit=10
        )
        pipeline[status] = {
            "count": frappe.db.count("OPS Order", {"order_status": status}),
            "orders": orders
        }

    return pipeline


@frappe.whitelist()
def get_shipment_stats() -> Dict[str, Any]:
    """Get shipment tracking statistics."""

    # Orders awaiting shipment (Ready for Fulfillment status, no tracking number)
    awaiting_shipment = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabOPS Order`
        WHERE order_status = 'Ready for Fulfillment'
        AND (tracking_number IS NULL OR tracking_number = '')
    """, as_dict=True)[0].cnt or 0

    # Orders with shipments in transit (has tracking, not delivered)
    in_transit = frappe.db.sql("""
        SELECT COUNT(DISTINCT parent) as cnt
        FROM `tabOPS Shipment`
        WHERE shipment_status IN ('Label Created', 'Picked Up', 'In Transit', 'Out for Delivery')
    """, as_dict=True)[0].cnt or 0

    # Delivered today
    today = frappe.utils.nowdate()
    delivered_today = frappe.db.sql("""
        SELECT COUNT(*) as cnt
        FROM `tabOPS Shipment`
        WHERE shipment_status = 'Delivered'
        AND DATE(delivered_date) = %s
    """, (today,), as_dict=True)[0].cnt or 0

    # Recent shipments with tracking
    recent_shipments = frappe.db.sql("""
        SELECT
            s.parent as order_name,
            o.ops_order_id,
            s.carrier,
            s.tracking_number,
            s.tracking_url,
            s.shipment_status,
            s.shipped_date
        FROM `tabOPS Shipment` s
        JOIN `tabOPS Order` o ON o.name = s.parent
        WHERE s.tracking_number IS NOT NULL AND s.tracking_number != ''
        ORDER BY COALESCE(s.shipped_date, s.creation) DESC
        LIMIT 10
    """, as_dict=True)

    # If no shipments in child table, fall back to orders with tracking_number
    if not recent_shipments:
        recent_shipments = frappe.db.sql("""
            SELECT
                name as order_name,
                ops_order_id,
                courier_company_name as carrier,
                tracking_number,
                tracking_url,
                CASE
                    WHEN order_status = 'Fulfilled' THEN 'Delivered'
                    WHEN order_status = 'Ready for Fulfillment' THEN 'Label Created'
                    ELSE 'In Transit'
                END as shipment_status
            FROM `tabOPS Order`
            WHERE tracking_number IS NOT NULL AND tracking_number != ''
            ORDER BY modified DESC
            LIMIT 10
        """, as_dict=True)

    return {
        "awaiting_shipment": awaiting_shipment,
        "in_transit": in_transit,
        "delivered_today": delivered_today,
        "recent_shipments": recent_shipments
    }
