# Copyright (c) 2025, Visual Graphx
# License: MIT

"""Top Customers Report - Shows customers ranked by total revenue."""

import frappe
from frappe import _


def execute(filters=None):
    """Execute the Top Customers report."""
    if filters is None:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    """Define report columns."""
    return [
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Data",
            "width": 250
        },
        {
            "label": _("Order Count"),
            "fieldname": "order_count",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Total Revenue"),
            "fieldname": "total_revenue",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Average Order Value"),
            "fieldname": "avg_order_value",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("First Order"),
            "fieldname": "first_order",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": _("Last Order"),
            "fieldname": "last_order",
            "fieldtype": "Date",
            "width": 110
        }
    ]


def get_data(filters):
    """Fetch report data based on filters."""
    conditions = []
    values = {}

    # Build conditions only if filters are provided
    # Use date_purchased field (the actual column in OPS Order)
    if filters.get("from_date"):
        conditions.append("DATE(o.date_purchased) >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("DATE(o.date_purchased) <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    # Build WHERE clause
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get limit (default 10)
    limit = filters.get("limit") or 10
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 10

    # Main SQL query
    # Using customer_name field (actual column in tabOPS Order)
    query = f"""
        SELECT
            o.customer_name AS customer,
            COUNT(o.name) AS order_count,
            COALESCE(SUM(o.total_amount), 0) AS total_revenue,
            COALESCE(AVG(o.total_amount), 0) AS avg_order_value,
            MIN(DATE(o.date_purchased)) AS first_order,
            MAX(DATE(o.date_purchased)) AS last_order
        FROM
            `tabOPS Order` o
        WHERE
            o.docstatus < 2
            AND o.customer_name IS NOT NULL
            AND o.customer_name != ''
            AND {where_clause}
        GROUP BY
            o.customer_name
        ORDER BY
            total_revenue DESC
        LIMIT {limit}
    """

    return frappe.db.sql(query, values, as_dict=True)
