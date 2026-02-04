# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


def _sanitize_traceback(tb: str) -> str:
    """Sanitize traceback to remove HTML and make it valid for Code field.

    The Code field with Python option validates syntax, so we need to
    ensure the traceback is clean text without HTML tags.
    """
    if not tb:
        return ""

    # Remove HTML tags
    tb = re.sub(r'<[^>]+>', '', tb)

    # Unescape HTML entities
    tb = tb.replace('&lt;', '<')
    tb = tb.replace('&gt;', '>')
    tb = tb.replace('&amp;', '&')
    tb = tb.replace('&quot;', '"')
    tb = tb.replace('&#39;', "'")
    tb = tb.replace('&nbsp;', ' ')
    tb = tb.replace('<br>', '\n')
    tb = tb.replace('<br/>', '\n')
    tb = tb.replace('<br />', '\n')

    # Remove any remaining HTML-like patterns
    tb = re.sub(r'<[^>]*>', '', tb)

    # Clean up excessive whitespace but preserve newlines
    lines = tb.split('\n')
    lines = [line.rstrip() for line in lines]
    tb = '\n'.join(lines)

    # Limit length to prevent oversized entries
    if len(tb) > 50000:
        tb = tb[:50000] + "\n... [truncated]"

    return tb


class OPSErrorLog(Document):
    def before_save(self):
        # Auto-set resolved info when status changes to Resolved
        if self.status in ("Resolved", "Auto-Resolved", "Ignored") and not self.resolved_at:
            self.resolved_at = now_datetime()
            self.resolved_by = frappe.session.user

    def resolve(self, resolution_notes=None, resolution_action=None):
        """Mark error as resolved"""
        self.status = "Resolved"
        self.resolved_at = now_datetime()
        self.resolved_by = frappe.session.user
        if resolution_notes:
            self.resolution_notes = resolution_notes
        if resolution_action:
            self.resolution_action = resolution_action
        self.save(ignore_permissions=True)

    def ignore_error(self, reason=None):
        """Mark error as ignored"""
        self.status = "Ignored"
        self.resolved_at = now_datetime()
        self.resolved_by = frappe.session.user
        self.resolution_action = "Ignored - Not Applicable"
        if reason:
            self.resolution_notes = reason
        self.save(ignore_permissions=True)


