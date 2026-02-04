"""Quote synchronization service for bidirectional OPS Quote sync."""

from __future__ import annotations

import json
import traceback
from typing import Any, Dict, List, Optional

import frappe
from frappe.utils import now_datetime, cint, flt

from ops_ziflow.services.onprintshop_client import OnPrintShopClient
from ops_ziflow.ops_integration.doctype.ops_quote.ops_quote import sync_quote_from_onprintshop


def _log_ops_error(
    error_title: str,
    error_message: str,
    error_type: str = "Sync Error",
    severity: str = "Medium",
    source_doctype: str = None,
    source_document: str = None,
    service_name: str = "quote_sync_service",
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
        frappe.log_error(f"{error_title}: {error_message}", "OPS Quote Sync Error")


def poll_onprintshop_quotes(batch_size: int = 200) -> Dict[str, Any]:
    """Scheduler job: Fetch only NEW quotes from OnPrintShop.

    Runs every 10 minutes via scheduler_events in hooks.py.
    Uses incremental sync - only fetches quotes with quote_id > last synced.

    For initial import, run: full_import_quotes() first.

    Args:
        batch_size: Number of quotes per API call (default 200)

    Returns:
        Dict with sync statistics
    """
    stats = {
        "synced": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "start_time": now_datetime(),
    }

    try:
        # Get last synced quote_id from cache or DB
        last_synced_id = frappe.cache().get_value("ops_quote_last_synced_id")
        if not last_synced_id:
            last_synced_id = frappe.db.sql("SELECT COALESCE(MAX(quote_id), 0) FROM `tabOPS Quote`")[0][0] or 0
            frappe.cache().set_value("ops_quote_last_synced_id", last_synced_id)

        client = OnPrintShopClient()
        max_new_id = last_synced_id
        offset = 0
        found_old = False

        frappe.logger().info(f"[OPS Quote Sync] Incremental sync from quote_id > {last_synced_id}")

        # Fetch quotes in batches until we hit already-synced ones
        while not found_old:
            result = client.get_quotes(limit=batch_size, offset=offset)
            quotes = result.get("quote", [])

            if not quotes:
                break

            for quote_data in quotes:
                try:
                    quote_id = cint(quote_data.get("quote_id"))
                    if not quote_id:
                        continue

                    # Skip if already synced (quote_id <= last_synced_id)
                    if quote_id <= last_synced_id:
                        found_old = True
                        continue

                    # Track max ID
                    max_new_id = max(max_new_id, quote_id)

                    # Check if exists (for stats)
                    existing = frappe.db.exists("OPS Quote", {"quote_id": quote_id})

                    # Sync the quote
                    doc = sync_quote_from_onprintshop(quote_id, quote_data)
                    frappe.db.set_value("OPS Quote", doc.name, "sync_in_progress", 1, update_modified=False)

                    if existing:
                        stats["updated"] += 1
                    else:
                        stats["created"] += 1

                    stats["synced"] += 1

                except Exception as e:
                    stats["errors"] += 1
                    _log_ops_error(
                        error_title=f"Error syncing quote {quote_data.get('quote_id')}",
                        error_message=str(e),
                        error_type="Sync Error",
                        severity="High",
                        source_doctype="OPS Quote",
                        source_document=str(quote_data.get('quote_id')),
                        function_name="poll_onprintshop_quotes",
                        request_data=json.dumps(quote_data, indent=2) if quote_data else None,
                        auto_retry=True,
                    )

            offset += batch_size

            # Safety: don't fetch more than 2000 quotes in one run
            if offset >= 2000:
                break

        # Clear sync_in_progress flags
        frappe.db.sql("UPDATE `tabOPS Quote` SET sync_in_progress = 0 WHERE sync_in_progress = 1")
        frappe.db.commit()

        # Update last synced ID
        if max_new_id > last_synced_id:
            frappe.cache().set_value("ops_quote_last_synced_id", max_new_id)

        frappe.cache().set_value("ops_quote_last_sync", now_datetime())

        stats["end_time"] = now_datetime()
        stats["last_synced_id"] = last_synced_id
        stats["new_max_id"] = max_new_id

        frappe.logger().info(f"[OPS Quote Sync] Completed: {stats}")

    except Exception as e:
        stats["error_message"] = str(e)
        _log_ops_error(
            error_title="OPS Quote Sync batch failed",
            error_message=str(e),
            error_type="Sync Error",
            severity="Critical",
            function_name="poll_onprintshop_quotes",
        )

    return stats


def full_import_quotes(batch_size: int = 100, delay: float = 1.0) -> Dict[str, Any]:
    """One-time full import of ALL quotes from OnPrintShop.

    Run this once to import all existing quotes:
    bench --site erp.visualgraphx.com execute ops_ziflow.services.quote_sync_service.full_import_quotes

    After this, poll_onprintshop_quotes will only sync NEW quotes.

    Args:
        batch_size: Number of quotes per API call (default 100)
        delay: Seconds to wait between API calls to avoid rate limiting (default 1.0)

    Returns:
        Dict with import statistics
    """
    import time

    stats = {
        "synced": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "start_time": now_datetime(),
    }

    try:
        client = OnPrintShopClient()

        # Get total count first
        first_result = client.get_quotes(limit=1, offset=0)
        total_in_ops = first_result.get("totalQuote", 0)
        frappe.logger().info(f"[OPS Quote Import] Total quotes in OnPrintShop: {total_in_ops}")
        print(f"Total quotes in OnPrintShop: {total_in_ops}")

        # Fetch quotes in batches with delay to avoid rate limiting
        all_quotes = []
        offset = 0

        while True:
            print(f"Fetching batch at offset {offset}...")
            result = client.get_quotes(limit=batch_size, offset=offset)
            quotes = result.get("quote", [])

            if not quotes:
                break

            all_quotes.extend(quotes)
            offset += batch_size

            # Rate limiting delay
            if delay > 0:
                time.sleep(delay)

            # Progress
            print(f"Fetched {len(all_quotes)} quotes so far...")

        stats["total_fetched"] = len(all_quotes)
        frappe.logger().info(f"[OPS Quote Import] Fetched {len(all_quotes)} quotes")
        print(f"Fetched {len(all_quotes)} quotes total, starting import...")

        max_quote_id = 0

        for quote_data in all_quotes:
            try:
                quote_id = cint(quote_data.get("quote_id"))
                if not quote_id:
                    continue

                max_quote_id = max(max_quote_id, quote_id)
                existing = frappe.db.exists("OPS Quote", {"quote_id": quote_id})
                doc = sync_quote_from_onprintshop(quote_id, quote_data)

                if existing:
                    stats["updated"] += 1
                else:
                    stats["created"] += 1

                stats["synced"] += 1

                # Progress every 100
                if stats["synced"] % 100 == 0:
                    frappe.db.commit()
                    print(f"Progress: {stats['synced']}/{len(all_quotes)}")
                    frappe.logger().info(f"[OPS Quote Import] Progress: {stats['synced']}/{len(all_quotes)}")

            except Exception as e:
                stats["errors"] += 1
                if stats["errors"] <= 50:  # Log more errors but not all
                    _log_ops_error(
                        error_title=f"Error importing quote {quote_data.get('quote_id')}",
                        error_message=str(e),
                        error_type="Sync Error",
                        severity="Medium",
                        source_doctype="OPS Quote",
                        source_document=str(quote_data.get('quote_id')),
                        function_name="full_import_quotes",
                        auto_retry=True,
                    )

        frappe.db.commit()

        # Store max quote_id for incremental sync
        frappe.cache().set_value("ops_quote_last_synced_id", max_quote_id)

        stats["end_time"] = now_datetime()
        stats["max_quote_id"] = max_quote_id

        print(f"\n=== Import Complete ===")
        print(f"Synced: {stats['synced']}, Created: {stats['created']}, Updated: {stats['updated']}, Errors: {stats['errors']}")
        print(f"Max quote_id for incremental sync: {max_quote_id}")

        frappe.logger().info(f"[OPS Quote Import] Complete: {stats}")

    except Exception as e:
        stats["error_message"] = str(e)
        _log_ops_error(
            error_title="OPS Quote Import batch failed",
            error_message=str(e),
            error_type="Sync Error",
            severity="Critical",
            function_name="full_import_quotes",
        )
        print(f"ERROR: {e}")

    return stats


def push_quote_to_onprintshop(doc, method: str = None) -> Optional[Dict]:
    """Push local quote changes to OnPrintShop.

    Called by doc_events on OPS Quote on_update.
    Skips if sync_in_progress is True (indicates incoming sync).

    Args:
        doc: OPS Quote document
        method: Hook method name (unused)

    Returns:
        API response or None if skipped
    """
    # Skip if this is an incoming sync (sync_in_progress flag set)
    if cint(doc.sync_in_progress):
        frappe.logger().debug(f"[OPS Quote Sync] Skipping push for {doc.name} - sync_in_progress")
        return None

    # Skip if no quote_id (not synced from OPS yet)
    if not doc.quote_id:
        frappe.logger().debug(f"[OPS Quote Sync] Skipping push for {doc.name} - no quote_id")
        return None

    # Skip if no user_id (required for API)
    if not doc.user_id:
        frappe.logger().debug(f"[OPS Quote Sync] Skipping push for {doc.name} - no user_id")
        return None

    # Check if there are actual local changes (modified > last_synced)
    if doc.last_synced and doc.modified:
        from frappe.utils import get_datetime
        if get_datetime(doc.modified) <= get_datetime(doc.last_synced):
            frappe.logger().debug(f"[OPS Quote Sync] Skipping push for {doc.name} - no changes since last sync")
            return None

    try:
        client = OnPrintShopClient()

        # Build products array for API
        products = _build_products_array(doc)

        # Push update to OnPrintShop
        result = client.update_quote(
            quote_id=int(doc.quote_id),
            user_id=int(doc.user_id),
            quote_title=doc.quote_title or f"Quote {doc.quote_id}",
            products=products,
        )

        # Update last_synced timestamp without triggering another save
        frappe.db.set_value("OPS Quote", doc.name, "last_synced", now_datetime(), update_modified=False)

        frappe.logger().info(f"[OPS Quote Sync] Pushed quote {doc.name} to OnPrintShop: {result}")
        return result

    except Exception as e:
        _log_ops_error(
            error_title=f"Error pushing quote {doc.name} to OnPrintShop",
            error_message=str(e),
            error_type="API Error",
            severity="High",
            source_doctype="OPS Quote",
            source_document=doc.name,
            function_name="push_quote_to_onprintshop",
            auto_retry=True,
        )
        return None


def _build_products_array(doc) -> List[Dict]:
    """Build products array for setQuote mutation from OPS Quote products.

    Args:
        doc: OPS Quote document

    Returns:
        List of product dicts for API
    """
    products = []

    for product in (doc.quote_products or []):
        product_data = {
            "productId": cint(product.products_id) or 0,
            "productTitle": product.products_title or "",
            "quantity": cint(product.quote_products_quantity) or 1,
            "price": flt(product.quote_products_price) or 0,
            "vendorPrice": flt(product.quote_products_vendor_price) or 0,
        }

        # Add custom product fields if it's a custom product
        if cint(product.is_custom_product):
            product_data["isCustomProduct"] = 1
            product_data["productName"] = product.products_name or ""
            product_data["prdSku"] = product.quote_product_sku or ""

        products.append(product_data)

    return products


@frappe.whitelist()
def manual_sync_from_ops(quote_name: str) -> Dict:
    """Manually trigger sync from OnPrintShop for a specific quote.

    Args:
        quote_name: Name of the OPS Quote document

    Returns:
        Sync result
    """
    doc = frappe.get_doc("OPS Quote", quote_name)

    if not doc.quote_id:
        frappe.throw("Quote has no OnPrintShop quote_id")

    try:
        client = OnPrintShopClient()
        result = client.get_quotes(quote_id=int(doc.quote_id))
        quotes = result.get("quote", [])

        if not quotes:
            frappe.throw(f"Quote {doc.quote_id} not found in OnPrintShop")

        quote_data = quotes[0]

        # Set sync flag
        doc.sync_in_progress = 1
        doc.sync_from_onprintshop(quote_data)
        doc.save(ignore_permissions=True)

        # Clear flag
        frappe.db.set_value("OPS Quote", doc.name, "sync_in_progress", 0, update_modified=False)
        frappe.db.commit()

        return {"status": "success", "message": f"Synced quote {doc.quote_id} from OnPrintShop"}

    except Exception as e:
        _log_ops_error(
            error_title=f"Manual sync failed for quote {quote_name}",
            error_message=str(e),
            error_type="Sync Error",
            severity="High",
            source_doctype="OPS Quote",
            source_document=quote_name,
            function_name="manual_sync_from_ops",
        )
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def manual_push_to_ops(quote_name: str) -> Dict:
    """Manually push a quote to OnPrintShop.

    Args:
        quote_name: Name of the OPS Quote document

    Returns:
        Push result
    """
    doc = frappe.get_doc("OPS Quote", quote_name)

    if not doc.quote_id:
        frappe.throw("Quote has no OnPrintShop quote_id")

    if not doc.user_id:
        frappe.throw("Quote has no user_id")

    try:
        client = OnPrintShopClient()
        products = _build_products_array(doc)

        result = client.update_quote(
            quote_id=int(doc.quote_id),
            user_id=int(doc.user_id),
            quote_title=doc.quote_title or f"Quote {doc.quote_id}",
            products=products,
        )

        # Update last_synced
        frappe.db.set_value("OPS Quote", doc.name, "last_synced", now_datetime(), update_modified=False)
        frappe.db.commit()

        return {"status": "success", "message": f"Pushed quote {doc.quote_id} to OnPrintShop", "result": result}

    except Exception as e:
        _log_ops_error(
            error_title=f"Manual push failed for quote {quote_name}",
            error_message=str(e),
            error_type="API Error",
            severity="High",
            source_doctype="OPS Quote",
            source_document=quote_name,
            function_name="manual_push_to_ops",
        )
        return {"status": "error", "message": str(e)}


def full_sync_from_ops(batch_size: int = 50) -> Dict:
    """Full sync of all quotes from OnPrintShop.

    Use for initial import or recovery.

    Args:
        batch_size: Number of quotes per API call

    Returns:
        Sync statistics
    """
    stats = {
        "synced": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "start_time": now_datetime(),
    }

    try:
        client = OnPrintShopClient()
        all_quotes = client.get_all_quotes(batch_size=batch_size)

        frappe.logger().info(f"[OPS Quote Full Sync] Fetched {len(all_quotes)} quotes")

        for quote_data in all_quotes:
            try:
                quote_id = quote_data.get("quote_id")
                if not quote_id:
                    continue

                existing = frappe.db.exists("OPS Quote", {"quote_id": quote_id})
                doc = sync_quote_from_onprintshop(quote_id, quote_data)

                if existing:
                    stats["updated"] += 1
                else:
                    stats["created"] += 1

                stats["synced"] += 1

                # Commit every 50 records
                if stats["synced"] % 50 == 0:
                    frappe.db.commit()
                    frappe.logger().info(f"[OPS Quote Full Sync] Progress: {stats['synced']}/{len(all_quotes)}")

            except Exception as e:
                stats["errors"] += 1
                _log_ops_error(
                    error_title=f"Error syncing quote {quote_data.get('quote_id')} in full sync",
                    error_message=str(e),
                    error_type="Sync Error",
                    severity="Medium",
                    source_doctype="OPS Quote",
                    source_document=str(quote_data.get('quote_id')),
                    function_name="full_sync_from_ops",
                    auto_retry=True,
                )

        frappe.db.commit()
        stats["end_time"] = now_datetime()
        frappe.logger().info(f"[OPS Quote Full Sync] Completed: {stats}")

    except Exception as e:
        stats["error_message"] = str(e)
        _log_ops_error(
            error_title="OPS Quote Full Sync batch failed",
            error_message=str(e),
            error_type="Sync Error",
            severity="Critical",
            function_name="full_sync_from_ops",
        )

    return stats
