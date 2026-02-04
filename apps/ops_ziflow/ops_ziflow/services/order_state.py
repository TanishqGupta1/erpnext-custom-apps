"""Order-level rollup helpers for ZiFlow proofs."""

from __future__ import annotations

import frappe


def update_order_proof_summary(order_name: str) -> None:
    """Update order-level proof summary fields based on linked products."""
    if not frappe.db.exists("OPS Order", order_name):
        return

    products = frappe.get_all(
        "OPS Order Product",
        filters={"parent": order_name},
        fields=[
            "name",
            "products_name",
            "ziflow_proof_status",
            "ziflow_proof_url",
            "ziflow_proof",
        ],
    )
    pending = [
        p for p in products if not p.get("ziflow_proof_status") or p["ziflow_proof_status"] != "Approved"
    ]
    all_approved = bool(products) and len(pending) == 0

    # Simple HTML summary for desk view
    rows = []
    for p in products:
        status = p.get("ziflow_proof_status") or "Pending"
        url = p.get("ziflow_proof_url") or ""
        link_html = f'<a href="{url}" target="_blank">{p.get("products_name")}</a>' if url else p.get("products_name")
        rows.append(f"<div><strong>{link_html}</strong>: {status}</div>")
    summary_html = "\n".join(rows) if rows else "No proofs yet."

    frappe.db.set_value("OPS Order", order_name, {
        "all_proofs_approved": 1 if all_approved else 0,
        "pending_proof_count": len(pending),
        "ziflow_proofs_html": summary_html,
    })
