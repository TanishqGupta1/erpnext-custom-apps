"""Order synchronization service for bidirectional OPS Order sync."""

from __future__ import annotations

import json
import re
import traceback
from typing import Any, Dict, List, Optional

import frappe
from frappe.utils import now_datetime, cint, flt, get_datetime

from ops_ziflow.services.onprintshop_client import OnPrintShopClient


def _sanitize_date(value: str) -> str:
    """Sanitize date values from OnPrintShop API.

    Handles invalid date strings like 'Invalid date', 'Today', empty strings, etc.
    Returns empty string for invalid values, otherwise returns the original value.
    """
    if not value:
        return ""
    if isinstance(value, str):
        # List of known invalid date strings from OnPrintShop
        invalid_patterns = [
            "invalid date",
            "invalid",
            "today",
            "n/a",
            "na",
            "null",
            "none",
            "undefined",
        ]
        if value.strip().lower() in invalid_patterns:
            return ""
        # Check for obviously malformed dates
        if not re.match(r'^\d{4}-\d{2}-\d{2}', value.strip()):
            # Not a valid ISO date format - could be datetime or invalid
            # Allow datetime formats like "2024-12-30 10:13:16"
            if not re.match(r'^\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}', value.strip()):
                return ""
    return value


def _log_ops_error(
    error_title: str,
    error_message: str,
    error_type: str = "Sync Error",
    severity: str = "Medium",
    source_doctype: str = None,
    source_document: str = None,
    service_name: str = "order_sync_service",
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
        frappe.log_error(f"{error_title}: {error_message}", "OPS Order Sync Error")


# Status mapping from OPS status_id to Frappe-allowed status names
# Frappe allowed values: Pending, New Order, In Design, Order Processing, Order Review,
# ERROR, In Production, Ready for Fulfillment, Fulfilled, Order Completed, Cancelled,
# Refunded, Materials on Order, Quote (Default), Reprint Order, Cancellation Request
OPS_STATUS_MAP = {
    1: "New Order",
    2: "Order Processing",  # Order Confirmed -> Order Processing
    3: "Order Review",      # Awaiting Approval -> Order Review
    4: "Pending",           # Awaiting Payment -> Pending
    5: "Order Processing",  # Payment Received -> Order Processing
    6: "In Design",         # In Prepress -> In Design
    7: "In Production",
    8: "Ready for Fulfillment",
    9: "Fulfilled",         # Partially Shipped -> Fulfilled
    10: "Fulfilled",        # Shipped -> Fulfilled
    11: "Fulfilled",        # Delivered -> Fulfilled
    12: "Pending",          # On Hold -> Pending
    13: "Cancelled",
    14: "Fulfilled",
    15: "Refunded",
    16: "Order Completed",
    26: "Order Completed",  # Alternate ID used by OPS
}

# Map OPS API status names to Frappe-allowed status names
OPS_STATUS_NAME_MAP = {
    "new order": "New Order",
    "order confirmed": "Order Processing",
    "awaiting approval": "Order Review",
    "awaiting payment": "Pending",
    "payment received": "Order Processing",
    "in prepress": "In Design",
    "in production": "In Production",
    "ready for fulfillment": "Ready for Fulfillment",
    "partially shipped": "Fulfilled",
    "shipped": "Fulfilled",
    "delivered": "Fulfilled",
    "on hold": "Pending",
    "cancelled": "Cancelled",
    "fulfilled": "Fulfilled",
    "refunded": "Refunded",
    "order completed": "Order Completed",
    "processing": "Order Processing",
    "pending": "Pending",
    "in design": "In Design",
    "materials on order": "Materials on Order",
    "quote": "Quote (Default)",
    "reprint": "Reprint Order",
    "cancellation request": "Cancellation Request",
}

# Reverse mapping for pushing to OPS
FRAPPE_STATUS_MAP = {v: k for k, v in OPS_STATUS_MAP.items()}


def _normalize_order_status(status_id: int, status_name: str) -> str:
    """Normalize OPS status to Frappe-allowed values."""
    # Try status_id mapping first
    if status_id and status_id in OPS_STATUS_MAP:
        return OPS_STATUS_MAP[status_id]

    # Try status name mapping
    if status_name:
        normalized = OPS_STATUS_NAME_MAP.get(status_name.lower().strip())
        if normalized:
            return normalized

    # Default fallback
    return status_name if status_name else "Pending"


def _get_doc_snapshot(doc) -> Dict[str, Any]:
    """Get a snapshot of key fields for change detection."""
    snapshot = {
        "order_name": doc.order_name or "",
        "order_status": doc.order_status or "",
        "orders_status_id": doc.orders_status_id or 0,
        "total_amount": flt(doc.total_amount),
        "order_amount": flt(doc.order_amount),
        "shipping_amount": flt(doc.shipping_amount),
        "tax_amount": flt(doc.tax_amount),
        "customer_name": doc.customer_name or "",
        "customer_email": doc.customer_email or "",
        "payment_status_title": doc.payment_status_title or "",
        "delivery_name": doc.delivery_name or "",
        "delivery_street_address": doc.delivery_street_address or "",
        "delivery_city": doc.delivery_city or "",
        "delivery_postcode": doc.delivery_postcode or "",
        "tracking_number": doc.tracking_number or "",
        "orders_due_date": str(doc.orders_due_date) if doc.orders_due_date else "",
        "production_due_date": str(doc.production_due_date) if doc.production_due_date else "",
    }
    # Include product count and key product data
    if hasattr(doc, "ops_order_products") and doc.ops_order_products:
        snapshot["product_count"] = len(doc.ops_order_products)
        snapshot["product_ids"] = sorted([str(p.orders_products_id) for p in doc.ops_order_products])
    else:
        snapshot["product_count"] = 0
        snapshot["product_ids"] = []
    return snapshot


def _has_order_changed(doc, before_snapshot: Dict[str, Any]) -> bool:
    """Check if order has meaningful changes after field mapping."""
    after_snapshot = _get_doc_snapshot(doc)

    for key, before_val in before_snapshot.items():
        after_val = after_snapshot.get(key)
        if before_val != after_val:
            frappe.logger().debug(f"[OPS Order Sync] Change detected in {key}: {before_val} -> {after_val}")
            return True

    return False


def poll_onprintshop_orders() -> Dict[str, Any]:
    """Scheduler job: Fetch new/updated orders from OnPrintShop.

    Runs every 6 hours via scheduler_events in hooks.py.
    Uses sync_in_progress flag to prevent outgoing sync loops.
    Paginates through ALL orders to ensure nothing is missed.

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
        client = OnPrintShopClient()

        # Fetch ALL orders from OnPrintShop using pagination
        order_list = client.get_all_orders(batch_size=100)

        frappe.logger().info(f"[OPS Order Sync] Fetched {len(order_list)} orders from OnPrintShop")

        for order_data in order_list:
            try:
                orders_id = order_data.get("orders_id")
                if not orders_id:
                    continue

                # Check if order exists
                existing = frappe.db.exists("OPS Order", {"ops_order_id": str(orders_id)})

                # Sync the order (create or update)
                doc = sync_order_from_onprintshop(orders_id, order_data)

                if doc:
                    # Set sync_in_progress to prevent outgoing sync
                    frappe.db.set_value("OPS Order", doc.name, "sync_in_progress", 1, update_modified=False)

                    if existing:
                        stats["updated"] += 1
                    else:
                        stats["created"] += 1

                    stats["synced"] += 1

            except Exception as e:
                stats["errors"] += 1
                _log_ops_error(
                    error_title=f"Error syncing order {order_data.get('orders_id')}",
                    error_message=str(e),
                    error_type="Sync Error",
                    severity="High",
                    source_doctype="OPS Order",
                    source_document=str(order_data.get('orders_id')),
                    function_name="poll_onprintshop_orders",
                    request_data=json.dumps(order_data, indent=2) if order_data else None,
                    auto_retry=True,
                )

        # Clear sync_in_progress flags after batch completes
        frappe.db.sql("""
            UPDATE `tabOPS Order`
            SET sync_in_progress = 0
            WHERE sync_in_progress = 1
        """)
        frappe.db.commit()

        # Update last sync timestamp in cache
        frappe.cache().set_value("ops_order_last_sync", now_datetime())

        stats["end_time"] = now_datetime()
        frappe.logger().info(f"[OPS Order Sync] Completed: {stats}")

    except Exception as e:
        stats["error_message"] = str(e)
        _log_ops_error(
            error_title="OPS Order Sync batch failed",
            error_message=str(e),
            error_type="Sync Error",
            severity="Critical",
            function_name="poll_onprintshop_orders",
        )

    return stats


def sync_order_from_onprintshop(orders_id: int, order_data: Dict = None) -> Optional[Any]:
    """Sync a single order from OnPrintShop to Frappe.

    Args:
        orders_id: The OPS order ID
        order_data: Optional pre-fetched order data

    Returns:
        The OPS Order document or None on failure
    """
    try:
        client = OnPrintShopClient()

        # Fetch full order details if not provided
        if not order_data or "product" not in order_data:
            order_data = client.get_order(orders_id)
            if not order_data:
                # Order doesn't exist in OnPrintShop anymore
                # Use a cache key to track orders we've already logged about (avoid spam)
                cache_key = f"ops_order_not_found_{orders_id}"
                already_logged = frappe.cache().get_value(cache_key)

                if not already_logged:
                    # Log once and cache for 24 hours
                    frappe.logger().info(f"[OPS Order Sync] Order {orders_id} not found in OnPrintShop - skipping")
                    frappe.cache().set_value(cache_key, True, expires_in_sec=86400)

                return None

        # Check if order exists in Frappe
        existing_name = frappe.db.get_value("OPS Order", {"ops_order_id": str(orders_id)}, "name")
        is_new_order = not existing_name

        if existing_name:
            doc = frappe.get_doc("OPS Order", existing_name)
            # Take snapshot BEFORE mapping fields for change detection
            before_snapshot = _get_doc_snapshot(doc)
        else:
            doc = frappe.new_doc("OPS Order")
            doc.ops_order_id = str(orders_id)
            before_snapshot = None

        # Map order fields
        _map_order_fields(doc, order_data)

        # Map order products (nested in 'product' array)
        _map_order_products(doc, order_data.get("product", []))

        # Map product options from features_details to child table
        _map_product_options(doc, order_data.get("product", []))

        # Check if there are actual changes (skip save if no changes)
        if not is_new_order and before_snapshot:
            has_changes = _has_order_changed(doc, before_snapshot)
            if not has_changes:
                # No changes - just update last_synced without creating a version
                frappe.db.set_value("OPS Order", doc.name, {
                    "last_synced": now_datetime(),
                    "sync_in_progress": 0,
                    "sync_status": "Synced",
                    "sync_error": ""
                }, update_modified=False)
                return doc

        # Save with sync flags (only if new or has changes)
        doc.sync_in_progress = 1
        doc.sync_status = "Synced"
        doc.sync_error = ""

        # Bypass link validation during sync (customer/company may not exist yet)
        doc.flags.ignore_links = True
        doc.flags.ignore_validate = True

        if is_new_order:
            doc.insert(ignore_permissions=True)
            frappe.logger().info(f"[OPS Order Sync] Created new order {doc.name} (OPS ID: {orders_id})")
        else:
            doc.save(ignore_permissions=True)
            frappe.logger().info(f"[OPS Order Sync] Updated order {doc.name} with changes")

        # Update last_synced without triggering modified
        frappe.db.set_value("OPS Order", doc.name, "last_synced", now_datetime(), update_modified=False)

        return doc

    except Exception as e:
        _log_ops_error(
            error_title=f"Error syncing order {orders_id}",
            error_message=str(e),
            error_type="Sync Error",
            severity="High",
            source_doctype="OPS Order",
            source_document=str(orders_id),
            function_name="sync_order_from_onprintshop",
            request_data=json.dumps(order_data, indent=2) if order_data else None,
            auto_retry=True,
        )
        return None


def _map_order_fields(doc, order_data: Dict):
    """Map OnPrintShop order fields to Frappe OPS Order fields."""

    # Always set ops_order_id and orders_id from API data
    if order_data.get("orders_id"):
        doc.ops_order_id = str(order_data.get("orders_id"))
        doc.orders_id = cint(order_data.get("orders_id"))

    # Basic info
    doc.order_name = order_data.get("order_name") or f"Order {order_data.get('orders_id')}"

    # Status mapping - normalize to Frappe-allowed values
    status_id = cint(order_data.get("orders_status_id", 0))
    status_name = order_data.get("order_status") or ""
    doc.orders_status_id = status_id
    doc.order_status = _normalize_order_status(status_id, status_name)

    # User and corporate IDs
    if order_data.get("user_id"):
        doc.user_id = str(order_data.get("user_id"))
    if order_data.get("corporate_id"):
        doc.corporate_id = cint(order_data.get("corporate_id"))

    # Customer info (nested in 'customer' object)
    customer = order_data.get("customer") or {}
    doc.customer_name = customer.get("customers_name") or ""
    doc.customer_email = customer.get("customers_email_address") or ""
    doc.customer_telephone = customer.get("customers_telephone") or ""
    doc.customer_company_name = customer.get("customers_company") or ""
    # Note: customer_company is a Link field, may need separate handling

    # Financials
    doc.total_amount = flt(order_data.get("total_amount", 0))
    doc.order_amount = flt(order_data.get("order_amount", 0)) or doc.total_amount
    doc.shipping_amount = flt(order_data.get("shipping_amount", 0))
    doc.tax_amount = flt(order_data.get("tax_amount", 0))
    doc.coupon_amount = flt(order_data.get("coupon_amount", 0))
    doc.order_vendor_amount = flt(order_data.get("order_vendor_amount", 0))
    doc.refund_amount = flt(order_data.get("refund_amount", 0))
    doc.payment_processing_fees = flt(order_data.get("payment_processing_fees", 0))

    # Coupon info
    doc.coupon_code = order_data.get("coupon_code") or ""
    doc.coupon_type = order_data.get("coupon_type") or ""

    # PO and transaction
    doc.po_number = order_data.get("po_number") or ""
    doc.transactionid = order_data.get("transactionid") or ""

    # Weight
    doc.total_weight = flt(order_data.get("total_weight", 0))

    # Payment info
    doc.payment_method_name = order_data.get("payment_method_name") or ""
    # Normalize payment status to allowed values (Paid, Unpaid)
    payment_status = order_data.get("payment_status_title") or ""
    if payment_status:
        payment_lower = payment_status.lower()
        if "paid" in payment_lower and "unpaid" not in payment_lower:
            doc.payment_status_title = "Paid"
        elif "unpaid" in payment_lower or "pending" in payment_lower:
            doc.payment_status_title = "Unpaid"
        elif "partial" in payment_lower:
            doc.payment_status_title = "Paid"  # Treat partial as paid for now
        else:
            doc.payment_status_title = "Unpaid"  # Default to unpaid
    else:
        doc.payment_status_title = ""
    doc.invoice_number = order_data.get("invoice_number") or ""
    doc.invoice_date = _sanitize_date(order_data.get("invoice_date")) or ""

    # Shipping info (from API) - use hasattr to safely set fields
    if order_data.get("shipping_mode"):
        doc.shipping_mode = order_data.get("shipping_mode")
    # Note: API field has typo "courirer_company_name"
    courier = order_data.get("courirer_company_name") or order_data.get("courier_company_name")
    if courier:
        doc.courier_company_name = courier
    if order_data.get("airway_bill_number"):
        doc.airway_bill_number = order_data.get("airway_bill_number")
    if order_data.get("shipping_type_id"):
        doc.shipping_type_id = cint(order_data.get("shipping_type_id"))

    # Shipment details (nested in 'shipment_detail' object or list)
    shipment_data = order_data.get("shipment_detail")
    if shipment_data:
        # Handle both dict and list formats
        if isinstance(shipment_data, list) and len(shipment_data) > 0:
            shipment = shipment_data[0] if isinstance(shipment_data[0], dict) else {}
        elif isinstance(shipment_data, dict):
            shipment = shipment_data
        else:
            shipment = {}

        if shipment:
            if shipment.get("shipment_tracking_number"):
                doc.tracking_number = shipment.get("shipment_tracking_number")
            if shipment.get("shipment_company"):
                doc.shipping_carrier = shipment.get("shipment_company")

    # Dates - sanitize all date fields to handle invalid values from OnPrintShop
    orders_due_date = _sanitize_date(order_data.get("orders_due_date"))
    if orders_due_date:
        doc.orders_due_date = orders_due_date

    production_due_date = _sanitize_date(order_data.get("production_due_date"))
    if production_due_date:
        doc.production_due_date = production_due_date

    payment_due_date = _sanitize_date(order_data.get("payment_due_date"))
    if payment_due_date:
        doc.payment_due_date = payment_due_date

    payment_date = _sanitize_date(order_data.get("payment_date"))
    if payment_date:
        doc.payment_date = payment_date

    orders_date_finished = _sanitize_date(order_data.get("orders_date_finished"))
    if orders_date_finished:
        doc.orders_date_finished = orders_date_finished

    local_orders_date_finished = _sanitize_date(order_data.get("local_orders_date_finished"))
    if local_orders_date_finished:
        doc.local_orders_date_finished = local_orders_date_finished

    order_last_modified_date = _sanitize_date(order_data.get("order_last_modified_date"))
    if order_last_modified_date:
        doc.order_last_modified_date = order_last_modified_date

    # Date purchased - use date_purchased if available, fallback to orders_date_finished
    date_purchased = _sanitize_date(order_data.get("date_purchased"))
    if date_purchased:
        doc.date_purchased = date_purchased
    elif orders_date_finished:
        doc.date_purchased = orders_date_finished

    # Delivery address (nested in 'delivery_detail' object)
    delivery = order_data.get("delivery_detail") or {}
    doc.delivery_name = delivery.get("delivery_name") or ""
    doc.delivery_company = delivery.get("delivery_company") or ""
    doc.delivery_street_address = delivery.get("delivery_street_address") or ""
    doc.delivery_suburb = delivery.get("delivery_suburb") or ""
    doc.delivery_city = delivery.get("delivery_city") or ""
    doc.delivery_postcode = delivery.get("delivery_postcode") or ""
    doc.delivery_state = delivery.get("delivery_state") or ""
    doc.delivery_state_code = delivery.get("delivery_state_code") or ""
    doc.delivery_country = delivery.get("delivery_country") or ""
    doc.delivery_telephone = delivery.get("delivery_telephone") or ""

    # Billing address (nested in 'billing_detail' object)
    billing = order_data.get("billing_detail") or {}
    doc.billing_name = billing.get("billing_name") or ""
    doc.billing_company = billing.get("billing_company") or ""
    doc.billing_street_address = billing.get("billing_street_address") or ""
    doc.billing_suburb = billing.get("billing_suburb") or ""
    doc.billing_city = billing.get("billing_city") or ""
    doc.billing_postcode = billing.get("billing_postcode") or ""
    doc.billing_state = billing.get("billing_state") or ""
    doc.billing_state_code = billing.get("billing_state_code") or ""
    doc.billing_country = billing.get("billing_country") or ""
    doc.billing_phone = billing.get("billing_telephone") or ""

    # Set default values for mandatory fields that may not come from API
    if not doc.tracking_url:
        doc.tracking_url = "N/A"
    if not doc.carrier_raw_response:
        doc.carrier_raw_response = "{}"


def _map_order_products(doc, products: List[Dict]):
    """Map OnPrintShop order products to child table."""

    # Clear existing products
    doc.ops_order_products = []

    for product in products:
        row = doc.append("ops_order_products", {})
        row.orders_products_id = cint(product.get("orders_products_id", 0))
        row.product_id = cint(product.get("product_id", 0))
        row.products_name = product.get("products_name") or ""
        row.products_title = product.get("products_title") or ""
        row.products_sku = product.get("products_sku") or ""
        row.products_quantity = cint(product.get("products_quantity", 1))
        row.products_price = flt(product.get("products_price", 0))
        row.products_unit_price = flt(product.get("products_unit_price", 0))
        row.final_price = flt(product.get("products_unit_price", 0)) or flt(product.get("products_price", 0))
        row.products_vendor_price = flt(product.get("products_vendor_price", 0))
        row.products_weight = flt(product.get("products_weight", 0)) if product.get("products_weight") else 0
        row.product_status = product.get("product_status") or "Pending"
        row.product_status_id = cint(product.get("product_status_id", 0))
        row.product_production_due_date = product.get("product_production_due_date") or ""

        # Size info
        row.productsize = product.get("productsize") or ""

        # Ziflow proof link
        row.ziflow_proof_url = product.get("ziflow_link") or ""
        # Try to link to existing OPS ZiFlow Proof by matching URL
        if row.ziflow_proof_url:
            # Try matching by order ID and line ID (more reliable than URL)
            proof_name = frappe.db.get_value("OPS ZiFlow Proof", {"ops_order": doc.name, "ops_line_id": row.orders_products_id}, "name")
            # Fallback to URL matching if line ID match fails
            if not proof_name and row.ziflow_proof_url:
                proof_name = frappe.db.get_value("OPS ZiFlow Proof", {"ziflow_url": row.ziflow_proof_url}, "name")
            if proof_name:
                row.ziflow_proof = proof_name

        # Product attributes/features (JSON field)
        features = product.get("features_details")
        if features:
            if isinstance(features, dict):
                row.features_details = json.dumps(features)
            elif isinstance(features, str):
                row.features_details = features
            else:
                row.features_details = json.dumps(features) if features else ""
        else:
            row.features_details = ""

        # Product size details (JSON)
        size_details = product.get("product_size_details")
        if size_details:
            if isinstance(size_details, dict):
                row.product_size_details = json.dumps(size_details)
            elif isinstance(size_details, str):
                row.product_size_details = size_details
            else:
                row.product_size_details = json.dumps(size_details) if size_details else ""

        # Template info
        row.template_type = product.get("template_type") or ""

        # Template info (JSON)
        template_info = product.get("template_info")
        if template_info:
            if isinstance(template_info, dict):
                row.template_info = json.dumps(template_info)
            elif isinstance(template_info, str):
                row.template_info = template_info

        # Product info (JSON)
        product_info = product.get("product_info")
        if product_info:
            if isinstance(product_info, dict):
                row.product_info = json.dumps(product_info)
            elif isinstance(product_info, str):
                row.product_info = product_info




def _map_product_options(doc, products: List[Dict]):
    """Parse features_details from products and populate order_product_options child table."""
    
    # Clear existing options
    doc.order_product_options = []
    
    for product in products:
        features = product.get("features_details")
        if not features:
            continue
        
        # Parse JSON if string
        if isinstance(features, str):
            try:
                features = json.loads(features)
            except (json.JSONDecodeError, TypeError):
                continue
        
        if not isinstance(features, dict):
            continue
        
        orders_products_id = product.get("orders_products_id", 0)
        product_name = product.get("products_name") or product.get("products_title") or ""
        
        # Iterate through each option (AO-1, AO-2, etc.)
        for option_key, option_data in features.items():
            if not isinstance(option_data, dict):
                continue
            
            # Extract option fields
            option_name = option_data.get("Heading") or option_data.get("option_key") or option_key
            option_value = option_data.get("AttributeValue") or option_data.get("AttributeLabel") or ""
            option_price = flt(option_data.get("option_price", 0))
            vendor_price = flt(option_data.get("vendor_price", 0))
            option_group = option_data.get("optionGroup") or ""
            option_id = cint(option_data.get("optionId", 0))
            attribute_id = cint(option_data.get("attributeId", 0)) if option_data.get("attributeId") else 0
            master_option_id = option_data.get("master_option_id")
            
            # Skip empty options
            if not option_name or option_name == "-":
                continue
            
            # Create child row
            row = doc.append("order_product_options", {})
            row.option_name = option_name[:140] if option_name else ""
            row.option_value = str(option_value)[:140] if option_value else ""
            row.option_price = option_price
            row.vendor_price = vendor_price
            row.option_group = option_group[:140] if option_group else ""
            row.option_id = option_id
            row.attribute_id = attribute_id
            row.orders_products_id = cint(orders_products_id)
            row.product_name = product_name[:140] if product_name else ""
            if master_option_id:
                row.master_option = str(master_option_id)


def push_order_to_onprintshop(doc, method: str = None) -> Optional[Dict]:
    """Push local order changes to OnPrintShop.

    Called by doc_events on OPS Order on_update.
    Skips if sync_in_progress is True (indicates incoming sync).

    Args:
        doc: OPS Order document
        method: Hook method name (unused)

    Returns:
        API response or None if skipped
    """
    # Skip if this is an incoming sync (sync_in_progress flag set)
    if cint(doc.sync_in_progress):
        frappe.logger().debug(f"[OPS Order Sync] Skipping push for {doc.name} - sync_in_progress")
        return None

    # Skip if no ops_order_id (not synced from OPS yet)
    if not doc.ops_order_id:
        frappe.logger().debug(f"[OPS Order Sync] Skipping push for {doc.name} - no ops_order_id")
        return None

    # Check if there are actual local changes (modified > last_synced)
    if doc.last_synced and doc.modified:
        if get_datetime(doc.modified) <= get_datetime(doc.last_synced):
            frappe.logger().debug(f"[OPS Order Sync] Skipping push for {doc.name} - no changes since last sync")
            return None

    try:
        client = OnPrintShopClient()

        # Currently only pushing status changes
        # Full order updates would require setOrder mutation from OPS API
        if doc.order_status and doc.orders_status_id:
            result = client.update_order_status(
                order_id=int(doc.ops_order_id),
                status_id=int(doc.orders_status_id)
            )

            # Update last_synced timestamp without triggering another save
            frappe.db.set_value("OPS Order", doc.name, {
                "last_synced": now_datetime(),
                "sync_status": "Synced",
                "sync_error": ""
            }, update_modified=False)

            frappe.logger().info(f"[OPS Order Sync] Pushed order {doc.name} status to OnPrintShop: {result}")
            return result

    except Exception as e:
        # Update sync error
        frappe.db.set_value("OPS Order", doc.name, {
            "sync_status": "Error",
            "sync_error": str(e)[:500]
        }, update_modified=False)

        _log_ops_error(
            error_title=f"Error pushing order {doc.name} to OnPrintShop",
            error_message=str(e),
            error_type="API Error",
            severity="High",
            source_doctype="OPS Order",
            source_document=doc.name,
            function_name="push_order_to_onprintshop",
            auto_retry=True,
        )
        return None


@frappe.whitelist()
def manual_sync_from_ops(order_name: str) -> Dict:
    """Manually trigger sync from OnPrintShop for a specific order.

    Args:
        order_name: Name of the OPS Order document

    Returns:
        Sync result
    """
    doc = frappe.get_doc("OPS Order", order_name)

    if not doc.ops_order_id:
        frappe.throw("Order has no OnPrintShop ops_order_id")

    try:
        result = sync_order_from_onprintshop(int(doc.ops_order_id))

        if result:
            # Clear sync flag
            frappe.db.set_value("OPS Order", doc.name, "sync_in_progress", 0, update_modified=False)
            frappe.db.commit()

            return {"status": "success", "message": f"Synced order {doc.ops_order_id} from OnPrintShop"}
        else:
            return {"status": "error", "message": f"Failed to sync order {doc.ops_order_id}"}

    except Exception as e:
        _log_ops_error(
            error_title=f"Manual sync failed for order {order_name}",
            error_message=str(e),
            error_type="Sync Error",
            severity="High",
            source_doctype="OPS Order",
            source_document=order_name,
            function_name="manual_sync_from_ops",
        )
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def manual_push_to_ops(order_name: str) -> Dict:
    """Manually push an order status to OnPrintShop.

    Args:
        order_name: Name of the OPS Order document

    Returns:
        Push result
    """
    doc = frappe.get_doc("OPS Order", order_name)

    if not doc.ops_order_id:
        frappe.throw("Order has no OnPrintShop ops_order_id")

    try:
        client = OnPrintShopClient()

        status_id = doc.orders_status_id or FRAPPE_STATUS_MAP.get(doc.order_status, 1)

        result = client.update_order_status(
            order_id=int(doc.ops_order_id),
            status_id=status_id
        )

        # Update last_synced
        frappe.db.set_value("OPS Order", doc.name, {
            "last_synced": now_datetime(),
            "sync_status": "Synced"
        }, update_modified=False)
        frappe.db.commit()

        return {"status": "success", "message": f"Pushed order {doc.ops_order_id} to OnPrintShop", "result": result}

    except Exception as e:
        _log_ops_error(
            error_title=f"Manual push failed for order {order_name}",
            error_message=str(e),
            error_type="API Error",
            severity="High",
            source_doctype="OPS Order",
            source_document=order_name,
            function_name="manual_push_to_ops",
        )
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def test_api_connection() -> Dict:
    """Test the OnPrintShop orders API connection.

    Returns:
        Dict with API test results
    """
    try:
        client = OnPrintShopClient()
        result = client.get_orders(limit=5)

        orders = result.get("orders", [])
        total = result.get("totalOrders", 0)

        return {
            "status": "success",
            "total_orders": total,
            "fetched": len(orders),
            "sample_orders": [
                {
                    "orders_id": o.get("orders_id"),
                    "order_status": o.get("order_status"),
                    "order_name": o.get("order_name"),
                    "customer_name": (o.get("customer") or {}).get("customers_name", "")
                }
                for o in orders[:3]
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def sync_recent_orders(limit: int = 50) -> Dict:
    """Sync recent orders from OnPrintShop.

    Called from dashboard Sync button to fetch latest orders.

    Args:
        limit: Maximum number of orders to sync

    Returns:
        Dict with sync results
    """
    try:
        client = OnPrintShopClient()
        result = client.get_orders(limit=int(limit), sort_by="date_purchased", sort_order="DESC")

        orders = result.get("orders", [])
        synced = 0
        errors = 0

        for order_data in orders:
            try:
                orders_id = order_data.get("orders_id")
                if orders_id:
                    sync_order_from_onprintshop(orders_id, order_data)
                    synced += 1
            except Exception as e:
                errors += 1
                frappe.log_error(
                    message=f"Error syncing order {order_data.get('orders_id')}: {str(e)}",
                    title="Sync Recent Orders Error"
                )

        frappe.db.commit()

        return {
            "status": "success",
            "synced": synced,
            "errors": errors,
            "total_fetched": len(orders)
        }
    except Exception as e:
        frappe.log_error(
            message=str(e),
            title="Sync Recent Orders Failed"
        )
        return {
            "status": "error",
            "message": str(e),
            "synced": 0
        }


@frappe.whitelist()
def backfill_ops_order_ids() -> Dict:
    """Backfill ops_order_id for orders where it's missing or zero.

    Since autoname is field:ops_order_id, the document name IS the order ID.
    This function copies name to ops_order_id for records where it's missing.

    Returns:
        Dict with backfill results
    """
    try:
        # Find orders where ops_order_id is NULL, empty, or '0'
        orders_to_fix = frappe.db.sql("""
            SELECT name
            FROM `tabOPS Order`
            WHERE ops_order_id IS NULL
               OR ops_order_id = ''
               OR ops_order_id = '0'
               OR ops_order_id = 0
        """, as_dict=True)

        fixed_count = 0
        for order in orders_to_fix:
            frappe.db.set_value("OPS Order", order.name, "ops_order_id", order.name, update_modified=False)
            fixed_count += 1

        frappe.db.commit()

        return {
            "status": "success",
            "fixed": fixed_count,
            "message": f"Backfilled ops_order_id for {fixed_count} orders"
        }
    except Exception as e:
        frappe.log_error(f"Backfill ops_order_id failed: {str(e)}", "OPS Order Backfill Error")
        return {
            "status": "error",
            "message": str(e)
        }


def full_sync_from_ops(batch_size: int = 50) -> Dict:
    """Full sync of all orders from OnPrintShop.

    Use for initial import or recovery.

    Args:
        batch_size: Number of orders per API call

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
        all_orders = client.get_all_orders(batch_size=batch_size)

        frappe.logger().info(f"[OPS Order Full Sync] Fetched {len(all_orders)} orders")

        for order_data in all_orders:
            try:
                orders_id = order_data.get("orders_id")
                if not orders_id:
                    continue

                existing = frappe.db.exists("OPS Order", {"ops_order_id": str(orders_id)})
                doc = sync_order_from_onprintshop(orders_id, order_data)

                if doc:
                    if existing:
                        stats["updated"] += 1
                    else:
                        stats["created"] += 1

                    stats["synced"] += 1

                    # Commit every 50 records
                    if stats["synced"] % 50 == 0:
                        frappe.db.commit()
                        frappe.logger().info(f"[OPS Order Full Sync] Progress: {stats['synced']}/{len(all_orders)}")

            except Exception as e:
                stats["errors"] += 1
                _log_ops_error(
                    error_title=f"Error syncing order {order_data.get('orders_id')} in full sync",
                    error_message=str(e),
                    error_type="Sync Error",
                    severity="Medium",
                    source_doctype="OPS Order",
                    source_document=str(order_data.get('orders_id')),
                    function_name="full_sync_from_ops",
                    auto_retry=True,
                )

        frappe.db.commit()
        stats["end_time"] = now_datetime()
        frappe.logger().info(f"[OPS Order Full Sync] Completed: {stats}")

    except Exception as e:
        stats["error_message"] = str(e)
        _log_ops_error(
            error_title="OPS Order Full Sync batch failed",
            error_message=str(e),
            error_type="Sync Error",
            severity="Critical",
            function_name="full_sync_from_ops",
        )

    return stats
