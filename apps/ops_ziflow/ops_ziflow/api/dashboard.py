"""Dashboard statistics API for ZiFlow integration."""

from typing import Any, Dict

import frappe


@frappe.whitelist()
def get_dashboard_stats() -> Dict[str, Any]:
    """Get ZiFlow dashboard statistics for number cards and charts."""
    status_counts = frappe.db.sql("""
        SELECT proof_status, COUNT(*) as count
        FROM `tabOPS ZiFlow Proof`
        GROUP BY proof_status
    """, as_dict=True)

    by_status = {row.proof_status: row.count for row in status_counts}
    total_proofs = sum(by_status.values())
    pending_count = by_status.get("Draft", 0) + by_status.get("In Review", 0) + by_status.get("Changes Requested", 0)
    approved_count = by_status.get("Approved", 0)
    rejected_count = by_status.get("Rejected", 0)

    overdue_count = frappe.db.count("OPS ZiFlow Proof", filters={
        "proof_status": ["in", ["Draft", "In Review", "Changes Requested"]],
        "deadline": ["<", frappe.utils.nowdate()]
    })

    recent_count = frappe.db.count("OPS ZiFlow Proof", filters={
        "modified": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
    })

    orders_pending = frappe.db.count("OPS Order", filters={
        "all_proofs_approved": 0,
        "pending_proof_count": [">", 0]
    })

    avg_comments = frappe.db.sql("""
        SELECT AVG(total_comments) as avg_comments FROM `tabOPS ZiFlow Proof`
    """, as_dict=True)

    return {
        "total_proofs": total_proofs,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "overdue_count": overdue_count,
        "recent_activity": recent_count,
        "orders_pending_proofs": orders_pending,
        "avg_comments": round(avg_comments[0].avg_comments or 0, 1) if avg_comments else 0,
        "by_status": by_status,
        "approval_rate": round((approved_count / total_proofs * 100) if total_proofs > 0 else 0, 1),
    }


@frappe.whitelist()
def get_proof_timeline(days: int = 30) -> Dict[str, Any]:
    """Get proof creation timeline for charts."""
    start_date = frappe.utils.add_days(frappe.utils.nowdate(), -int(days))

    timeline = frappe.db.sql("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM `tabOPS ZiFlow Proof`
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY date
    """, (start_date,), as_dict=True)

    approvals = frappe.db.sql("""
        SELECT DATE(approved_at) as date, COUNT(*) as count
        FROM `tabOPS ZiFlow Proof`
        WHERE approved_at >= %s AND approved_at IS NOT NULL
        GROUP BY DATE(approved_at)
        ORDER BY date
    """, (start_date,), as_dict=True)

    return {"created": timeline, "approved": approvals}


@frappe.whitelist()
def get_overdue_count() -> int:
    """Get count of overdue proofs for Number Card."""
    return frappe.db.count("OPS ZiFlow Proof", filters={
        "proof_status": ["in", ["Draft", "In Review", "Changes Requested"]],
        "deadline": ["<", frappe.utils.nowdate()]
    })


@frappe.whitelist()
def get_overdue_proofs(limit: int = 20) -> Dict[str, Any]:
    """Get list of overdue proofs that need attention."""
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={
            "proof_status": ["in", ["Draft", "In Review", "Changes Requested"]],
            "deadline": ["<", frappe.utils.nowdate()]
        },
        fields=["name", "proof_name", "proof_status", "deadline", "ziflow_url", "ops_order", "unresolved_comments"],
        order_by="deadline asc",
        limit=int(limit)
    )
    return {"proofs": proofs, "count": len(proofs)}


@frappe.whitelist()
def get_recent_proofs(limit: int = 10) -> Dict[str, Any]:
    """Get recently updated proofs."""
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        fields=["name", "proof_name", "proof_status", "modified", "ziflow_url", "ops_order", "current_version"],
        order_by="modified desc",
        limit=int(limit)
    )
    return {"proofs": proofs, "count": len(proofs)}


@frappe.whitelist()
def get_proofs_by_order(ops_order: str) -> Dict[str, Any]:
    """Get all proofs linked to a specific order."""
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={"ops_order": ops_order},
        fields=["name", "proof_name", "proof_status", "ziflow_url", "deadline", "approved_at", "current_version", "total_comments", "unresolved_comments"],
        order_by="creation desc"
    )
    return {
        "proofs": proofs,
        "count": len(proofs),
        "all_approved": all(p.proof_status == "Approved" for p in proofs) if proofs else False,
        "pending_count": sum(1 for p in proofs if p.proof_status != "Approved")
    }


@frappe.whitelist()
def get_proofs_by_customer(ops_customer: str) -> Dict[str, Any]:
    """Get all proofs linked to a specific customer."""
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={"ops_customer": ops_customer},
        fields=["name", "proof_name", "proof_status", "ziflow_url", "ops_order", "deadline", "approved_at"],
        order_by="creation desc",
        limit=50
    )
    status_counts = {}
    for p in proofs:
        status_counts[p.proof_status] = status_counts.get(p.proof_status, 0) + 1
    return {"proofs": proofs, "count": len(proofs), "by_status": status_counts}
