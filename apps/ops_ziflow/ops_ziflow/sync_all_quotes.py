# sync_all_quotes.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.sync_all_quotes.sync_all

import frappe
import json
import os

def sync_all():
    """Sync all quotes from JSON file to Frappe OPS Quote DocType"""

    # Read from JSON file
    json_path = '/home/frappe/frappe-bench/apps/ops_ziflow/ops_ziflow/quotes_result.json'

    if not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    if not data.get('data') or not data['data'].get('get_quote'):
        print("No quote data found in JSON")
        print(f"Errors: {data.get('errors', [])}")
        return

    quotes = data['data']['get_quote']['quote']
    total_quote = data['data']['get_quote'].get('totalQuote', len(quotes))

    print(f"Found {len(quotes)} quotes (total in system: {total_quote})")

    success_count = 0
    error_count = 0

    for quote_data in quotes:
        quote_id = quote_data.get('quote_id')
        quote_title = quote_data.get('quote_title', 'Untitled')

        try:
            # Check if quote already exists
            existing = frappe.db.exists('OPS Quote', {'quote_id': quote_id})

            if existing:
                doc = frappe.get_doc('OPS Quote', {'quote_id': quote_id})
                action = "Updated"
            else:
                doc = frappe.new_doc('OPS Quote')
                doc.quote_id = quote_id
                action = "Created"

            # Sync data using the sync_from_onprintshop method
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
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {success_count + error_count}")


if __name__ == "__main__":
    sync_all()
