"""Bootstrap helpers for the ZiFlow app."""

from __future__ import annotations

import logging
import json
from typing import Dict, List

import frappe

from ops_ziflow.services.ziflow_client import ZiFlowClient
from ops_ziflow.utils.config import load_settings, require_api_key
LOGGER = logging.getLogger(__name__)


def ensure_module_def() -> None:
    """Create Module Def for OPS Integration when missing (idempotent)."""
    if frappe.db.exists("Module Def", "OPS Integration"):
        return
    module = frappe.get_doc({
        "doctype": "Module Def",
        "module_name": "OPS Integration",
        "app_name": "ops_ziflow",
    })
    module.insert(ignore_permissions=True, ignore_if_duplicate=True)
    LOGGER.info("Created Module Def: OPS Integration")


def ensure_number_cards() -> None:
    """Create number cards for ZiFlow dashboard (idempotent)."""
    number_cards = [
        {
            "name": "Total ZiFlow Proofs",
            "label": "Total Proofs",
            "document_type": "OPS ZiFlow Proof",
            "function": "Count",
            "color": "#449CF0",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly",
        },
        {
            "name": "Pending ZiFlow Proofs",
            "label": "Pending Review",
            "document_type": "OPS ZiFlow Proof",
            "function": "Count",
            "color": "#ECAD4B",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly",
            "filters_json": '[["OPS ZiFlow Proof","proof_status","in",["Draft","In Review","Changes Requested"]]]',
        },
        {
            "name": "Approved ZiFlow Proofs",
            "label": "Approved",
            "document_type": "OPS ZiFlow Proof",
            "function": "Count",
            "color": "#48BB74",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly",
            "filters_json": '[["OPS ZiFlow Proof","proof_status","=","Approved"]]',
        },
        {
            "name": "Overdue ZiFlow Proofs",
            "label": "Overdue",
            "document_type": "OPS ZiFlow Proof",
            "function": "Count",
            "color": "#E53E3E",
            "is_public": 1,
            "show_percentage_stats": 0,
            "filters_json": '[["OPS ZiFlow Proof","proof_status","in",["Draft","In Review","Changes Requested"]],["OPS ZiFlow Proof","deadline","is","set"]]',
        },
        {
            "name": "Orders with Pending Proofs",
            "label": "Orders Pending",
            "document_type": "OPS Order",
            "function": "Count",
            "color": "#805AD5",
            "is_public": 1,
            "show_percentage_stats": 0,
            "filters_json": '[["OPS Order","all_proofs_approved","=",0],["OPS Order","pending_proof_count",">",0]]',
        },
    ]
    for card_def in number_cards:
        if frappe.db.exists("Number Card", card_def["name"]):
            continue
        try:
            card = frappe.get_doc({"doctype": "Number Card", **card_def})
            card.insert(ignore_permissions=True, ignore_if_duplicate=True)
            LOGGER.info(f"Created Number Card: {card_def['name']}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to create Number Card: {card_def['name']}")


def ensure_workspace() -> None:
    """Create/update a public workspace so the module appears in the desk switcher."""
    # Ensure number cards exist first
    ensure_number_cards()
    workspace = None
    if frappe.db.exists("Workspace", {"app": "ops_ziflow"}):
        workspace = frappe.get_doc("Workspace", {"app": "ops_ziflow"})
    elif frappe.db.exists("Workspace", {"label": "OPS ZiFlow"}):
        workspace = frappe.get_doc("Workspace", {"label": "OPS ZiFlow"})
    else:
        workspace = frappe.new_doc("Workspace")

    workspace.update({
        "doctype": "Workspace",
        "app": "ops_ziflow",
        "label": "OPS ZiFlow",
        "title": "OPS ZiFlow",
        "module": "OPS Integration",
        "public": 1,
        "is_hidden": 0,
        "icon": "octicon octicon-checklist",
    })

    content = [
        {"id": "ziflow_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>ZiFlow</b></span>", "col": 12}},
        {"id": "ziflow_proofs_shortcut", "type": "shortcut", "data": {"shortcut_name": "ZiFlow Proofs", "col": 3}},
        {"id": "ziflow_files_shortcut", "type": "shortcut", "data": {"shortcut_name": "File Manager", "col": 3}},
        {"id": "ziflow_portal_shortcut", "type": "shortcut", "data": {"shortcut_name": "ZiFlow Portal", "col": 3}},
        {"id": "ziflow_spacer", "type": "spacer", "data": {"col": 12}},
        {"id": "ziflow_folders_header", "type": "header", "data": {"text": "<span class=\"h5\"><b>Folders & Files</b></span>", "col": 12}},
    ]
    workspace.content = json.dumps(content)

    shortcuts = [
        {
            "label": "ZiFlow Proofs",
            "type": "DocType",
            "link_to": "OPS ZiFlow Proof",
            "doc_view": "List",
            "color": "blue",
        },
        {
            "label": "File Manager",
            "type": "DocType",
            "link_to": "File",
            "doc_view": "List",
            "color": "grey",
        },
        {
            "label": "ZiFlow Portal",
            "type": "URL",
            "url": "https://app.ziflow.com/#/proofs/folders",
            "color": "green",
        },
    ]
    workspace.set("shortcuts", [])
    for sc in shortcuts:
        workspace.append("shortcuts", sc)

    workspace.flags.ignore_permissions = True
    if workspace.is_new():
        workspace.insert(ignore_if_duplicate=True)
        LOGGER.info("Created Workspace: OPS ZiFlow")
    else:
        workspace.save(ignore_version=True)
        LOGGER.info("Updated Workspace: OPS ZiFlow")


