"""Dashboard statistics API for OPS Quotes."""

from typing import Any, Dict

import frappe


@frappe.whitelist()
def get_quotes_dashboard_stats() -> Dict[str, Any]:
    """Get OPS Quotes dashboard statistics."""

    # Quotes by status
    status_counts = frappe.db.sql("""
        SELECT quote_status, COUNT(*) as count
        FROM `tabOPS Quote`
        GROUP BY quote_status
    """, as_dict=True)

    by_status = {row.quote_status or "Unknown": row.count for row in status_counts}
    total_quotes = sum(by_status.values())

    # Key status counts
    draft = by_status.get("Draft", 0)
    pending = by_status.get("Pending", 0)
    sent = by_status.get("Sent", 0)
    accepted = by_status.get("Accepted", 0)
    rejected = by_status.get("Rejected", 0)
    expired = by_status.get("Expired", 0)
    converted = by_status.get("Converted", 0)
    cancelled = by_status.get("Cancelled", 0)

    # Active quotes (not converted/cancelled/rejected/expired)
    active_statuses = ["Draft", "Pending", "Sent", "Accepted"]
    active_quotes = sum(by_status.get(s, 0) for s in active_statuses)

    # Value stats
    value_stats = frappe.db.sql("""
        SELECT
            SUM(quote_price) as total_value,
            SUM(CASE WHEN quote_status = 'Converted' THEN quote_price ELSE 0 END) as converted_value,
            SUM(CASE WHEN quote_status = 'Accepted' THEN quote_price ELSE 0 END) as accepted_value,
            AVG(quote_price) as avg_quote_value,
            SUM(profit_margin) as total_profit,
            AVG(profit_percentage) as avg_profit_pct
        FROM `tabOPS Quote`
        WHERE quote_status NOT IN ('Cancelled', 'Rejected')
    """, as_dict=True)[0]

    # Quotes this month
    this_month_start = frappe.utils.get_first_day(frappe.utils.nowdate())
    quotes_this_month = frappe.db.count("OPS Quote", filters={
        "quote_date": [">=", this_month_start]
    })

    # Value this month
    monthly_value = frappe.db.sql("""
        SELECT COALESCE(SUM(quote_price), 0) as value
        FROM `tabOPS Quote`
        WHERE quote_date >= %s
        AND quote_status NOT IN ('Cancelled', 'Rejected')
    """, (this_month_start,), as_dict=True)[0]

    # Quotes today
    quotes_today = frappe.db.count("OPS Quote", filters={
        "quote_date": [">=", frappe.utils.nowdate()]
    })

    # Conversion rate
    convertible = sent + accepted + converted + rejected + expired
    conversion_rate = round((converted / convertible * 100), 1) if convertible > 0 else 0

    # Acceptance rate (accepted + converted out of all sent)
    acceptance_rate = round(((accepted + converted) / convertible * 100), 1) if convertible > 0 else 0

    # Sync status
    sync_pending = frappe.db.count("OPS Quote", filters={"sync_status": "Pending"})
    sync_error = frappe.db.count("OPS Quote", filters={"sync_status": "Error"})

    return {
        "total_quotes": total_quotes,
        "active_quotes": active_quotes,
        "draft": draft,
        "pending": pending,
        "sent": sent,
        "accepted": accepted,
        "rejected": rejected,
        "expired": expired,
        "converted": converted,
        "cancelled": cancelled,
        "quotes_today": quotes_today,
        "quotes_this_month": quotes_this_month,
        "total_value": value_stats.total_value or 0,
        "converted_value": value_stats.converted_value or 0,
        "accepted_value": value_stats.accepted_value or 0,
        "avg_quote_value": round(value_stats.avg_quote_value or 0, 2),
        "monthly_value": monthly_value.value or 0,
        "total_profit": value_stats.total_profit or 0,
        "avg_profit_pct": round(value_stats.avg_profit_pct or 0, 1),
        "conversion_rate": conversion_rate,
        "acceptance_rate": acceptance_rate,
        "sync_pending": sync_pending,
        "sync_error": sync_error,
        "by_status": by_status,
    }


