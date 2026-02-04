"""Shipment synchronization service for OPS Orders."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import frappe
from frappe.utils import now_datetime

from ops_ziflow.services.onprintshop_client import OnPrintShopClient


# Carrier tracking URL templates
CARRIER_TRACKING_URLS = {
    "ups": "https://www.ups.com/track?tracknum={tracking}",
    "fedex": "https://www.fedex.com/fedextrack/?trknbr={tracking}",
    "usps": "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking}",
    "dhl": "https://www.dhl.com/us-en/home/tracking/tracking-express.html?submit=1&tracking-id={tracking}",
    "ontrac": "https://www.ontrac.com/tracking/?trackingres=ref&trackingnumber={tracking}",
    "gso": "https://www.gso.com/Tracking?TrackingNumbers={tracking}",
    "spee-dee": "https://speedeedelivery.com/track/{tracking}",
    "speedee": "https://speedeedelivery.com/track/{tracking}",
    "lasership": "https://www.lasership.com/track/{tracking}",
    "amazon": "https://track.amazon.com/tracking/{tracking}",
}


def get_tracking_url(carrier: str, tracking_number: str) -> Optional[str]:
    """Generate tracking URL based on carrier name."""
    if not carrier or not tracking_number:
        return None

    carrier_lower = carrier.lower().strip()

    # Try exact match
    if carrier_lower in CARRIER_TRACKING_URLS:
        return CARRIER_TRACKING_URLS[carrier_lower].format(tracking=tracking_number)

    # Try partial match
    for name, url_template in CARRIER_TRACKING_URLS.items():
        if name in carrier_lower or carrier_lower in name:
            return url_template.format(tracking=tracking_number)

    return None


def sync_order_shipments(order_name: str) -> Dict[str, Any]:
    """Sync shipments for a specific order from OPS API.

    Args:
        order_name: The Frappe OPS Order document name

    Returns:
        Dict with sync results
    """
    try:
        order = frappe.get_doc("OPS Order", order_name)
        ops_order_id = order.ops_order_id

        if not ops_order_id:
            return {"success": False, "error": "No OPS Order ID found"}

        # Fetch from OPS API
        client = OnPrintShopClient()
        ops_order = client.get_order(int(ops_order_id))

        if not ops_order:
            return {"success": False, "error": f"Order {ops_order_id} not found in OPS"}

        shipment_details = ops_order.get("shipment_detail") or []
        if not isinstance(shipment_details, list):
            shipment_details = [shipment_details] if shipment_details else []

        synced = 0
        created = 0

        # Clear existing shipments and re-add from API
        existing_shipments = {s.ops_shipment_id: s for s in order.shipments if s.ops_shipment_id}

        for i, shipment in enumerate(shipment_details):
            tracking = shipment.get("shipment_tracking_number")
            carrier = shipment.get("shipment_company") or ops_order.get("courirer_company_name") or "Unknown"
            weight = shipment.get("shipment_total_weight")

            # Use index as shipment ID if not available
            shipment_id = i + 1

            # Check if this shipment already exists
            if shipment_id in existing_shipments:
                # Update existing
                row = existing_shipments[shipment_id]
                row.carrier = carrier
                row.tracking_number = tracking
                row.total_weight = weight
                row.tracking_url = get_tracking_url(carrier, tracking)
                row.last_synced = now_datetime()
                synced += 1
            else:
                # Create new
                row = order.append("shipments", {
                    "ops_shipment_id": shipment_id,
                    "carrier": carrier,
                    "tracking_number": tracking,
                    "total_weight": weight,
                    "tracking_url": get_tracking_url(carrier, tracking),
                    "shipment_status": "Pending" if not tracking else "Label Created",
                    "last_synced": now_datetime()
                })
                created += 1

        # Also sync primary shipment fields on order
        if ops_order.get("courirer_company_name"):
            order.courier_company_name = ops_order.get("courirer_company_name")
        if ops_order.get("airway_bill_number"):
            order.tracking_number = ops_order.get("airway_bill_number")
            order.tracking_url = get_tracking_url(order.courier_company_name, order.tracking_number)

        order.last_tracking_update = now_datetime()
        order.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "synced": synced,
            "created": created,
            "total_shipments": len(order.shipments)
        }

    except Exception as e:
        frappe.log_error(f"Error syncing shipments for {order_name}: {str(e)}", "Shipment Sync Error")
        return {"success": False, "error": str(e)}


def push_shipment_to_ops(order_name: str, shipment_idx: int = None) -> Dict[str, Any]:
    """Push shipment data from Frappe to OPS API.

    Args:
        order_name: The Frappe OPS Order document name
        shipment_idx: Optional specific shipment row index to push

    Returns:
        Dict with push results
    """
    try:
        order = frappe.get_doc("OPS Order", order_name)
        ops_order_id = order.ops_order_id

        if not ops_order_id:
            return {"success": False, "error": "No OPS Order ID found"}

        client = OnPrintShopClient()
        pushed = 0
        errors = []

        # Get shipments to push
        shipments_to_push = order.shipments
        if shipment_idx is not None:
            shipments_to_push = [order.shipments[shipment_idx]] if shipment_idx < len(order.shipments) else []

        for shipment in shipments_to_push:
            if not shipment.tracking_number:
                continue

            try:
                result = client.set_shipment(
                    order_id=int(ops_order_id),
                    tracking_number=shipment.tracking_number,
                    shipment_id=shipment.ops_shipment_id if shipment.ops_shipment_id else None,
                    shipment_info={
                        "carrier": shipment.carrier,
                        "weight": shipment.total_weight,
                        "package_count": shipment.package_count
                    }
                )

                if result.get("result"):
                    # Update the shipment ID if returned
                    if result.get("shipment_id"):
                        shipment.ops_shipment_id = result.get("shipment_id")
                    shipment.last_synced = now_datetime()
                    shipment.sync_error = None
                    pushed += 1
                else:
                    shipment.sync_error = result.get("message", "Unknown error")
                    errors.append(f"Shipment {shipment.idx}: {shipment.sync_error}")

            except Exception as e:
                shipment.sync_error = str(e)
                errors.append(f"Shipment {shipment.idx}: {str(e)}")

        order.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": len(errors) == 0,
            "pushed": pushed,
            "errors": errors
        }

    except Exception as e:
        frappe.log_error(f"Error pushing shipments for {order_name}: {str(e)}", "Shipment Push Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def sync_shipment(order_name: str) -> Dict[str, Any]:
    """API method to sync shipments for an order."""
    return sync_order_shipments(order_name)


@frappe.whitelist()
def push_shipment(order_name: str, shipment_idx: int = None) -> Dict[str, Any]:
    """API method to push shipment to OPS."""
    return push_shipment_to_ops(order_name, int(shipment_idx) if shipment_idx else None)


@frappe.whitelist()
def add_shipment(order_name: str, carrier: str, tracking_number: str,
                 package_count: int = 1, weight: float = None) -> Dict[str, Any]:
    """Add a new shipment to an order and push to OPS.

    Args:
        order_name: The Frappe OPS Order document name
        carrier: Carrier name (e.g., 'UPS', 'FedEx')
        tracking_number: Tracking number
        package_count: Number of packages
        weight: Total weight in lbs

    Returns:
        Dict with result
    """
    try:
        order = frappe.get_doc("OPS Order", order_name)

        # Add shipment row
        row = order.append("shipments", {
            "carrier": carrier,
            "tracking_number": tracking_number,
            "tracking_url": get_tracking_url(carrier, tracking_number),
            "package_count": package_count,
            "total_weight": weight,
            "shipment_status": "Label Created",
            "shipped_date": now_datetime()
        })

        order.save(ignore_permissions=True)
        frappe.db.commit()

        # Push to OPS
        if order.ops_order_id:
            push_result = push_shipment_to_ops(order_name, len(order.shipments) - 1)
            return {
                "success": True,
                "shipment_added": True,
                "push_result": push_result
            }

        return {"success": True, "shipment_added": True}

    except Exception as e:
        frappe.log_error(f"Error adding shipment to {order_name}: {str(e)}", "Add Shipment Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_shipment_status(order_name: str, shipment_idx: int, status: str,
                           delivered_date: str = None) -> Dict[str, Any]:
    """Update shipment status.

    Args:
        order_name: The Frappe OPS Order document name
        shipment_idx: Shipment row index
        status: New status
        delivered_date: Delivery date if status is 'Delivered'

    Returns:
        Dict with result
    """
    try:
        order = frappe.get_doc("OPS Order", order_name)

        if shipment_idx >= len(order.shipments):
            return {"success": False, "error": "Invalid shipment index"}

        shipment = order.shipments[int(shipment_idx)]
        shipment.shipment_status = status

        if status == "Delivered" and delivered_date:
            shipment.delivered_date = delivered_date
        elif status == "Delivered" and not shipment.delivered_date:
            shipment.delivered_date = now_datetime()

        order.save(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "status": status}

    except Exception as e:
        frappe.log_error(f"Error updating shipment status: {str(e)}", "Update Shipment Error")
        return {"success": False, "error": str(e)}


def sync_all_order_shipments(limit: int = 100) -> Dict[str, Any]:
    """Sync shipments for all recent active orders.

    Args:
        limit: Maximum number of orders to sync

    Returns:
        Dict with sync summary
    """
    active_statuses = ["New Order", "In Design", "Order Processing", "In Production",
                       "Ready for Fulfillment", "Partially Shipped"]

    orders = frappe.get_all(
        "OPS Order",
        filters={"order_status": ["in", active_statuses]},
        fields=["name", "ops_order_id"],
        order_by="modified desc",
        limit=limit
    )

    results = {
        "total": len(orders),
        "success": 0,
        "failed": 0,
        "errors": []
    }

    for order in orders:
        result = sync_order_shipments(order.name)
        if result.get("success"):
            results["success"] += 1
        else:
            results["failed"] += 1
            results["errors"].append(f"{order.name}: {result.get('error')}")

    return results