@frappe.whitelist()
def log_error(
    error_title: str,
    error_message: str,
    error_type: str = "Unknown",
    severity: str = "Medium",
    source_doctype: str = None,
    source_document: str = None,
    source_field: str = None,
    service_name: str = None,
    function_name: str = None,
    traceback: str = None,
    request_data: str = None,
    response_data: str = None,
    auto_retry: bool = False,
    max_retries: int = 3
) -> str:
    """
    Log an error to OPS Error Log.

    Returns the name of the created error log document.
    """
    try:
        # Sanitize traceback to remove HTML tags that cause validation errors
        sanitized_traceback = _sanitize_traceback(traceback) if traceback else None

        # Validate source_document exists if source_doctype is provided
        # Dynamic Link fields fail if the referenced document doesn't exist
        validated_source_document = None
        if source_doctype and source_document:
            try:
                if frappe.db.exists(source_doctype, source_document):
                    validated_source_document = source_document
                else:
                    # Document doesn't exist - store the ID in error_message instead
                    if error_message:
                        error_message = f"{error_message}\n[Reference: {source_doctype} {source_document}]"
                    else:
                        error_message = f"[Reference: {source_doctype} {source_document}]"
            except Exception:
                # DocType might not exist or other error - skip validation
                pass

        doc = frappe.get_doc({
            "doctype": "OPS Error Log",
            "error_title": error_title[:140] if error_title else "Unknown Error",
            "error_message": error_message,
            "error_type": error_type,
            "severity": severity,
            "status": "Open",
            "source_doctype": source_doctype if validated_source_document else None,
            "source_document": validated_source_document,
            "source_field": source_field,
            "service_name": service_name,
            "function_name": function_name,
            "traceback": sanitized_traceback,
            "request_data": request_data,
            "response_data": response_data,
            "auto_retry": 1 if auto_retry else 0,
            "max_retries": max_retries,
            "occurred_at": now_datetime()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    except Exception as e:
        # If we can't log the error, at least print it
        frappe.log_error(f"Failed to log OPS error: {str(e)}\nOriginal error: {error_title}")
        return None


@frappe.whitelist()
def resolve_error(error_name: str, resolution_notes: str = None, resolution_action: str = None):
    """Resolve an error log entry"""
    doc = frappe.get_doc("OPS Error Log", error_name)
    doc.resolve(resolution_notes, resolution_action)
    return {"status": "success", "message": f"Error {error_name} resolved"}


@frappe.whitelist()
def bulk_resolve_errors(error_names: list, resolution_notes: str = None, resolution_action: str = None):
    """Resolve multiple error log entries"""
    if isinstance(error_names, str):
        import json
        error_names = json.loads(error_names)

    resolved = 0
    for name in error_names:
        try:
            doc = frappe.get_doc("OPS Error Log", name)
            doc.resolve(resolution_notes, resolution_action)
            resolved += 1
        except Exception:
            pass

    frappe.db.commit()
    return {"status": "success", "resolved": resolved}


@frappe.whitelist()
def ignore_error(error_name: str, reason: str = None):
    """Ignore an error log entry"""
    doc = frappe.get_doc("OPS Error Log", error_name)
    doc.ignore_error(reason)
    return {"status": "success", "message": f"Error {error_name} ignored"}


@frappe.whitelist()
def get_error_summary():
    """Get summary of errors by type and status"""
    summary = {
        "total_open": frappe.db.count("OPS Error Log", {"status": "Open"}),
        "total_in_progress": frappe.db.count("OPS Error Log", {"status": "In Progress"}),
        "by_severity": {},
        "by_type": {},
        "recent_critical": []
    }

    # By severity
    for severity in ["Critical", "High", "Medium", "Low", "Info"]:
        count = frappe.db.count("OPS Error Log", {"status": "Open", "severity": severity})
        if count > 0:
            summary["by_severity"][severity] = count

    # By type
    types = frappe.db.sql("""
        SELECT error_type, COUNT(*) as count
        FROM `tabOPS Error Log`
        WHERE status = 'Open'
        GROUP BY error_type
    """, as_dict=True)
    for t in types:
        summary["by_type"][t.error_type] = t.count

    # Recent critical errors
    summary["recent_critical"] = frappe.get_all(
        "OPS Error Log",
        filters={"status": "Open", "severity": ["in", ["Critical", "High"]]},
        fields=["name", "error_title", "error_type", "severity", "occurred_at", "source_doctype", "source_document"],
        order_by="occurred_at desc",
        limit=10
    )

    return summary


@frappe.whitelist()
def retry_error(error_name: str):
    """Retry the operation that caused the error"""
    doc = frappe.get_doc("OPS Error Log", error_name)

    if doc.retry_count >= doc.max_retries:
        return {"status": "error", "message": "Max retries exceeded"}

    # Increment retry count
    doc.retry_count += 1
    doc.status = "In Progress"
    doc.save(ignore_permissions=True)

    # Attempt retry based on error type and source
    try:
        result = _execute_retry(doc)
        if result.get("success"):
            doc.status = "Auto-Resolved"
            doc.resolution_action = "Auto Retry Success"
            doc.resolved_at = now_datetime()
            doc.save(ignore_permissions=True)
            return {"status": "success", "message": "Retry successful"}
        else:
            doc.status = "Open"
            doc.save(ignore_permissions=True)
            return {"status": "error", "message": result.get("message", "Retry failed")}
    except Exception as e:
        doc.status = "Open"
        doc.save(ignore_permissions=True)
        return {"status": "error", "message": str(e)}


def _execute_retry(error_doc):
    """Execute retry based on error type"""
    from ops_ziflow.services import sync_service

    if error_doc.error_type == "Sync Error" and error_doc.source_doctype == "OPS ZiFlow Proof":
        # Retry proof sync
        if error_doc.source_document:
            try:
                sync_service.sync_proof_status(error_doc.source_document)
                return {"success": True}
            except Exception as e:
                return {"success": False, "message": str(e)}

    return {"success": False, "message": "No retry handler for this error type"}
