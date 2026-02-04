"""Check quote sync status"""
import frappe
from frappe.utils import now_datetime, add_days

def check_status():
    # Get total count
    total = frappe.db.count("OPS Quote")

    # Get synced in last hour
    last_hour = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS Quote`
        WHERE last_synced >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    """)[0][0]

    # Get synced in last 24 hours
    last_24h = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS Quote`
        WHERE last_synced >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    """)[0][0]

    # Get never synced
    never_synced = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS Quote`
        WHERE last_synced IS NULL
    """)[0][0]

    print(f"\n=== OPS Quote Sync Status ===")
    print(f"Total Quotes: {total}")
    print(f"Synced in last hour: {last_hour}")
    print(f"Synced in last 24h: {last_24h}")
    print(f"Never synced: {never_synced}")
    print(f"Stale (>24h): {total - last_24h}")
    print(f"\nSync coverage: {(last_24h/total*100):.1f}%" if total > 0 else "N/A")
