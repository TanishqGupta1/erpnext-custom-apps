"""Consolidated OPS Dashboard API - Orders, Quotes, Proofs, Products."""

from typing import Any, Dict

import frappe


@frappe.whitelist()
def get_dashboard_overview() -> Dict[str, Any]:
    """Get consolidated overview of all OPS entities."""

    # === ORDERS ===
    order_status_counts = frappe.db.sql("""
        SELECT order_status, COUNT(*) as count
        FROM `tabOPS Order`
        GROUP BY order_status
    """, as_dict=True)
    orders_by_status = {row.order_status or "Unknown": row.count for row in order_status_counts}
    total_orders = sum(orders_by_status.values())

    active_order_statuses = ["New Order", "In Design", "Order Processing", "Order Review",
                             "In Production", "Ready for Fulfillment", "Materials on Order", "Reprint Order"]
    active_orders = sum(orders_by_status.get(s, 0) for s in active_order_statuses)

    order_revenue = frappe.db.sql("""
        SELECT
            COALESCE(SUM(order_amount), 0) as total,
            COALESCE(SUM(CASE WHEN order_status = 'Order Completed' THEN order_amount ELSE 0 END), 0) as completed
        FROM `tabOPS Order`
        WHERE order_status NOT IN ('Cancelled', 'Refunded')
    """, as_dict=True)[0]

    # Overdue orders
    overdue_orders = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabOPS Order`
        WHERE production_due_date IS NOT NULL
        AND production_due_date < %s
        AND order_status NOT IN ('Order Completed', 'Fulfilled', 'Cancelled', 'Refunded')
    """, (frappe.utils.nowdate(),), as_dict=True)[0].cnt or 0

    # === QUOTES ===
    quote_status_counts = frappe.db.sql("""
        SELECT quote_status, COUNT(*) as count
        FROM `tabOPS Quote`
        GROUP BY quote_status
    """, as_dict=True)
    quotes_by_status = {row.quote_status or "Unknown": row.count for row in quote_status_counts}
    total_quotes = sum(quotes_by_status.values())

    active_quote_statuses = ["Draft", "Pending", "Sent", "Accepted"]
    active_quotes = sum(quotes_by_status.get(s, 0) for s in active_quote_statuses)

    quote_value = frappe.db.sql("""
        SELECT
            COALESCE(SUM(quote_price), 0) as total,
            COALESCE(SUM(CASE WHEN quote_status = 'Converted' THEN quote_price ELSE 0 END), 0) as converted
        FROM `tabOPS Quote`
        WHERE quote_status NOT IN ('Cancelled', 'Rejected')
    """, as_dict=True)[0]

    # Conversion rate
    convertible = (quotes_by_status.get("Sent", 0) + quotes_by_status.get("Accepted", 0) +
                   quotes_by_status.get("Converted", 0) + quotes_by_status.get("Rejected", 0) +
                   quotes_by_status.get("Expired", 0))
    conversion_rate = round((quotes_by_status.get("Converted", 0) / convertible * 100), 1) if convertible > 0 else 0

    # === PROOFS ===
    proof_status_counts = frappe.db.sql("""
        SELECT proof_status, COUNT(*) as count
        FROM `tabOPS ZiFlow Proof`
        GROUP BY proof_status
    """, as_dict=True)
    proofs_by_status = {row.proof_status or "Unknown": row.count for row in proof_status_counts}
    total_proofs = sum(proofs_by_status.values())

    pending_proofs = (proofs_by_status.get("Draft", 0) + proofs_by_status.get("In Review", 0) +
                      proofs_by_status.get("Changes Requested", 0))
    approved_proofs = proofs_by_status.get("Approved", 0)

    # Overdue proofs
    overdue_proofs = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabOPS ZiFlow Proof`
        WHERE deadline IS NOT NULL
        AND deadline < %s
        AND proof_status IN ('Draft', 'In Review', 'Changes Requested')
    """, (frappe.utils.nowdate(),), as_dict=True)[0].cnt or 0

    # === PRODUCTS ===
    total_products = frappe.db.count("OPS Product")
    active_products = frappe.db.count("OPS Product", {"is_active": 1}) if frappe.db.has_column("OPS Product", "is_active") else total_products

    # Products by category (if category field exists)
    products_by_category = {}
    if frappe.db.has_column("OPS Product", "category"):
        cat_counts = frappe.db.sql("""
            SELECT category, COUNT(*) as count
            FROM `tabOPS Product`
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
        """, as_dict=True)
        products_by_category = {row.category: row.count for row in cat_counts}

    # === CUSTOMERS ===
    total_customers = frappe.db.count("OPS Customer")

    # === TODAY'S ACTIVITY ===
    today = frappe.utils.nowdate()
    orders_today = frappe.db.count("OPS Order", {"date_purchased": [">=", today]})
    quotes_today = frappe.db.count("OPS Quote", {"quote_date": [">=", today]})

    # === THIS MONTH ===
    this_month_start = frappe.utils.get_first_day(today)
    orders_this_month = frappe.db.count("OPS Order", {"date_purchased": [">=", this_month_start]})
    quotes_this_month = frappe.db.count("OPS Quote", {"quote_date": [">=", this_month_start]})

    monthly_revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(order_amount), 0) as revenue
        FROM `tabOPS Order`
        WHERE date_purchased >= %s
        AND order_status NOT IN ('Cancelled', 'Refunded')
    """, (this_month_start,), as_dict=True)[0].revenue or 0

    return {
        # Orders
        "total_orders": total_orders,
        "active_orders": active_orders,
        "orders_by_status": orders_by_status,
        "order_revenue": order_revenue.total,
        "completed_revenue": order_revenue.completed,
        "overdue_orders": overdue_orders,
        "new_orders": orders_by_status.get("New Order", 0),
        "in_production": orders_by_status.get("In Production", 0),
        "orders_today": orders_today,
        "orders_this_month": orders_this_month,
        "monthly_revenue": monthly_revenue,

        # Quotes
        "total_quotes": total_quotes,
        "active_quotes": active_quotes,
        "quotes_by_status": quotes_by_status,
        "quote_value": quote_value.total,
        "converted_value": quote_value.converted,
        "conversion_rate": conversion_rate,
        "pending_quotes": quotes_by_status.get("Pending", 0),
        "sent_quotes": quotes_by_status.get("Sent", 0),
        "quotes_today": quotes_today,
        "quotes_this_month": quotes_this_month,

        # Proofs
        "total_proofs": total_proofs,
        "pending_proofs": pending_proofs,
        "approved_proofs": approved_proofs,
        "overdue_proofs": overdue_proofs,
        "proofs_by_status": proofs_by_status,

        # Products
        "total_products": total_products,
        "active_products": active_products,
        "products_by_category": products_by_category,

        # Customers
        "total_customers": total_customers,
    }


