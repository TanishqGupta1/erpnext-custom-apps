"""Proof creation and automation flows."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Dict, List

import frappe
from frappe.utils import add_days, get_datetime, now_datetime

from ops_ziflow.services.order_state import update_order_proof_summary
from ops_ziflow.services.ziflow_client import ZiFlowClient
from ops_ziflow.utils.config import load_settings, require_api_key
from ops_ziflow.utils.errors import MissingConfigurationError, ZiFlowError
from ops_ziflow.utils.status_mapper import map_proof_to_product_status, map_ziflow_status

TRIGGER_STATUSES = {"In Design", "Order Review"}


def handle_order_status_change(doc, method=None):
    """Hook: create proofs when OPS Order enters a proofing status."""
    if getattr(frappe.flags, "in_patch", False) or getattr(frappe.flags, "in_install", False):
        return
    try:
        previous = doc.get_db_value("order_status") if not doc.is_new() else None
    except Exception:
        previous = None

    current = getattr(doc, "order_status", None)
    if not current or current not in TRIGGER_STATUSES or previous == current:
        return

    # Avoid duplicate attempts if proofs already exist
    for child in doc.get("ops_order_products", []):
        if getattr(child, "ziflow_proof", None):
            continue
        try:
            create_proof_for_order_product(child.name, order_doc=doc)
        except MissingConfigurationError as exc:
            frappe.log_error(f"ZiFlow configuration missing for product {child.name}: {exc}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "ZiFlow proof creation failed")


def create_proof_for_order_product(order_product_name: str, order_doc=None) -> Dict[str, Any]:
    """Create a ZiFlow proof for a specific OPS Order Product."""
    settings = load_settings()
    require_api_key(settings)
    client = ZiFlowClient(settings)

    product_row = frappe.get_doc("OPS Order Product", order_product_name)
    if getattr(product_row, "ziflow_proof", None):
        return {"message": "Proof already linked", "proof": product_row.ziflow_proof}

    order = order_doc or frappe.get_doc("OPS Order", product_row.parent)
    product = get_ops_product(product_row.product_id)
    customer = resolve_ops_customer(order)

    if product and product.get("requires_proof_approval") is False:
        return {"message": "Proof not required for product", "skipped": True}

    folder_id = resolve_folder_id(customer, product, settings)
    template_id = resolve_template_id(product, settings)
    reviewers = collect_reviewers(order, customer)
    deadline = resolve_deadline(order, product_row, settings)
    file_url = extract_file_url(product_row)
    if not file_url:
        raise MissingConfigurationError("No file URL found for proof creation")

    proof_name = derive_proof_name(order, product_row)
    payload = {
        "name": proof_name,
        "file_url": file_url,
        "folder_id": folder_id,
        "template_id": template_id,
        "reviewers": [{"email": email} for email in reviewers] if reviewers else [],
        "deadline": deadline.isoformat() if deadline else None,
        "message": f"Please review proof for Order #{order.ops_order_id}",
    }

    response = client.create_proof(payload)
    proof_status = map_ziflow_status(response.get("status")) or "In Review"

    proof_doc = frappe.get_doc({
        "doctype": "OPS ZiFlow Proof",
        "ziflow_proof_id": response.get("id"),
        "proof_name": proof_name,
        "proof_status": proof_status,
        "ziflow_url": response.get("share_url") or response.get("url"),
        "file_url": file_url,
        "ops_order": order.name,
        "ops_order_product": product_row.name,
        "ops_product": product.get("name") if product else None,
        "ops_customer": customer.name if customer else None,
        "ziflow_folder_id": folder_id,
        "folder_name": (response.get("folder") or {}).get("name"),
        "template_id": template_id,
        "template_name": (response.get("template") or {}).get("name"),
        "deadline": deadline,
        "created_at": response.get("created_at"),
        "last_synced": now_datetime(),
        "versions_json": json.dumps(response.get("versions") or [], indent=2),
        "reviewers_json": json.dumps(response.get("reviewers") or payload.get("reviewers") or [], indent=2),
        "raw_payload": json.dumps(response, indent=2),
    })
    proof_doc.insert(ignore_permissions=True)

    frappe.db.set_value("OPS Order Product", product_row.name, {
        "ziflow_proof": proof_doc.name,
        "ziflow_proof_status": map_proof_to_product_status(proof_status) or "In Review",
        "ziflow_proof_url": proof_doc.ziflow_url,
        "ziflow_deadline": deadline.date() if deadline else None,
        "ziflow_approved_at": proof_doc.approved_at,
        "ziflow_version": proof_doc.current_version or 1,
    })

    update_order_proof_summary(order.name)
    return {"proof": proof_doc.name, "ziflow_proof_id": proof_doc.ziflow_proof_id, "status": proof_status}


def bulk_create_proofs(order_name: str) -> Dict[str, Any]:
    """Create proofs for all products within an OPS Order."""
    order = frappe.get_doc("OPS Order", order_name)
    results = []
    for child in order.get("ops_order_products", []):
        try:
            results.append(create_proof_for_order_product(child.name, order_doc=order))
        except MissingConfigurationError as exc:
            results.append({"product": child.name, "error": str(exc)})
        except ZiFlowError as exc:
            results.append({"product": child.name, "error": str(exc)})
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"ZiFlow bulk creation failed for {child.name}")
            results.append({"product": child.name, "error": "Unexpected error"})
    update_order_proof_summary(order.name)
    return {"results": results}


def derive_proof_name(order, product_row) -> str:
    order_id = getattr(order, "ops_order_id", order.name)
    product_name = getattr(product_row, "products_name", product_row.name)
    return f"{order_id}-{product_name}"


def resolve_deadline(order, product_row, settings) -> Any:
    date_value = (
        getattr(product_row, "product_production_due_date", None)
        or getattr(order, "production_due_date", None)
        or getattr(order, "orders_due_date", None)
    )
    if not date_value:
        return None
    deadline = get_datetime(str(date_value))
    if settings.deadline_buffer_days:
        deadline = add_days(deadline, -int(settings.deadline_buffer_days))
    return deadline


def resolve_folder_id(customer, product, settings) -> str | None:
    if customer and customer.get("ziflow_folder_id"):
        return customer.ziflow_folder_id
    if product and product.get("ziflow_folder_id"):
        return product.ziflow_folder_id
    return settings.default_folder_id


def resolve_template_id(product, settings) -> str | None:
    if product and product.get("default_ziflow_template"):
        return product.default_ziflow_template
    return settings.default_template_id


def collect_reviewers(order, customer) -> List[str]:
    reviewers = []
    primary_email = getattr(order, "customers_email_address", None) or getattr(order, "customer_email", None)
    if primary_email:
        reviewers.append(primary_email)
    if customer:
        default_reviewers = getattr(customer, "default_proof_reviewers", "") or ""
        for email in split_emails(default_reviewers):
            reviewers.append(email)
        secondary = getattr(customer, "secondary_emails", None)
        if secondary:
            for row in secondary:
                if row.get("email"):
                    reviewers.append(row.get("email"))
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for email in reviewers:
        if not email:
            continue
        normalized = email.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def split_emails(value: str) -> List[str]:
    parts = []
    for token in value.replace("\n", ",").split(","):
        token = token.strip()
        if token:
            parts.append(token)
    return parts


def extract_file_url(product_row) -> str | None:
    """Attempt to find a usable file URL for ZiFlow."""
    direct_keys = [
        "file_url",
        "print_ready_file_url",
        "proof_file_url",
        "artwork_url",
    ]
    for key in direct_keys:
        value = getattr(product_row, key, None)
        if value:
            return value

    features = getattr(product_row, "features_details", None)
    if features:
        try:
            data = json.loads(features)
            for key in ("print_ready_files", "proof_files"):
                bucket = data.get(key)
                url = _extract_url_from_bucket(bucket)
                if url:
                    return url
        except Exception:
            pass
    return None


def _extract_url_from_bucket(bucket: Any) -> str | None:
    if isinstance(bucket, list) and bucket:
        first = bucket[0]
        if isinstance(first, dict):
            return first.get("url") or first.get("file_url") or first.get("link")
        return str(first)
    if isinstance(bucket, dict):
        return bucket.get("url") or bucket.get("file_url") or bucket.get("link")
    return None


def get_ops_product(product_id: Any):
    if not product_id:
        return None
    rows = frappe.get_all(
        "OPS Product",
        filters={"product_id": product_id},
        fields=["name", "product_name", "requires_proof_approval", "default_ziflow_template", "ziflow_folder_id"],
        limit=1,
    )
    if not rows:
        return None
    return frappe.get_doc("OPS Product", rows[0].name)


def resolve_ops_customer(order):
    candidates = [
        getattr(order, "ops_customer", None),
        getattr(order, "customer_company", None),
        getattr(order, "customers_company", None),
    ]
    for candidate in candidates:
        if candidate and frappe.db.exists("OPS Customer", candidate):
            return frappe.get_doc("OPS Customer", candidate)

    email = getattr(order, "customers_email_address", None) or getattr(order, "customer_email", None)
    if email:
        matches = frappe.get_all("OPS Customer", filters={"customer_email": email}, limit=1)
        if matches:
            return frappe.get_doc("OPS Customer", matches[0].name)
    return None
