"""Backfill existing ZiFlow proofs into Frappe."""

from __future__ import annotations

import json
import traceback
from datetime import datetime

import frappe

from ops_ziflow.services.ziflow_client import ZiFlowClient
from ops_ziflow.utils.config import load_settings, require_api_key
from ops_ziflow.utils.errors import ZiFlowError
from ops_ziflow.utils.status_mapper import map_ziflow_status


def _log_ops_error(
    error_title: str,
    error_message: str,
    error_type: str = "Sync Error",
    severity: str = "Medium",
    source_doctype: str = None,
    source_document: str = None,
    service_name: str = "import_service",
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
        frappe.log_error(f"{error_title}: {error_message}", "OPS Import Error")


def _parse_iso_datetime(value: str | None) -> str | None:
    """Convert ISO 8601 datetime string to MySQL-compatible format."""
    if not value:
        return None
    try:
        # Handle ISO 8601 format with Z suffix or timezone
        if isinstance(value, str):
            # Remove 'Z' suffix and parse
            clean_value = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_value)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        pass
    return None


def _extract_items(payload: dict | list) -> list:
    """Return list of proofs from varied ZiFlow list response shapes."""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    return payload.get("data") or payload.get("proofs") or payload.get("items") or []


def sync_all_proofs(
    page_size: int = 50,
    max_pages: int = 20,
    folder_id: str | None = None,
    include_comments: bool = False,
) -> dict:
    """Import/sync existing ZiFlow proofs into OPS ZiFlow Proof DocType.

    Args:
        page_size: records per page from ZiFlow list endpoint.
        max_pages: safety cap to avoid runaway syncs.
        folder_id: optional ZiFlow folder filter.
        include_comments: if True, fetch comments per proof.
    """
    settings = load_settings()
    require_api_key(settings)
    client = ZiFlowClient(settings)

    inserted = 0
    updated = 0
    errors: list[str] = []

    for page in range(1, max_pages + 1):
        list_resp = client.list_proofs(page=page, page_size=page_size, folder_id=folder_id)
        items = _extract_items(list_resp)
        if not items:
            break

        for item in items:
            proof_id = item.get("id")
            if not proof_id:
                continue
            try:
                detail = client.get_proof(proof_id)
                if include_comments:
                    comments = client.get_comments(proof_id)
                    detail["comments"] = comments.get("data") or comments.get("comments") or comments
                created = upsert_proof(detail or item)
                if created:
                    inserted += 1
                else:
                    updated += 1
            except ZiFlowError as exc:
                errors.append(f"{proof_id}: {exc}")
                _log_ops_error(
                    error_title=f"ZiFlow API error importing proof {proof_id}",
                    error_message=str(exc),
                    error_type="API Error",
                    severity="Medium",
                    source_doctype="OPS ZiFlow Proof",
                    source_document=proof_id,
                    function_name="sync_all_proofs",
                    auto_retry=True,
                )
            except Exception as e:
                errors.append(f"{proof_id}: unexpected error")
                _log_ops_error(
                    error_title=f"ZiFlow import failed for {proof_id}",
                    error_message=str(e),
                    error_type="Sync Error",
                    severity="High",
                    source_doctype="OPS ZiFlow Proof",
                    source_document=proof_id,
                    function_name="sync_all_proofs",
                    auto_retry=True,
                )

        if len(items) < page_size:
            break

    return {"inserted": inserted, "updated": updated, "errors": errors}


def _extract_preview_url(payload: dict) -> str | None:
    """Extract preview/thumbnail URL from ZiFlow API response.

    Checks common locations for preview URLs in the payload.
    ZiFlow uses 'image_link' for larger preview and 'thumbnail_link' for small thumbnail.
    """
    # ZiFlow specific fields (prefer larger image_link over thumbnail_link)
    if payload.get("image_link"):
        return payload["image_link"]
    if payload.get("thumbnail_link"):
        return payload["thumbnail_link"]

    # Check other common field names
    for key in ("thumbnail_url", "preview_url", "thumbnail", "preview", "image_url"):
        if payload.get(key):
            return payload[key]

    # Check versions array for the latest version's thumbnail
    versions = payload.get("versions") or []
    if versions and isinstance(versions, list):
        # Get the latest version (usually first or last depending on sort)
        latest = versions[-1] if versions else None
        if latest and isinstance(latest, dict):
            for key in ("image_link", "thumbnail_link", "thumbnail_url", "preview_url", "thumbnail", "preview", "image_url"):
                if latest.get(key):
                    return latest[key]

    return None


