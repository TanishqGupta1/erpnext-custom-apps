import json
from typing import Any, Dict

import frappe

from ops_ziflow.services import proof_service, sync_service
from ops_ziflow.services import import_service
from ops_ziflow.services.order_state import update_order_proof_summary


@frappe.whitelist()
def create_ziflow_proof(ops_order_product: str) -> Dict[str, Any]:
    """Create ZiFlow proof for an OPS Order Product."""
    return proof_service.create_proof_for_order_product(ops_order_product)


@frappe.whitelist()
def sync_proof_status(ziflow_proof_id: str) -> Dict[str, Any]:
    """Sync proof status from ZiFlow."""
    return sync_service.sync_proof_status(ziflow_proof_id)


@frappe.whitelist(allow_guest=True)
def ziflow_webhook() -> Dict[str, Any]:
    """Handle ZiFlow webhook callbacks."""
    payload = _get_request_json()
    return sync_service.handle_webhook(payload)

        
@frappe.whitelist()
def bulk_create_proofs(ops_order: str) -> Dict[str, Any]:
    """Create proofs for all products in an order."""
    return proof_service.bulk_create_proofs(ops_order)


@frappe.whitelist()
def get_proof_summary(ops_order: str) -> Dict[str, Any]:
    """Return proof summary for an order."""
    update_order_proof_summary(ops_order)
    order = frappe.get_doc("OPS Order", ops_order)
    return {
        "all_proofs_approved": order.get("all_proofs_approved"),
        "pending_proof_count": order.get("pending_proof_count"),
        "summary_html": order.get("ziflow_proofs_html"),
    }


@frappe.whitelist()
def backfill_ziflow_proofs(folder_id: str | None = None, include_comments: int = 0, page_size: int = 50, max_pages: int = 20) -> Dict[str, Any]:
    """Pull existing ZiFlow proofs into Frappe (idempotent).

    Args:
        folder_id: optional ZiFlow folder to scope import.
        include_comments: 1/0 to also fetch comments per proof.
        page_size: ZiFlow page size.
        max_pages: limit for pagination.
    """
    return import_service.sync_all_proofs(
        page_size=int(page_size),
        max_pages=int(max_pages),
        folder_id=folder_id or None,
        include_comments=bool(int(include_comments)),
    )


@frappe.whitelist()
def upsert_ziflow_payload(payload: Dict[str, Any] | str) -> Dict[str, Any]:
    """Upsert a single ZiFlow proof payload into OPS ZiFlow Proof.

    Accepts a dict or JSON string payload in ZiFlow proof format.
    """
    if isinstance(payload, str):
        payload = json.loads(payload)
    created = import_service.upsert_proof(payload or {})
    return {
        "created": created,
        "name": payload.get("id") or payload.get("ziflow_proof_id"),
    }


def _get_request_json() -> Dict[str, Any]:
    if frappe.request and frappe.request.data:
        try:
            return json.loads(frappe.request.data)
        except Exception:
            pass
    if frappe.local.form_dict:
        return dict(frappe.local.form_dict)
    return {}
