"""Set the baseline for incremental quote sync"""
import frappe

def set_baseline():
    """Set the last synced quote ID based on current max in Frappe.

    This allows incremental sync to work without doing a full import.
    """
    max_quote_id = frappe.db.sql("SELECT MAX(quote_id) FROM `tabOPS Quote`")[0][0] or 0

    # Set in cache for incremental sync
    frappe.cache().set_value("ops_quote_last_synced_id", max_quote_id)

    # Also update last_synced for all quotes that don't have it
    updated = frappe.db.sql("""
        UPDATE `tabOPS Quote`
        SET last_synced = NOW()
        WHERE last_synced IS NULL OR last_synced < DATE_SUB(NOW(), INTERVAL 24 HOUR)
    """)
    frappe.db.commit()

    count_updated = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS Quote`
        WHERE last_synced >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)
    """)[0][0]

    print(f"\n=== Quote Sync Baseline Set ===")
    print(f"Max quote_id in Frappe: {max_quote_id}")
    print(f"Set ops_quote_last_synced_id: {max_quote_id}")
    print(f"Updated last_synced for {count_updated} quotes")
    print(f"\nIncremental sync will now only fetch quotes with quote_id > {max_quote_id}")
