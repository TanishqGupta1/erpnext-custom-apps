# OPS Error Log

Centralized error tracking and resolution management for OPS integration services.

## Access URLs

- **Error List**: `/app/ops-error-log`
- **Error Dashboard**: `/app/ops-error-dashboard`

## API Usage

### Log an Error

```python
from ops_ziflow.ops_integration.doctype.ops_error_log.ops_error_log import log_error

log_error(
    error_title="Order sync failed",
    error_message="Connection timeout",
    error_type="API Error",        # Sync Error, API Error, Webhook Error, Data Integrity, Validation Error, Configuration Error
    severity="High",               # Critical, High, Medium, Low, Info
    source_doctype="OPS Order",
    source_document="ORD-00123",
    service_name="order_sync_service",
    function_name="poll_onprintshop_orders",
    traceback=traceback.format_exc(),
    request_data='{"order_id": 123}',
    auto_retry=True,
    max_retries=3
)
```

### Resolve/Ignore Errors

```python
from ops_ziflow.ops_integration.doctype.ops_error_log.ops_error_log import resolve_error, ignore_error, bulk_resolve_errors

# Single resolve
resolve_error("OPS-ERR-0001", resolution_notes="Fixed", resolution_action="Manual Fix")

# Bulk resolve
bulk_resolve_errors(["OPS-ERR-0001", "OPS-ERR-0002"], resolution_action="Data Corrected")

# Ignore
ignore_error("OPS-ERR-0005", reason="Duplicate")
```

### Get Summary

```python
from ops_ziflow.ops_integration.doctype.ops_error_log.ops_error_log import get_error_summary

summary = get_error_summary()
# Returns: total_open, total_in_progress, by_severity, by_type, recent_critical
```

## Services Using Error Logging

| Service | Functions |
|---------|-----------|
| sync_service.py | poll_pending_proofs, handle_webhook, add_order_comment |
| order_sync_service.py | poll_onprintshop_orders, sync_order_from_onprintshop, push_order_to_onprintshop |
| import_service.py | sync_all_proofs |
| quote_sync_service.py | poll_onprintshop_quotes, full_import_quotes, push_quote_to_onprintshop |

## Severity Guide

| Severity | Use Case |
|----------|----------|
| Critical | System failures, batch crashes |
| High | Individual sync/API failures |
| Medium | Recoverable errors |
| Low | Minor issues |
| Info | Warnings |

## Adding to New Services

```python
import traceback
import frappe

def _log_ops_error(
    error_title, error_message, error_type="Sync Error", severity="Medium",
    source_doctype=None, source_document=None, service_name="your_service",
    function_name=None, request_data=None, auto_retry=False
):
    try:
        from ops_ziflow.ops_integration.doctype.ops_error_log.ops_error_log import log_error
        log_error(
            error_title=error_title, error_message=error_message,
            error_type=error_type, severity=severity,
            source_doctype=source_doctype, source_document=source_document,
            service_name=service_name, function_name=function_name,
            traceback=traceback.format_exc(), request_data=request_data,
            auto_retry=auto_retry
        )
    except Exception:
        frappe.log_error(f"{error_title}: {error_message}", "OPS Error")
```
