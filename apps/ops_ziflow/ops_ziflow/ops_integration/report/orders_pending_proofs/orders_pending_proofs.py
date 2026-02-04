"""Orders Pending Proofs Report - Shows orders with proofs awaiting approval."""

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "name",
            "label": "Order",
            "fieldtype": "Link",
            "options": "OPS Order",
            "width": 150,
        },
        {
            "fieldname": "customer_name",
            "label": "Customer",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "order_date",
            "label": "Order Date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "fieldname": "pending_proof_count",
            "label": "Pending Proofs",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "fieldname": "total_proofs",
            "label": "Total Proofs",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "fieldname": "oldest_pending",
            "label": "Oldest Pending Since",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "fieldname": "status",
            "label": "Order Status",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def get_data(filters):
    conditions = []
    values = {}

    if filters and filters.get("customer"):
        conditions.append("o.ops_customer = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters and filters.get("from_date"):
        conditions.append("o.order_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters and filters.get("to_date"):
        conditions.append("o.order_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    data = frappe.db.sql(
        f"""
        SELECT
            o.name,
            o.ops_customer as customer_name,
            o.order_date,
            o.pending_proof_count,
            (SELECT COUNT(*) FROM `tabOPS ZiFlow Proof` p WHERE p.ops_order = o.name) as total_proofs,
            (SELECT MIN(p.creation) FROM `tabOPS ZiFlow Proof` p
             WHERE p.ops_order = o.name AND p.proof_status IN ('Draft', 'In Review', 'Changes Requested')) as oldest_pending,
            o.status
        FROM `tabOPS Order` o
        WHERE o.all_proofs_approved = 0
          AND o.pending_proof_count > 0
          AND {where_clause}
        ORDER BY o.pending_proof_count DESC, o.order_date ASC
        """,
        values,
        as_dict=True,
    )

    return data
