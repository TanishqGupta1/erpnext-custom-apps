"""Sync helpers: webhook handling and polling fallback."""

from __future__ import annotations

import json
import traceback
from typing import Any, Dict

import frappe

from ops_ziflow.services.order_state import update_order_proof_summary
from ops_ziflow.services.ziflow_client import ZiFlowClient
from ops_ziflow.utils.config import load_settings, require_api_key
from ops_ziflow.utils.status_mapper import map_proof_to_product_status


def _safe_truncate(value: str, max_length: int) -> str:
    """Truncate a string to max_length if needed."""
    if value and len(value) > max_length:
        return value[:max_length]
    return value


def _parse_datetime(value: str):
    """Parse ISO 8601 datetime string to datetime object."""
    if not value:
        return None
    try:
        from datetime import datetime
        # Handle ISO 8601 format with Z suffix
        if value.endswith('Z'):
            value = value[:-1] + '+00:00'
        # Try parsing with timezone
        try:
            dt = datetime.fromisoformat(value)
            return dt.replace(tzinfo=None)  # Remove timezone for MySQL compatibility
        except ValueError:
            # Fallback: try parsing common formats
            for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value.split('+')[0].split('Z')[0], fmt)
                except ValueError:
                    continue
        return None
    except Exception:
        return None


def _log_ops_error(
    error_title: str,
    error_message: str,
    error_type: str = "Sync Error",
    severity: str = "Medium",
    source_doctype: str = None,
    source_document: str = None,
    service_name: str = "sync_service",
    function_name: str = None,
    request_data: str = None,
    response_data: str = None,
    auto_retry: bool = False,
):
    """Log error to OPS Error Log."""
    try:
        from ops_ziflow.ops_integration.doctype.ops_error_log.ops_error_log import log_error
        log_error(
            error_title=error_title,
            error_message=error_message,
            error_type=error_type,
            severity=severity,
            source_doctype=source_doctype,
            source_document=source_document,
            service_name=service_name,
            function_name=function_name,
            traceback=traceback.format_exc(),
            request_data=request_data,
            response_data=response_data,
            auto_retry=auto_retry,
        )
    except Exception:
        # Fallback to standard logging if OPS Error Log fails
        frappe.log_error(f"{error_title}: {error_message}", "OPS Sync Error")


def sync_proof_status(ziflow_proof_id: str) -> Dict[str, Any]:
    import json
    settings = load_settings()
    require_api_key(settings)
    client = ZiFlowClient(settings)

    proof_doc = frappe.get_doc("OPS ZiFlow Proof", ziflow_proof_id)
    payload = client.get_proof(ziflow_proof_id)

    # Apply payload directly since custom controller may not be loaded
    if payload:
        proof_doc.ziflow_proof_id = payload.get("id") or proof_doc.ziflow_proof_id
        proof_doc.proof_name = payload.get("name") or proof_doc.proof_name
        proof_doc.proof_status = map_proof_to_product_status(payload.get("status")) or proof_doc.proof_status
        # Map ZiFlow status to OPS status
        ziflow_status = payload.get("status")
        if ziflow_status:
            from ops_ziflow.utils.status_mapper import map_ziflow_status
            proof_doc.proof_status = map_ziflow_status(ziflow_status) or proof_doc.proof_status
        ziflow_url = payload.get("url") or payload.get("share_url")
        if ziflow_url:
            proof_doc.ziflow_url = _safe_truncate(ziflow_url, 140)
        file_url = payload.get("file_url")
        if file_url:
            proof_doc.file_url = _safe_truncate(file_url, 140)
        deadline = payload.get("deadline")
        if deadline:
            proof_doc.deadline = _parse_datetime(deadline) or proof_doc.deadline
        created_at = payload.get("created_at")
        if created_at:
            proof_doc.created_at = _parse_datetime(created_at) or proof_doc.created_at
        approved_at = payload.get("approved_at")
        if approved_at:
            proof_doc.approved_at = _parse_datetime(approved_at) or proof_doc.approved_at
        proof_doc.current_version = payload.get("current_version") or proof_doc.current_version
        proof_doc.total_versions = payload.get("total_versions") or proof_doc.total_versions
        folder = payload.get("folder") or {}
        proof_doc.ziflow_folder_id = payload.get("folder_id") or folder.get("id") or proof_doc.ziflow_folder_id
        proof_doc.folder_name = folder.get("name") or proof_doc.folder_name
        if payload.get("versions"):
            proof_doc.versions_json = json.dumps(payload.get("versions"), indent=2)
        if payload.get("reviewers"):
            proof_doc.reviewers_json = json.dumps(payload.get("reviewers"), indent=2)
        comments = payload.get("comments")
        if comments:
            proof_doc.comments_json = json.dumps(comments, indent=2)
            proof_doc.total_comments = len(comments)
            proof_doc.unresolved_comments = len([c for c in comments if not c.get("resolved")])
        proof_doc.raw_payload = json.dumps(payload, indent=2)
        proof_doc.last_synced = frappe.utils.now_datetime()

    # Clear invalid links before saving
    if proof_doc.ops_order_product and not frappe.db.exists("OPS Order Product", proof_doc.ops_order_product):
        proof_doc.ops_order_product = None

    # Truncate existing long URLs to prevent validation errors
    if proof_doc.file_url and len(proof_doc.file_url) > 140:
        proof_doc.file_url = proof_doc.file_url[:140]
    if proof_doc.ziflow_url and len(proof_doc.ziflow_url) > 140:
        proof_doc.ziflow_url = proof_doc.ziflow_url[:140]

    proof_doc.flags.ignore_links = True
    proof_doc.save(ignore_permissions=True)
    update_linked_product(proof_doc)
    if proof_doc.ops_order:
        update_order_proof_summary(proof_doc.ops_order)
    return {"status": proof_doc.proof_status, "payload": payload}


