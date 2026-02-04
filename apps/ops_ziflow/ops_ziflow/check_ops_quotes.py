"""Check quote counts in OPS vs Frappe"""
import frappe
from ops_ziflow.services.onprintshop_client import OnPrintShopClient

def check():
    # Check Frappe count
    frappe_count = frappe.db.count("OPS Quote")
    frappe_max = frappe.db.sql("SELECT MAX(quote_id) FROM `tabOPS Quote`")[0][0] or 0
    frappe_min = frappe.db.sql("SELECT MIN(quote_id) FROM `tabOPS Quote`")[0][0] or 0

    print(f"\n=== Frappe OPS Quote ===")
    print(f"Total: {frappe_count}")
    print(f"Quote ID range: {frappe_min} - {frappe_max}")

    # Check OPS count
    try:
        client = OnPrintShopClient()
        result = client.get_quotes(limit=1, offset=0)
        ops_total = result.get("totalQuote", 0)
        quotes = result.get("quote", [])

        print(f"\n=== OnPrintShop ===")
        print(f"Total quotes: {ops_total}")

        if quotes:
            print(f"Latest quote_id: {quotes[0].get('quote_id')}")

        # Calculate difference
        print(f"\n=== Sync Status ===")
        print(f"In Frappe: {frappe_count}")
        print(f"In OPS: {ops_total}")
        print(f"Missing: {ops_total - frappe_count}")

    except Exception as e:
        print(f"Error connecting to OPS: {e}")