@frappe.whitelist()
def get_quotes_timeline(days: int = 30) -> Dict[str, Any]:
    """Get quote creation timeline for charts."""
    start_date = frappe.utils.add_days(frappe.utils.nowdate(), -int(days))

    timeline = frappe.db.sql("""
        SELECT DATE(quote_date) as date, COUNT(*) as count, SUM(quote_price) as value
        FROM `tabOPS Quote`
        WHERE quote_date >= %s
        GROUP BY DATE(quote_date)
        ORDER BY date
    """, (start_date,), as_dict=True)

    converted = frappe.db.sql("""
        SELECT DATE(modified) as date, COUNT(*) as count, SUM(quote_price) as value
        FROM `tabOPS Quote`
        WHERE modified >= %s AND quote_status = 'Converted'
        GROUP BY DATE(modified)
        ORDER BY date
    """, (start_date,), as_dict=True)

    return {"created": timeline, "converted": converted}


@frappe.whitelist()
def get_recent_quotes(limit: int = 10) -> Dict[str, Any]:
    """Get recently created quotes."""
    quotes = frappe.get_all(
        "OPS Quote",
        fields=["name", "quote_id", "quote_title", "customer_name", "quote_status",
                "quote_price", "quote_date", "profit_margin", "profit_percentage"],
        order_by="quote_date desc",
        limit=int(limit)
    )
    return {"quotes": quotes, "count": len(quotes)}


@frappe.whitelist()
def get_quotes_needing_attention(limit: int = 15) -> Dict[str, Any]:
    """Get quotes that need attention (pending, sent but not responded, sync errors)."""

    # Pending quotes (latest first)
    pending_quotes = frappe.get_all(
        "OPS Quote",
        filters={"quote_status": "Pending"},
        fields=["name", "quote_id", "quote_title", "customer_name", "quote_price", "quote_date"],
        order_by="quote_date desc",
        limit=int(limit)
    )

    # Sent quotes awaiting response (latest first)
    sent_quotes = frappe.get_all(
        "OPS Quote",
        filters={"quote_status": "Sent"},
        fields=["name", "quote_id", "quote_title", "customer_name", "quote_price", "quote_date"],
        order_by="quote_date desc",
        limit=int(limit)
    )

    # Quotes with sync errors
    sync_errors = frappe.get_all(
        "OPS Quote",
        filters={"sync_status": "Error"},
        fields=["name", "quote_id", "quote_title", "customer_name", "sync_error", "quote_date"],
        order_by="modified desc",
        limit=int(limit)
    )

    return {
        "pending": pending_quotes,
        "sent": sent_quotes,
        "sync_errors": sync_errors
    }


@frappe.whitelist()
def get_top_customers_quotes(limit: int = 10) -> Dict[str, Any]:
    """Get top customers by quote count and value."""
    customers = frappe.db.sql("""
        SELECT
            customer_name,
            customer_company,
            COUNT(*) as quote_count,
            SUM(quote_price) as total_value,
            SUM(CASE WHEN quote_status = 'Converted' THEN 1 ELSE 0 END) as converted_count,
            SUM(CASE WHEN quote_status = 'Converted' THEN quote_price ELSE 0 END) as converted_value
        FROM `tabOPS Quote`
        WHERE quote_status NOT IN ('Cancelled')
        AND customer_name IS NOT NULL AND customer_name != ''
        GROUP BY customer_name, customer_company
        ORDER BY total_value DESC
        LIMIT %s
    """, (int(limit),), as_dict=True)

    return {"customers": customers}


@frappe.whitelist()
def get_quotes_pipeline() -> Dict[str, Any]:
    """Get quotes in sales pipeline."""
    pipeline_statuses = ["Draft", "Pending", "Sent", "Accepted"]

    pipeline = {}
    for status in pipeline_statuses:
        quotes = frappe.get_all(
            "OPS Quote",
            filters={"quote_status": status},
            fields=["name", "quote_id", "quote_title", "customer_name", "quote_price", "quote_date"],
            order_by="quote_date desc",
            limit=10
        )
        total_value = frappe.db.sql("""
            SELECT COALESCE(SUM(quote_price), 0) as value
            FROM `tabOPS Quote`
            WHERE quote_status = %s
        """, (status,), as_dict=True)[0]

        pipeline[status] = {
            "count": frappe.db.count("OPS Quote", {"quote_status": status}),
            "value": total_value.value or 0,
            "quotes": quotes
        }

    return pipeline


