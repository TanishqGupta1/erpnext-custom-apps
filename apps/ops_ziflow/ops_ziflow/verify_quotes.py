# verify_quotes.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.verify_quotes.verify

import frappe

def verify():
    """Verify quote sync results"""

    # Count quotes
    quote_count = frappe.db.count('OPS Quote')
    product_count = frappe.db.count('OPS Quote Product')
    option_count = frappe.db.count('OPS Quote Product Option')

    print(f"=== OPS Quote Sync Verification ===")
    print(f"Total Quotes: {quote_count}")
    print(f"Total Products: {product_count}")
    print(f"Total Product Options: {option_count}")

    # Status breakdown
    print(f"\n=== Status Breakdown ===")
    statuses = frappe.db.sql("""
        SELECT quote_status, COUNT(*) as count
        FROM `tabOPS Quote`
        GROUP BY quote_status
        ORDER BY count DESC
    """, as_dict=True)

    for s in statuses:
        print(f"  {s['quote_status']}: {s['count']}")

    # Quote value summary
    print(f"\n=== Value Summary ===")
    totals = frappe.db.sql("""
        SELECT
            SUM(quote_price) as total_quote_value,
            SUM(quote_vendor_price) as total_vendor_cost,
            SUM(profit_margin) as total_profit
        FROM `tabOPS Quote`
    """, as_dict=True)[0]

    print(f"  Total Quote Value: ${totals['total_quote_value']:,.2f}")
    print(f"  Total Vendor Cost: ${totals['total_vendor_cost']:,.2f}")
    print(f"  Total Profit: ${totals['total_profit']:,.2f}")


if __name__ == "__main__":
    verify()