@frappe.whitelist()
def get_recent_activity(limit: int = 20) -> Dict[str, Any]:
    """Get recent activity across all entities."""

    # Recent orders
    recent_orders = frappe.get_all(
        "OPS Order",
        fields=["name", "ops_order_id", "customer_name", "order_status", "order_amount", "date_purchased"],
        order_by="date_purchased desc",
        limit=int(limit)
    )

    # Recent quotes
    recent_quotes = frappe.get_all(
        "OPS Quote",
        fields=["name", "quote_id", "quote_title", "customer_name", "quote_status", "quote_price", "quote_date"],
        order_by="quote_date desc",
        limit=int(limit)
    )

    # Recent proofs
    recent_proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        fields=["name", "proof_name", "proof_status", "ops_order", "ops_customer", "creation"],
        order_by="creation desc",
        limit=int(limit)
    )

    return {
        "orders": recent_orders,
        "quotes": recent_quotes,
        "proofs": recent_proofs
    }


@frappe.whitelist()
def get_attention_items() -> Dict[str, Any]:
    """Get items needing attention across all entities."""

    # Overdue orders
    overdue_orders = frappe.db.sql("""
        SELECT name, ops_order_id, customer_name, order_status, production_due_date, order_amount
        FROM `tabOPS Order`
        WHERE production_due_date IS NOT NULL
        AND production_due_date < %s
        AND order_status NOT IN ('Order Completed', 'Fulfilled', 'Cancelled', 'Refunded')
        ORDER BY production_due_date DESC
        LIMIT 10
    """, (frappe.utils.nowdate(),), as_dict=True)

    # Orders pending proofs
    orders_pending_proofs = frappe.get_all(
        "OPS Order",
        filters={
            "all_proofs_approved": 0,
            "pending_proof_count": [">", 0],
            "order_status": ["not in", ["Order Completed", "Cancelled", "Refunded"]]
        },
        fields=["name", "ops_order_id", "customer_name", "pending_proof_count", "date_purchased"],
        order_by="date_purchased desc",
        limit=10
    )

    # Pending quotes
    pending_quotes = frappe.get_all(
        "OPS Quote",
        filters={"quote_status": ["in", ["Pending", "Sent"]]},
        fields=["name", "quote_id", "quote_title", "customer_name", "quote_price", "quote_status", "quote_date"],
        order_by="quote_date desc",
        limit=10
    )

    # Overdue proofs
    overdue_proofs = frappe.db.sql("""
        SELECT name, proof_name, proof_status, ops_order, ops_customer, deadline
        FROM `tabOPS ZiFlow Proof`
        WHERE deadline IS NOT NULL
        AND deadline < %s
        AND proof_status IN ('Draft', 'In Review', 'Changes Requested')
        ORDER BY deadline DESC
        LIMIT 10
    """, (frappe.utils.nowdate(),), as_dict=True)

    return {
        "overdue_orders": overdue_orders,
        "orders_pending_proofs": orders_pending_proofs,
        "pending_quotes": pending_quotes,
        "overdue_proofs": overdue_proofs
    }


