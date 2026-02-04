# sync_sample_quotes.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.sync_sample_quotes.sync_quotes

import frappe
import requests
import json

OPS_GRAPHQL_URL = "https://admin.onprintshop.com/graphql"
OPS_API_KEY = "NjcwNGNjMTI3MzA3Mzk2NDcwNGNjMTI3MzA3Mzk="

def fetch_quotes_from_ops(limit=2):
    """Fetch quotes from OnPrintShop GraphQL API"""

    query = """
        query get_quote($quote_id: Int, $user_id: Int, $limit: Int, $offset: Int) {
            get_quote(quote_id: $quote_id, user_id: $user_id, limit: $limit, offset: $offset) {
                quote {
                    quote_id
                    user_id
                    quote_title
                    quote_price
                    quote_vendor_price
                    sort_order
                    quote_status
                    quote_date
                    admin_notes
                    quote_shipping_addr
                    quote_billing_addr
                    ship_amt
                    quote_tax_exampt
                    quoteproduct {
                        isCustomProduct
                        quote_products_id
                        quote_id
                        products_id
                        products_title
                        quote_products_quantity
                        quote_products_price
                        quote_products_vendor_price
                        quote_products_info
                        products_prd_day
                        products_weight
                        quote_product_sku
                        quote_product_notes
                    }
                }
                totalQuote
            }
        }
    """

    variables = {
        'quote_id': None,
        'user_id': None,
        'limit': limit,
        'offset': 0
    }

    headers = {
        'Content-Type': 'application/json',
        'api_key': OPS_API_KEY
    }

    response = requests.post(
        OPS_GRAPHQL_URL,
        json={'query': query, 'variables': variables},
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'get_quote' in data['data']:
            return data['data']['get_quote']

    print(f"Error fetching quotes: {response.status_code} - {response.text}")
    return None


def sync_quotes():
    """Sync sample quotes from OnPrintShop to Frappe"""

    print("Fetching quotes from OnPrintShop...")
    result = fetch_quotes_from_ops(limit=2)

    if not result:
        print("No quotes fetched from OnPrintShop")
        return

    quotes = result.get('quote', [])
    total = result.get('totalQuote', 0)

    print(f"Found {total} total quotes, fetching {len(quotes)}")

    for quote_data in quotes:
        quote_id = quote_data.get('quote_id')
        print(f"\nSyncing Quote ID: {quote_id}")
        print(f"  Title: {quote_data.get('quote_title')}")
        print(f"  Price: {quote_data.get('quote_price')}")
        print(f"  Products: {len(quote_data.get('quoteproduct', []))}")

        try:
            # Check if quote already exists
            if frappe.db.exists('OPS Quote', {'quote_id': quote_id}):
                doc = frappe.get_doc('OPS Quote', {'quote_id': quote_id})
                print(f"  Updating existing quote...")
            else:
                doc = frappe.new_doc('OPS Quote')
                doc.quote_id = quote_id
                print(f"  Creating new quote...")

            # Sync data from OPS
            doc.sync_from_onprintshop(quote_data)
            doc.save(ignore_permissions=True)

            print(f"  SUCCESS: Quote {quote_id} synced")
            print(f"    - Total Amount: {doc.total_amount}")
            print(f"    - Profit Margin: {doc.profit_margin}")
            print(f"    - Profit %: {doc.profit_percentage}")
            print(f"    - Products synced: {len(doc.quote_products or [])}")

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    frappe.db.commit()
    print("\n=== Sync Complete ===")


if __name__ == "__main__":
    sync_quotes()
