# sync_quotes_from_json.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.sync_quotes_from_json.sync_quotes

import frappe
import json

# Embedded quote data from OnPrintShop API
QUOTES_DATA = {
    "get_quote": {
        "quote": [
            {
                "quote_id": 1641,
                "user_id": 476,
                "quote_title": "Luncheon Branding",
                "quote_price": 1987.52,
                "quote_vendor_price": 356.434,
                "sort_order": 0,
                "quote_status": 9,
                "quote_date": "2025-12-19 14:55:23",
                "admin_notes": None,
                "quote_shipping_addr": 354,
                "quote_billing_addr": 354,
                "ship_amt": 0,
                "quote_tax_exampt": False,
                "quoteproduct": [
                    {
                        "isCustomProduct": 0,
                        "quote_products_id": 5405,
                        "quote_id": 1641,
                        "products_id": 201,
                        "products_title": "e_201",
                        "quote_products_quantity": 1,
                        "quote_products_price": 1247.52,
                        "quote_products_vendor_price": 356.434086,
                        "quote_products_info": [{"Heading": "Job Name", "AttributeValue": "Coroplast Signs"}],
                        "products_prd_day": "2",
                        "products_weight": 2.02176,
                        "quote_product_sku": None,
                        "quote_product_notes": None
                    },
                    {
                        "isCustomProduct": 1,
                        "quote_products_id": 5406,
                        "quote_id": 1641,
                        "products_id": 0,
                        "products_title": "Cardstock Cards",
                        "quote_products_quantity": 1,
                        "quote_products_price": 340,
                        "quote_products_vendor_price": None,
                        "quote_products_info": [{"Heading": "Job Name", "AttributeValue": "Menu Cards"}],
                        "products_prd_day": "0",
                        "products_weight": 0,
                        "quote_product_sku": None,
                        "quote_product_notes": None
                    },
                    {
                        "isCustomProduct": 1,
                        "quote_products_id": 5407,
                        "quote_id": 1641,
                        "products_id": 0,
                        "products_title": "18pt Cardstock",
                        "quote_products_quantity": 1,
                        "quote_products_price": 400,
                        "quote_products_vendor_price": None,
                        "quote_products_info": [{"Heading": "Job Name", "AttributeValue": "Table Cards"}],
                        "products_prd_day": "0",
                        "products_weight": 0,
                        "quote_product_sku": None,
                        "quote_product_notes": None
                    }
                ]
            },
            {
                "quote_id": 1640,
                "user_id": 314,
                "quote_title": "Realty Sign",
                "quote_price": 109.11,
                "quote_vendor_price": 56.1752,
                "sort_order": 0,
                "quote_status": 4,
                "quote_date": "2025-12-19 11:28:26",
                "admin_notes": None,
                "quote_shipping_addr": 353,
                "quote_billing_addr": 353,
                "ship_amt": 0,
                "quote_tax_exampt": False,
                "quoteproduct": [
                    {
                        "isCustomProduct": 0,
                        "quote_products_id": 5403,
                        "quote_id": 1640,
                        "products_id": 202,
                        "products_title": "e_202",
                        "quote_products_quantity": 1,
                        "quote_products_price": 74.11,
                        "quote_products_vendor_price": 21.1752,
                        "quote_products_info": [{"Heading": "Job Name", "AttributeValue": "Realty Sign"}],
                        "products_prd_day": "4",
                        "products_weight": 4.6224,
                        "quote_product_sku": None,
                        "quote_product_notes": None
                    },
                    {
                        "isCustomProduct": 0,
                        "quote_products_id": 5404,
                        "quote_id": 1640,
                        "products_id": 214,
                        "products_title": "e_214",
                        "quote_products_quantity": 1,
                        "quote_products_price": 35,
                        "quote_products_vendor_price": 35,
                        "quote_products_info": [{"Heading": "Job Name", "AttributeValue": "None"}],
                        "products_prd_day": "6",
                        "products_weight": 0,
                        "quote_product_sku": None,
                        "quote_product_notes": None
                    }
                ]
            }
        ],
        "totalQuote": 2
    }
}


def sync_quotes():
    """Sync embedded quote data to Frappe OPS Quote DocType"""

    quotes = QUOTES_DATA['get_quote']['quote']
    print(f"Syncing {len(quotes)} quotes...")

    for quote_data in quotes:
        quote_id = quote_data.get('quote_id')
        print(f"\n=== Syncing Quote ID: {quote_id} ===")
        print(f"  Title: {quote_data.get('quote_title')}")
        print(f"  Price: ${quote_data.get('quote_price')}")
        print(f"  Vendor Price: ${quote_data.get('quote_vendor_price')}")
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

            # Sync data using the sync_from_onprintshop method
            doc.sync_from_onprintshop(quote_data)
            doc.save(ignore_permissions=True)

            print(f"  SUCCESS: Quote {quote_id} synced!")
            print(f"    - Status: {doc.quote_status}")
            print(f"    - Quote Price: ${doc.quote_price}")
            print(f"    - Vendor Price: ${doc.quote_vendor_price}")
            print(f"    - Subtotal: ${doc.subtotal}")
            print(f"    - Total Amount: ${doc.total_amount}")
            print(f"    - Profit Margin: ${doc.profit_margin}")
            print(f"    - Profit %: {doc.profit_percentage}%")
            print(f"    - Products synced: {len(doc.quote_products or [])}")

            # Print product details
            for i, product in enumerate(doc.quote_products or [], 1):
                print(f"      Product {i}: {product.products_title} - ${product.quote_products_price} x {product.quote_products_quantity}")

        except Exception as e:
            print(f"  ERROR syncing quote {quote_id}: {str(e)}")
            import traceback
            traceback.print_exc()

    frappe.db.commit()
    print("\n=== Sync Complete ===")


if __name__ == "__main__":
    sync_quotes()
