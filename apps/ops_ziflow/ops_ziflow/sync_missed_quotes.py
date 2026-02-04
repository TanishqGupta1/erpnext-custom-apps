# sync_missed_quotes.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.sync_missed_quotes.sync_missed

import frappe
import json
import os

def sync_missed():
    """Sync missed quotes from JSON file"""

    json_path = '/home/frappe/frappe-bench/apps/ops_ziflow/ops_ziflow/missed_quotes.json'

    if not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    if not data.get('data') or not data['data'].get('get_quote'):
        print("No quote data found in JSON")
        return

    quotes = data['data']['get_quote']['quote']
    print(f"Found {len(quotes)} missed quotes to sync")

    success_count = 0
    error_count = 0
    new_count = 0
    update_count = 0

    for quote_data in quotes:
        quote_id = quote_data.get('quote_id')
        quote_title = quote_data.get('quote_title', 'Untitled')

        try:
            existing = frappe.db.exists('OPS Quote', {'quote_id': quote_id})

            if existing:
                doc = frappe.get_doc('OPS Quote', {'quote_id': quote_id})
                action = "Updated"
                update_count += 1
            else:
                doc = frappe.new_doc('OPS Quote')
                doc.quote_id = quote_id
                action = "Created"
                new_count += 1

            doc.sync_from_onprintshop(quote_data)
            doc.save(ignore_permissions=True)

            product_count = len(doc.quote_products or [])
            option_count = len(doc.quote_product_options or [])

            print(f"  {action}: {quote_id} - {quote_title} ({product_count} products, {option_count} options)")
            success_count += 1

        except Exception as e:
            print(f"  ERROR {quote_id} - {quote_title}: {str(e)}")
            error_count += 1

    frappe.db.commit()

    print(f"\n=== Sync Complete ===")
    print(f"  New: {new_count}")
    print(f"  Updated: {update_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {success_count + error_count}")


if __name__ == "__main__":
    sync_missed()
