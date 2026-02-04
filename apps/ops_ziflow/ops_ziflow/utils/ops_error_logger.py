"""OPS Error Logger - Utility functions for logging to OPS Error Log."""

from typing import Dict, Optional
import frappe
from frappe.utils import now_datetime


def log_ops_error(
    title: str,
    error_type: str = "Sync Error",
    severity: str = "Medium",
    service_name: str = "ZiFlow",
    function_name: str = "",
    error_message: str = "",
    traceback: str = "",
    source_doctype: str = None,
    source_document: str = None,
    request_data: str = None,
    response_data: str = None,
) -> Optional[str]:
    """Log an error to OPS Error Log doctype.

    Args:
        title: Short error title
        error_type: Sync Error, API Error, Validation Error, Data Integrity, Configuration Error, Webhook Error, Unknown
        severity: Critical, High, Medium, Low, Info
        service_name: Service/Module name (e.g., ZiFlow, OnPrintShop)
        function_name: Function where error occurred
        error_message: Error message text
        traceback: Full traceback
        source_doctype: Related DocType
        source_document: Related document name
        request_data: JSON request data
        response_data: JSON response data

    Returns:
        Name of created OPS Error Log or None
    """
    try:
        doc = frappe.new_doc("OPS Error Log")
        doc.error_title = title[:140] if title else "Unknown Error"
        doc.error_type = error_type
        doc.severity = severity
        doc.status = "Open"
        doc.service_name = service_name
        doc.function_name = function_name
        doc.error_message = error_message[:65000] if error_message else ""
        doc.traceback = traceback[:65000] if traceback else ""

        if source_doctype:
            doc.source_doctype = source_doctype
        if source_document:
            doc.source_document = source_document
        if request_data:
            doc.request_data = request_data[:65000] if len(request_data) > 65000 else request_data
        if response_data:
            doc.response_data = response_data[:65000] if len(response_data) > 65000 else response_data

        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    except Exception as e:
        # Fallback to standard error log if OPS Error Log fails
        frappe.log_error(f"Failed to log OPS error: {e}\nOriginal error: {error_message}", "OPS Error Log Failed")
        return None


def log_sync_status(stats: Dict, sync_type: str = "ZiFlow Sync") -> Optional[str]:
    """Log sync status/health info to OPS Error Log.

    Args:
        stats: Sync statistics dictionary
        sync_type: Type of sync (e.g., ZiFlow Sync, ZiFlow Poll)

    Returns:
        Name of created OPS Error Log or None (only logs if there were errors)
    """
    errors = stats.get("errors", 0)
    error_message = stats.get("error_message", "")

    # Only log if there were errors
    if errors == 0 and not error_message:
        return None

    # Determine severity based on error count
    if errors > 50 or error_message:
        severity = "High"
    elif errors > 10:
        severity = "Medium"
    else:
        severity = "Low"

    title = f"{sync_type}: {errors} errors"
    if error_message:
        title = f"{sync_type} Failed: {error_message[:50]}"

    message = f"""Sync Statistics:
- Total Fetched: {stats.get('total_fetched', 0)}
- Created: {stats.get('created', 0)}
- Updated: {stats.get('updated', 0)}
- Errors: {errors}
- Start: {stats.get('start_time', 'N/A')}
- End: {stats.get('end_time', 'N/A')}
"""
    if error_message:
        message += f"\nError: {error_message}"

    return log_ops_error(
        title=title,
        error_type="Sync Error",
        severity=severity,
        service_name="ZiFlow",
        function_name=sync_type.lower().replace(" ", "_"),
        error_message=message,
    )


def check_proof_health() -> Dict:
    """Check ZiFlow proof data health and log any issues.

    Returns:
        Dict with health check results
    """
    result = {
        "total": 0,
        "field_coverage": {},
        "invalid_links": {},
        "issues": {},
        "logged_errors": [],
    }

    total = frappe.db.count("OPS ZiFlow Proof")
    result["total"] = total

    if total == 0:
        return result

    # Check critical fields
    critical_fields = [
        ("proof_status", "Status"),
        ("deadline", "Deadline"),
        ("ops_order", "OPS Order"),
    ]

    for fieldname, label in critical_fields:
        count = frappe.db.sql(f"""
            SELECT COUNT(*) FROM `tabOPS ZiFlow Proof`
            WHERE `{fieldname}` IS NOT NULL AND `{fieldname}` != ''
        """)[0][0]
        pct = 100 * count // total
        result["field_coverage"][fieldname] = {"count": count, "pct": pct}

        # Log if critical field coverage is below 80%
        if pct < 80:
            error_name = log_ops_error(
                title=f"Low {label} coverage: {pct}%",
                error_type="Data Integrity",
                severity="Medium" if pct >= 50 else "High",
                service_name="ZiFlow",
                function_name="check_proof_health",
                error_message=f"{label} field is only populated in {count}/{total} proofs ({pct}%)",
                source_doctype="OPS ZiFlow Proof",
            )
            if error_name:
                result["logged_errors"].append(error_name)

    # Check for invalid links
    invalid_orders = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS ZiFlow Proof` p
        WHERE p.ops_order IS NOT NULL AND p.ops_order != ''
        AND NOT EXISTS (SELECT 1 FROM `tabOPS Order` o WHERE o.name = p.ops_order)
    """)[0][0]

    if invalid_orders > 0:
        result["invalid_links"]["ops_order"] = invalid_orders
        error_name = log_ops_error(
            title=f"Invalid OPS Order links: {invalid_orders}",
            error_type="Data Integrity",
            severity="High",
            service_name="ZiFlow",
            function_name="check_proof_health",
            error_message=f"Found {invalid_orders} proofs with invalid ops_order references",
            source_doctype="OPS ZiFlow Proof",
        )
        if error_name:
            result["logged_errors"].append(error_name)

    # Check Approved without approved_at
    approved_no_date = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS ZiFlow Proof`
        WHERE proof_status = 'Approved' AND approved_at IS NULL
    """)[0][0]

    if approved_no_date > 0:
        result["issues"]["approved_no_date"] = approved_no_date
        error_name = log_ops_error(
            title=f"Approved proofs missing date: {approved_no_date}",
            error_type="Data Integrity",
            severity="Low",
            service_name="ZiFlow",
            function_name="check_proof_health",
            error_message=f"Found {approved_no_date} Approved proofs without approved_at date",
            source_doctype="OPS ZiFlow Proof",
        )
        if error_name:
            result["logged_errors"].append(error_name)

    return result
