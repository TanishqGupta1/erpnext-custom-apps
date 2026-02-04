# Copyright (c) 2024, Visual Graphx and contributors
# For license information, please see license.txt

"""
Customer 360 View API
Provides whitelisted methods to fetch Orders, Proofs, and Timeline data
for the Customer form embedded tabs.

Field Mapping:
- ERPNext Customer.ops_corporate_id -> OPS Customer.name (the link ID)
- OPS Order.erp_customer -> OPS Customer.name (Link field)
- OPS ZiFlow Proof.ops_order -> OPS Order.name
"""

import frappe
from frappe import _
from frappe.utils import add_months, nowdate
import re


def _get_ops_customer_id(customer_name):
    """
    Get the OPS Customer ID (ops_corporate_id) for an ERPNext Customer.

    Args:
        customer_name: ERPNext Customer doctype name

    Returns:
        str: The ops_corporate_id or None
    """
    return frappe.db.get_value("Customer", customer_name, "ops_corporate_id")


@frappe.whitelist()
def get_customer_orders(customer_name, limit=50, offset=0):
    """
    Fetch OPS Orders for a customer (last 6 months).

    Args:
        customer_name: The ERPNext Customer doctype name
        limit: Number of records to fetch (pagination)
        offset: Offset for pagination

    Returns:
        dict with 'data' (list of orders) and 'total' (count)
    """
    if not customer_name:
        return {"data": [], "total": 0}

    # Permission check
    if not frappe.has_permission("OPS Order", "read"):
        frappe.throw(_("You don't have permission to view orders"), frappe.PermissionError)

    # Get OPS Customer ID from ERPNext Customer
    ops_customer_id = _get_ops_customer_id(customer_name)

    if not ops_customer_id:
        return {"data": [], "total": 0, "message": "No OPS Customer ID linked"}

    # Calculate 12 months ago
    twelve_months_ago = add_months(nowdate(), -12)

    # Build filters - erp_customer links to OPS Customer
    filters = {
        "erp_customer": ops_customer_id,
        "orders_date_finished": [">=", twelve_months_ago]
    }

    # Get total count for pagination
    total = frappe.db.count("OPS Order", filters=filters)

    # Fetch orders
    orders = frappe.get_all(
        "OPS Order",
        filters=filters,
        fields=[
            "name",
            "ops_order_id",
            "order_name",
            "orders_date_finished",
            "order_status",
            "payment_status_title",
            "total_amount",
            "customer_name",
            "order_amount"
        ],
        order_by="orders_date_finished desc",
        limit_page_length=int(limit),
        start=int(offset)
    )

    # Format dates for display
    for order in orders:
        if order.get("orders_date_finished"):
            order["orders_date_finished"] = frappe.utils.format_datetime(
                order["orders_date_finished"], "dd-MM-yyyy HH:mm"
            )
        if order.get("total_amount"):
            order["total_amount"] = frappe.utils.fmt_money(
                order["total_amount"], currency="USD"
            )

    return {
        "data": orders,
        "total": total
    }


@frappe.whitelist()
def get_customer_proofs(customer_name, limit=50, offset=0):
    """
    Fetch OPS ZiFlow Proofs for a customer.

    Chain: ERPNext Customer -> ops_corporate_id -> OPS Orders -> OPS ZiFlow Proofs

    Args:
        customer_name: The ERPNext Customer doctype name
        limit: Number of records to fetch
        offset: Offset for pagination

    Returns:
        dict with 'data' (list of proofs) and 'total' (count)
    """
    if not customer_name:
        return {"data": [], "total": 0}

    # Permission check
    if not frappe.has_permission("OPS ZiFlow Proof", "read"):
        frappe.throw(_("You don't have permission to view proofs"), frappe.PermissionError)

    # Get OPS Customer ID from ERPNext Customer
    ops_customer_id = _get_ops_customer_id(customer_name)

    if not ops_customer_id:
        return {"data": [], "total": 0, "message": "No OPS Customer ID linked"}

    # Get all OPS Order names for this customer
    customer_orders = frappe.get_all(
        "OPS Order",
        filters={"erp_customer": ops_customer_id},
        pluck="name"
    )

    if not customer_orders:
        return {"data": [], "total": 0}

    # Build filters for proofs
    filters = {
        "ops_order": ["in", customer_orders]
    }

    # Get total count
    total = frappe.db.count("OPS ZiFlow Proof", filters=filters)

    # Fetch proofs
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters=filters,
        fields=[
            "name",
            "ziflow_proof_id",
            "proof_name",
            "proof_status",
            "created_at",
            "modified",
            "deadline",
            "ziflow_url",
            "ops_order",
            "current_version",
            "total_comments",
            "unresolved_comments"
        ],
        order_by="modified desc",
        limit_page_length=int(limit),
        start=int(offset)
    )

    # Format dates
    for proof in proofs:
        if proof.get("modified"):
            proof["modified"] = frappe.utils.format_datetime(
                proof["modified"], "dd-MM-yyyy HH:mm"
            )
        if proof.get("created_at"):
            proof["created_at"] = frappe.utils.format_datetime(
                proof["created_at"], "dd-MM-yyyy HH:mm"
            )
        if proof.get("deadline"):
            proof["deadline"] = frappe.utils.format_datetime(
                proof["deadline"], "dd-MM-yyyy HH:mm"
            )

    return {
        "data": proofs,
        "total": total
    }