def get_custom_fields() -> Dict[str, List[dict]]:
    """Return custom field definitions aligned with the integration plan."""
    return {
        "OPS Order Product": [
            {
                "fieldname": "ziflow_section",
                "label": "ZiFlow Proofing",
                "fieldtype": "Section Break",
                "insert_after": "product_production_due_date",
            },
            {
                "fieldname": "ziflow_proof",
                "label": "ZiFlow Proof",
                "fieldtype": "Link",
                "options": "OPS ZiFlow Proof",
                "insert_after": "ziflow_section",
            },
            {
                "fieldname": "ziflow_proof_status",
                "label": "Proof Status",
                "fieldtype": "Select",
                "options": "\nPending\nIn Review\nApproved\nRejected",
                "insert_after": "ziflow_proof",
            },
            {
                "fieldname": "ziflow_proof_url",
                "label": "Proof URL",
                "fieldtype": "Data",
                "insert_after": "ziflow_proof_status",
            },
            {
                "fieldname": "cb_ziflow",
                "fieldtype": "Column Break",
                "insert_after": "ziflow_proof_url",
            },
            {
                "fieldname": "ziflow_deadline",
                "label": "Proof Deadline",
                "fieldtype": "Date",
                "insert_after": "cb_ziflow",
            },
            {
                "fieldname": "ziflow_approved_at",
                "label": "Approved At",
                "fieldtype": "Datetime",
                "insert_after": "ziflow_deadline",
            },
            {
                "fieldname": "ziflow_version",
                "label": "Version",
                "fieldtype": "Int",
                "default": "1",
                "insert_after": "ziflow_approved_at",
            },
        ],
        "OPS Order": [
            {
                "fieldname": "ziflow_tab",
                "label": "Proofing",
                "fieldtype": "Tab Break",
                "insert_after": "ops_order_products",
            },
            {
                "fieldname": "all_proofs_approved",
                "label": "All Proofs Approved",
                "fieldtype": "Check",
                "read_only": 1,
                "insert_after": "ziflow_tab",
            },
            {
                "fieldname": "pending_proof_count",
                "label": "Pending Proofs",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "all_proofs_approved",
            },
            {
                "fieldname": "ziflow_proofs_html",
                "label": "Proof Status Summary",
                "fieldtype": "HTML",
                "insert_after": "pending_proof_count",
            },
        ],
        "OPS Product": [
            {
                "fieldname": "ziflow_section",
                "label": "ZiFlow Settings",
                "fieldtype": "Section Break",
                "insert_after": "sync_tab",
            },
            {
                "fieldname": "requires_proof_approval",
                "label": "Requires Proof Approval",
                "fieldtype": "Check",
                "insert_after": "ziflow_section",
            },
            {
                "fieldname": "default_ziflow_template",
                "label": "Default Template ID",
                "fieldtype": "Data",
                "insert_after": "requires_proof_approval",
            },
            {
                "fieldname": "ziflow_folder_id",
                "label": "ZiFlow Folder ID",
                "fieldtype": "Data",
                "insert_after": "default_ziflow_template",
            },
        ],
        "OPS Customer": [
            {
                "fieldname": "ziflow_section",
                "label": "ZiFlow Settings",
                "fieldtype": "Section Break",
                "insert_after": "add_address_button",
            },
            {
                "fieldname": "ziflow_folder_id",
                "label": "ZiFlow Folder ID",
                "fieldtype": "Data",
                "insert_after": "ziflow_section",
            },
            {
                "fieldname": "default_proof_reviewers",
                "label": "Default Reviewers (emails)",
                "fieldtype": "Small Text",
                "insert_after": "ziflow_folder_id",
            },
            {
                "fieldname": "proof_notifications_enabled",
                "label": "Proof Notifications",
                "fieldtype": "Check",
                "default": "1",
                "insert_after": "default_proof_reviewers",
            },
        ],
    }


def ensure_custom_fields() -> None:
    """Create required custom fields (idempotent) without altering existing schema columns."""
    definitions = get_custom_fields()
    for dt, fields in definitions.items():
        normalize_insert_after(dt, fields)
        for field in fields:
            upsert_custom_field(dt, field)
            ensure_column(dt, field)
    LOGGER.info("Ensured ZiFlow custom fields are present (column-safe)")


def normalize_insert_after(dt: str, fields: List[dict]) -> None:
    """If insert_after targets a missing field, append to the end to avoid errors."""
    try:
        meta = frappe.get_meta(dt)
    except Exception:
        return
    fallback = meta.fields[-1].fieldname if meta.fields else None
    existing_fields = {f.fieldname for f in meta.fields}
    for field in fields:
        target = field.get("insert_after")
        if target and target not in existing_fields:
            field["insert_after"] = fallback


def upsert_custom_field(dt: str, field: dict) -> None:
    """Insert the Custom Field if it does not exist."""
    if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": field["fieldname"]}):
        return
    doc = frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": dt,
            **field,
        }
    )
    doc.flags.ignore_validate = True
    doc.insert(ignore_permissions=True, ignore_if_duplicate=True)


def ensure_column(dt: str, field: dict) -> None:
    """Add the column for the custom field without modifying other columns."""
    fieldname = field.get("fieldname")
    fieldtype = field.get("fieldtype")
    if not fieldname or not fieldtype:
        return
    try:
        if not frappe.db.has_column(dt, fieldname):
            frappe.db.add_column(dt, fieldname, fieldtype)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Failed to add column {fieldname} on {dt}")


def register_webhook() -> dict:
    """Register ZiFlow webhook pointing to this site's API endpoint."""
    settings = load_settings()
    require_api_key(settings)
    client = ZiFlowClient(settings)
    webhook_url = settings.webhook_url or f"{frappe.utils.get_url()}/api/method/ops_ziflow.api.ziflow_webhook"
    return client.create_webhook(webhook_url, settings.webhook_events)