def poll_pending_proofs() -> None:
    """Scheduler fallback: poll open proofs every 5 minutes.

    Skips proofs that have failed too many times (tracked via sync_error_count).
    """
    from ops_ziflow.utils.errors import ZiFlowError

    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={
            "proof_status": ["in", ["Draft", "In Review", "Changes Requested"]],
        },
        fields=["name", "ziflow_proof_id", "proof_name"],
    )

    for row in proofs:
        try:
            # Check if this proof has failed too many times
            error_count = frappe.db.get_value("OPS ZiFlow Proof", row.name, "sync_error_count") or 0
            if error_count >= 10:
                # Skip proofs that have failed 10+ times - likely deleted from ZiFlow
                continue

            sync_proof_status(row.name)

            # Reset error count on success
            if error_count > 0:
                frappe.db.set_value("OPS ZiFlow Proof", row.name, "sync_error_count", 0, update_modified=False)

        except ZiFlowError as e:
            # ZiFlow API error - could be 404 (deleted) or other API issue
            error_count = (frappe.db.get_value("OPS ZiFlow Proof", row.name, "sync_error_count") or 0) + 1
            frappe.db.set_value("OPS ZiFlow Proof", row.name, {
                "sync_error_count": error_count,
                "last_sync_error": str(e)[:500],
            }, update_modified=False)

            # Only log if first few failures (avoid spam)
            if error_count <= 3:
                _log_ops_error(
                    error_title=f"ZiFlow API error for {row.proof_name or row.name}",
                    error_message=str(e),
                    error_type="API Error",
                    severity="Medium" if error_count == 1 else "Low",
                    source_doctype="OPS ZiFlow Proof",
                    source_document=row.name,
                    function_name="poll_pending_proofs",
                    auto_retry=error_count < 3,
                )
            elif error_count == 10:
                # Log once when we're about to stop retrying
                _log_ops_error(
                    error_title=f"ZiFlow proof sync disabled after 10 failures: {row.proof_name or row.name}",
                    error_message=f"Proof will no longer be polled. Last error: {e}",
                    error_type="API Error",
                    severity="High",
                    source_doctype="OPS ZiFlow Proof",
                    source_document=row.name,
                    function_name="poll_pending_proofs",
                    auto_retry=False,
                )

        except Exception as e:
            # Other unexpected errors
            _log_ops_error(
                error_title=f"ZiFlow poll failed for {row.proof_name or row.name}",
                error_message=str(e),
                error_type="Sync Error",
                severity="Medium",
                source_doctype="OPS ZiFlow Proof",
                source_document=row.name,
                function_name="poll_pending_proofs",
                auto_retry=True,
            )


def handle_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process ZiFlow webhook events."""
    proof_id = (
        payload.get("ziflow_proof_id")
        or payload.get("proof_id")
        or (payload.get("proof") or {}).get("id")
        or payload.get("id")
    )
    if not proof_id:
        _log_ops_error(
            error_title="ZiFlow webhook missing proof id",
            error_message="Webhook payload did not contain a valid proof ID",
            error_type="Webhook Error",
            severity="High",
            function_name="handle_webhook",
            request_data=json.dumps(payload, indent=2),
        )
        return {"error": "missing proof id"}

    settings = load_settings()
    require_api_key(settings)
    client = ZiFlowClient(settings)

    proof_doc = frappe.get_doc("OPS ZiFlow Proof", proof_id)
    proof_payload = payload.get("proof") or client.get_proof(proof_id)
    proof_doc.apply_ziflow_payload(proof_payload)
    proof_doc.save(ignore_permissions=True)
    update_linked_product(proof_doc)
    update_order_proof_summary(proof_doc.ops_order)

    event_type = payload.get("event")
    if event_type:
        add_order_comment(proof_doc.ops_order, f"ZiFlow event {event_type} for proof {proof_doc.proof_name}")

    return {"status": proof_doc.proof_status}


def update_linked_product(proof_doc) -> None:
    """Propagate proof status to OPS Order Product."""
    if not proof_doc.ops_order_product:
        return

    product_status = map_proof_to_product_status(proof_doc.proof_status) or "Pending"
    frappe.db.set_value("OPS Order Product", proof_doc.ops_order_product, {
        "ziflow_proof_status": product_status,
        "ziflow_proof_url": proof_doc.ziflow_url,
        "ziflow_approved_at": proof_doc.approved_at,
        "ziflow_version": proof_doc.current_version or 1,
    })


def add_order_comment(order_name: str, content: str) -> None:
    if not order_name:
        return
    try:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "OPS Order",
            "reference_name": order_name,
            "content": content,
        }).insert(ignore_permissions=True)
    except Exception as e:
        _log_ops_error(
            error_title=f"Failed to add ZiFlow comment on {order_name}",
            error_message=str(e),
            error_type="Sync Error",
            severity="Low",
            source_doctype="OPS Order",
            source_document=order_name,
            function_name="add_order_comment",
        )
