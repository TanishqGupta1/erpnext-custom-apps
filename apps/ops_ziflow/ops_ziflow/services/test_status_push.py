"""Test pushing status change from Frappe to OPS."""

import frappe

def test_status_change():
    """Change order status and verify it pushes to OPS."""
    # Get the order
    doc = frappe.get_doc("OPS Order", "2153")

    print(f"Before change:")
    print(f"  order_status: {doc.order_status}")
    print(f"  orders_status_id: {doc.orders_status_id}")
    print(f"  sync_in_progress: {doc.sync_in_progress}")
    print(f"  last_synced: {doc.last_synced}")

    # Change status to "Ready for Fulfillment" (status_id 8)
    doc.order_status = "Ready for Fulfillment"
    doc.orders_status_id = 8
    doc.sync_in_progress = 0  # Make sure it's not blocked

    # Save - this should trigger the on_update hook
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # Re-fetch to see updated sync status
    doc.reload()

    print(f"\nAfter change:")
    print(f"  order_status: {doc.order_status}")
    print(f"  orders_status_id: {doc.orders_status_id}")
    print(f"  sync_status: {doc.sync_status}")
    print(f"  sync_error: {doc.sync_error}")
    print(f"  last_synced: {doc.last_synced}")

    return {
        "status": "done",
        "order_status": doc.order_status,
        "sync_status": doc.sync_status,
        "sync_error": doc.sync_error
    }