@frappe.whitelist()
def get_charts_data(days: int = 30) -> Dict[str, Any]:
    """Get data for dashboard charts."""
    start_date = frappe.utils.add_days(frappe.utils.nowdate(), -int(days))

    # Orders timeline
    orders_timeline = frappe.db.sql("""
        SELECT DATE(date_purchased) as date, COUNT(*) as count, SUM(order_amount) as revenue
        FROM `tabOPS Order`
        WHERE date_purchased >= %s
        GROUP BY DATE(date_purchased)
        ORDER BY date
    """, (start_date,), as_dict=True)

    # Quotes timeline
    quotes_timeline = frappe.db.sql("""
        SELECT DATE(quote_date) as date, COUNT(*) as count, SUM(quote_price) as value
        FROM `tabOPS Quote`
        WHERE quote_date >= %s
        GROUP BY DATE(quote_date)
        ORDER BY date
    """, (start_date,), as_dict=True)

    # Proofs created
    proofs_timeline = frappe.db.sql("""
        SELECT DATE(creation) as date, COUNT(*) as count
        FROM `tabOPS ZiFlow Proof`
        WHERE creation >= %s
        GROUP BY DATE(creation)
        ORDER BY date
    """, (start_date,), as_dict=True)

    # Ensure dates are serialized as strings for JavaScript compatibility
    for item in orders_timeline:
        if item.get("date"):
            item["date"] = str(item["date"])
    for item in quotes_timeline:
        if item.get("date"):
            item["date"] = str(item["date"])
    for item in proofs_timeline:
        if item.get("date"):
            item["date"] = str(item["date"])

    return {
        "orders": orders_timeline,
        "quotes": quotes_timeline,
        "proofs": proofs_timeline
    }


@frappe.whitelist()
def get_pipeline_summary() -> Dict[str, Any]:
    """Get pipeline summary for orders and quotes."""

    # Order pipeline
    order_pipeline_statuses = ["New Order", "In Design", "Order Processing", "In Production", "Ready for Fulfillment"]
    order_pipeline = {}
    for status in order_pipeline_statuses:
        count = frappe.db.count("OPS Order", {"order_status": status})
        value = frappe.db.sql("""
            SELECT COALESCE(SUM(order_amount), 0) as value
            FROM `tabOPS Order`
            WHERE order_status = %s
        """, (status,), as_dict=True)[0].value or 0
        order_pipeline[status] = {"count": count, "value": value}

    # Quote pipeline
    quote_pipeline_statuses = ["Draft", "Pending", "Sent", "Accepted"]
    quote_pipeline = {}
    for status in quote_pipeline_statuses:
        count = frappe.db.count("OPS Quote", {"quote_status": status})
        value = frappe.db.sql("""
            SELECT COALESCE(SUM(quote_price), 0) as value
            FROM `tabOPS Quote`
            WHERE quote_status = %s
        """, (status,), as_dict=True)[0].value or 0
        quote_pipeline[status] = {"count": count, "value": value}

    return {
        "orders": order_pipeline,
        "quotes": quote_pipeline
    }