@frappe.whitelist()
def get_customer_timeline(customer_name, limit=50, offset=0):
    """
    Fetch Communications for a customer using the standard Frappe Communication doctype.
    Shows unified timeline of Email, Phone, Chat, etc.

    Args:
        customer_name: The ERPNext Customer doctype name
        limit: Number of records to fetch
        offset: Offset for pagination

    Returns:
        dict with 'data' (list of communications) and 'total' (count)
    """
    if not customer_name:
        return {"data": [], "total": 0}

    # Permission check - Communication is a standard doctype
    if not frappe.has_permission("Communication", "read"):
        frappe.throw(_("You don't have permission to view communications"), frappe.PermissionError)

    # Calculate 6 months ago
    six_months_ago = add_months(nowdate(), -6)

    # Build filters - Communications linked to this Customer
    filters = {
        "reference_doctype": "Customer",
        "reference_name": customer_name,
        "communication_date": [">=", six_months_ago]
    }

    # Get total count
    total = frappe.db.count("Communication", filters=filters)

    # Fetch communications
    communications = frappe.get_all(
        "Communication",
        filters=filters,
        fields=[
            "name",
            "subject",
            "communication_type",
            "communication_medium",
            "communication_date",
            "sent_or_received",
            "sender",
            "sender_full_name",
            "recipients",
            "content",
            "has_attachment",
            "seen",
            "read_by_recipient",
            "delivery_status",
            "phone_no"
        ],
        order_by="communication_date desc",
        limit_page_length=int(limit),
        start=int(offset)
    )

    # Format and enrich data
    for comm in communications:
        # Format date
        if comm.get("communication_date"):
            comm["communication_date_formatted"] = frappe.utils.format_datetime(
                comm["communication_date"], "dd-MM-yyyy HH:mm"
            )

        # Truncate content for summary
        content = comm.get("content", "") or ""
        # Strip HTML tags for preview
        text_content = re.sub('<[^<]+?>', '', content)
        comm["content_preview"] = text_content[:150] + "..." if len(text_content) > 150 else text_content

        # Determine channel/icon based on communication_type and communication_medium
        comm["channel"] = _get_communication_channel(comm)

    return {
        "data": communications,
        "total": total
    }


def _get_communication_channel(comm):
    """Determine the channel type for display."""
    comm_type = comm.get("communication_type", "")
    comm_medium = comm.get("communication_medium", "")

    if comm_medium:
        return comm_medium

    if comm_type == "Email":
        return "Email"
    elif comm_type == "Chat":
        return "Chat"
    elif comm_type == "Phone":
        return "Voice"
    elif comm_type == "SMS":
        return "SMS"
    elif comm_type == "Event":
        return "Event"
    elif comm_type == "Meeting":
        return "Meeting"
    elif comm_type == "Visit":
        return "Visit"
    else:
        return comm_type or "Other"


@frappe.whitelist()
def get_customer_360_summary(customer_name):
    """
    Get a quick summary/count for badge display on tabs.

    Args:
        customer_name: The ERPNext Customer doctype name

    Returns:
        dict with counts for orders, proofs, communications
    """
    if not customer_name:
        return {"orders": 0, "proofs": 0, "communications": 0}

    twelve_months_ago = add_months(nowdate(), -12)
    six_months_ago = add_months(nowdate(), -6)

    # Get OPS Customer ID
    ops_customer_id = _get_ops_customer_id(customer_name)

    # Count orders (last 12 months)
    orders_count = 0
    if ops_customer_id and frappe.has_permission("OPS Order", "read"):
        try:
            orders_count = frappe.db.count(
                "OPS Order",
                filters={
                    "erp_customer": ops_customer_id,
                    "orders_date_finished": [">=", twelve_months_ago]
                }
            )
        except Exception:
            orders_count = 0

    # Count proofs via orders
    proofs_count = 0
    if ops_customer_id and frappe.has_permission("OPS ZiFlow Proof", "read"):
        try:
            customer_orders = frappe.get_all(
                "OPS Order",
                filters={"erp_customer": ops_customer_id},
                pluck="name"
            )
            if customer_orders:
                proofs_count = frappe.db.count(
                    "OPS ZiFlow Proof",
                    filters={"ops_order": ["in", customer_orders]}
                )
        except Exception:
            proofs_count = 0

    # Count communications (last 6 months) - using standard Communication doctype
    comms_count = 0
    if frappe.has_permission("Communication", "read"):
        try:
            comms_count = frappe.db.count(
                "Communication",
                filters={
                    "reference_doctype": "Customer",
                    "reference_name": customer_name,
                    "communication_date": [">=", six_months_ago]
                }
            )
        except Exception:
            comms_count = 0

    return {
        "orders": orders_count,
        "proofs": proofs_count,
        "communications": comms_count
    }