@frappe.whitelist()
def get_conversion_stats() -> Dict[str, Any]:
    """Get detailed conversion statistics."""

    # Monthly conversion rates
    monthly_stats = frappe.db.sql("""
        SELECT
            DATE_FORMAT(quote_date, '%%Y-%%m') as month,
            COUNT(*) as total,
            SUM(CASE WHEN quote_status = 'Converted' THEN 1 ELSE 0 END) as converted,
            SUM(CASE WHEN quote_status IN ('Accepted', 'Converted') THEN 1 ELSE 0 END) as won,
            SUM(CASE WHEN quote_status = 'Rejected' THEN 1 ELSE 0 END) as lost,
            SUM(quote_price) as total_value,
            SUM(CASE WHEN quote_status = 'Converted' THEN quote_price ELSE 0 END) as converted_value
        FROM `tabOPS Quote`
        WHERE quote_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(quote_date, '%%Y-%%m')
        ORDER BY month
    """, as_dict=True)

    return {"monthly": monthly_stats}


@frappe.whitelist()
def get_quotes_list(
    status: str = None,
    date_from: str = None,
    date_to: str = None,
    customer: str = None,
    value_min: str = None,
    value_max: str = None,
    sync_status: str = None,
    sort_field: str = "quote_date",
    sort_order: str = "desc",
    limit: str = "25",
    offset: str = "0"
):
    """Get paginated quotes list with filters."""
    # Convert string params to proper types
    limit = int(limit) if limit else 25
    offset = int(offset) if offset else 0

    filters = {}
    or_filters = []

    # Status filter (can be comma-separated for multiple)
    if status:
        status_list = [s.strip() for s in status.split(",") if s.strip()]
        if len(status_list) == 1:
            filters["quote_status"] = status_list[0]
        elif len(status_list) > 1:
            or_filters = [["quote_status", "=", s] for s in status_list]

    # Date range filters
    if date_from:
        filters["quote_date"] = [">=", date_from]
    if date_to:
        if "quote_date" in filters:
            filters["quote_date"] = ["between", [date_from, date_to]]
        else:
            filters["quote_date"] = ["<=", date_to]

    # Customer search
    if customer:
        filters["customer_name"] = ["like", f"%{customer}%"]

    # Value range filters
    if value_min:
        try:
            filters["quote_price"] = [">=", float(value_min)]
        except (ValueError, TypeError):
            pass
    if value_max:
        try:
            if "quote_price" in filters:
                filters["quote_price"] = ["between", [float(value_min or 0), float(value_max)]]
            else:
                filters["quote_price"] = ["<=", float(value_max)]
        except (ValueError, TypeError):
            pass

    # Sync status filter
    if sync_status:
        filters["sync_status"] = sync_status

    # Validate sort field
    valid_sort_fields = [
        "quote_date", "quote_id", "customer_name", "quote_status",
        "quote_price", "profit_margin", "profit_percentage", "modified"
    ]
    if sort_field not in valid_sort_fields:
        sort_field = "quote_date"

    # Validate sort order
    sort_order = "desc" if sort_order.lower() != "asc" else "asc"

    # Build order_by
    order_by = f"{sort_field} {sort_order}"

    # Get total count for pagination
    if or_filters:
        total = frappe.db.count("OPS Quote", or_filters=or_filters)
    else:
        total = frappe.db.count("OPS Quote", filters=filters)

    # Get quotes
    quotes = frappe.get_all(
        "OPS Quote",
        filters=filters if not or_filters else None,
        or_filters=or_filters if or_filters else None,
        fields=[
            "name", "quote_id", "quote_title", "customer_name", "customer_company",
            "quote_status", "quote_price", "quote_date", "profit_margin",
            "profit_percentage", "sync_status", "modified"
        ],
        order_by=order_by,
        limit_start=offset,
        limit_page_length=limit
    )

    return {
        "quotes": quotes,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + len(quotes)) < total
    }