def _parse_pass_through_value(payload: dict) -> tuple:
    """Extract OPS Order ID and Line ID from pass_through_value.

    pass_through_value format: "ORDER_ID|LINE_ID"
    Returns: (order_id, line_id) or (None, None) if not found/parseable
    """
    ptv = payload.get("pass_through_value")
    if not ptv or not isinstance(ptv, str):
        return None, None

    parts = ptv.split("|")
    if len(parts) >= 2:
        order_id = parts[0].strip() if parts[0].strip() else None
        line_id = parts[1].strip() if parts[1].strip() else None
        return order_id, line_id
    elif len(parts) == 1 and parts[0].strip():
        return parts[0].strip(), None
    return None, None


def _get_ops_order_and_customer(order_id: str) -> tuple:
    """Look up OPS Order and get customer info.

    Returns: (order_name, customer_name) or (None, None) if not found
    """
    if not order_id:
        return None, None

    # Look up OPS Order by ops_order_id field
    order_name = frappe.db.get_value("OPS Order", {"ops_order_id": order_id}, "name")
    if not order_name:
        # Try looking up by name directly
        if frappe.db.exists("OPS Order", order_id):
            order_name = order_id

    if not order_name:
        return None, None

    # Get customer from the order (customer_company is a Link field)
    customer = frappe.db.get_value("OPS Order", order_name, "customer_company")
    return order_name, customer


def upsert_proof(payload: dict) -> bool:
    """Create or update a single OPS ZiFlow Proof from payload.

    Returns:
        True if a new record was inserted, False if an existing record was updated.
    """
    proof_id = payload.get("id") or payload.get("ziflow_proof_id")
    if not proof_id:
        return False

    created = False
    # Look up by ziflow_proof_id field since doc name may differ from UUID
    existing = frappe.db.get_value("OPS ZiFlow Proof", {"ziflow_proof_id": proof_id}, "name")
    if existing:
        doc = frappe.get_doc("OPS ZiFlow Proof", existing)
    else:
        doc = frappe.new_doc("OPS ZiFlow Proof")
        created = True

    # Directly map fields since custom DocType doesn't load Python controller
    doc.ziflow_proof_id = payload.get("id") or doc.get("ziflow_proof_id")
    doc.proof_name = payload.get("name") or doc.get("proof_name") or "Unknown"
    doc.proof_status = map_ziflow_status(payload.get("status")) or doc.get("proof_status") or "Draft"
    doc.ziflow_url = payload.get("url") or payload.get("share_url") or payload.get("public_link") or doc.get("ziflow_url")
    doc.file_url = payload.get("file_url") or doc.get("file_url")
    doc.preview_url = _extract_preview_url(payload) or doc.get("preview_url")
    doc.deadline = _parse_iso_datetime(payload.get("deadline")) or doc.get("deadline")
    doc.created_at = _parse_iso_datetime(payload.get("created_at")) or doc.get("created_at")
    doc.approved_at = _parse_iso_datetime(payload.get("approved_at")) or doc.get("approved_at")
    doc.current_version = payload.get("current_version") or payload.get("version") or doc.get("current_version")
    doc.total_versions = payload.get("total_versions") or doc.get("total_versions")

    # Extract OPS Order and Customer from pass_through_value
    order_id, line_id = _parse_pass_through_value(payload)
    if order_id or line_id:
        doc.ops_line_id = line_id or doc.get("ops_line_id")
        order_name, customer_name = _get_ops_order_and_customer(order_id)
        if order_name:
            doc.ops_order = order_name
        if customer_name:
            doc.ops_customer = customer_name

    folder = payload.get("folder") or {}
    doc.ziflow_folder_id = payload.get("folder_id") or folder.get("id") or doc.get("ziflow_folder_id")
    doc.folder_name = folder.get("name") or doc.get("folder_name")

    template = payload.get("template") or {}
    doc.template_id = payload.get("template_id") or template.get("id") or doc.get("template_id")
    doc.template_name = template.get("name") or doc.get("template_name")

    if payload.get("versions"):
        doc.versions_json = json.dumps(payload.get("versions"), indent=2)
    if payload.get("reviewers"):
        doc.reviewers_json = json.dumps(payload.get("reviewers"), indent=2)

    comments = payload.get("comments")
    if comments:
        doc.comments_json = json.dumps(comments, indent=2)
        doc.total_comments = len(comments)
        unresolved = [c for c in comments if not c.get("resolved")]
        doc.unresolved_comments = len(unresolved)

    doc.raw_payload = json.dumps(payload, indent=2)
    doc.last_synced = frappe.utils.now_datetime()

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)
    return created
