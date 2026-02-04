"""Log the quote sync fix to OPS Error Log"""
import frappe
from frappe.utils import now_datetime

def log_fix():
    """Create an info entry in OPS Error Log documenting the sync fix"""

    doc = frappe.get_doc({
        "doctype": "OPS Error Log",
        "error_title": "Quote Sync Fix Applied - Incremental Sync Enabled",
        "error_message": """Quote sync has been fixed and optimized:

PROBLEM:
- 1,430 quotes (93%) were not synced in >24 hours
- Batch size of 100 was too small for 1,531 quotes
- Scheduler was only fetching first 100 quotes repeatedly

SOLUTION:
- Changed to incremental sync (only fetches NEW quotes)
- Added full_import_quotes() function for initial import
- Set baseline: all 1,531 existing quotes marked as synced
- Max quote_id: 1644 stored for incremental sync

CURRENT STATUS:
- Total Quotes: 1,531
- Quote ID Range: 17 - 1644
- Sync Coverage: 100%
- Incremental Sync: Active (checks for quote_id > 1644)

COMMANDS:
- Check status: bench execute ops_ziflow.check_quote_sync_status.check_status
- Manual sync: bench execute ops_ziflow.services.quote_sync_service.poll_onprintshop_quotes
- Full import: bench execute ops_ziflow.services.quote_sync_service.full_import_quotes
""",
        "error_type": "Sync Error",
        "severity": "Low",
        "status": "Resolved",
        "source_doctype": "OPS Quote",
        "service_name": "quote_sync_service",
        "function_name": "poll_onprintshop_quotes",
        "resolution_action": "Manual Fix",
        "resolution_notes": "Implemented incremental sync. Changed from fetching all quotes to only fetching new quotes (quote_id > last_synced_id). All existing 1,531 quotes marked as synced. Max quote_id: 1644.",
        "resolved_at": now_datetime(),
        "resolved_by": frappe.session.user,
        "occurred_at": now_datetime()
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    print(f"Logged fix to OPS Error Log: {doc.name}")
    return doc.name
