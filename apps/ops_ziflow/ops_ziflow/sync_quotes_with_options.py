# sync_quotes_with_options.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.sync_quotes_with_options.sync_quotes

import frappe
import json

# Full quote data from OnPrintShop API with all options
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
                        "products_title": "Coroplast Signs",
                        "quote_products_quantity": 1,
                        "quote_products_price": 1247.52,
                        "quote_products_vendor_price": 356.434086,
                        "quote_products_info": [
                            {"optionId": 0, "Heading": "Job Name", "AttributeValue": "Coroplast Signs", "attributeId": ""},
                            {"optionId": "", "Heading": "Product Sizes", "AttributeValue": "<b>24</b> Width x <b>36</b> Height <span class=\"text-danger\"> (Inch)</span>", "attributeId": ""},
                            {"optionId": 6525, "Heading": "Substrate Class", "AttributeValue": "Sheet", "attributeId": "11449"},
                            {"optionId": 2235, "Heading": "Print Sides", "AttributeValue": "Double", "attributeId": "6892"},
                            {"optionId": 2239, "Heading": "Ink Type", "AttributeValue": "CMYK", "attributeId": "3150"},
                            {"optionId": 4476, "Heading": "Print Surface", "AttributeValue": "1st", "attributeId": "8015"},
                            {"optionId": 2245, "Heading": "Ink Finish", "AttributeValue": "Gloss", "attributeId": "3160"},
                            {"optionId": 2242, "Heading": "Ink Tech", "AttributeValue": "Vanguard VK300D-HS", "attributeId": "3177"},
                            {"optionId": 4477, "Heading": "Print Mode", "AttributeValue": "4-Pass", "attributeId": "8896"},
                            {"optionId": 2250, "Heading": "Substrate", "AttributeValue": "Coroplast 4mm - White", "attributeId": "3523"},
                            {"optionId": 4082, "Heading": "Sheet Size", "AttributeValue": "4' x 8'", "attributeId": "7093"},
                            {"optionId": 2253, "Heading": "Sign Type", "AttributeValue": "Standard", "attributeId": "3174"},
                            {"optionId": 2251, "Heading": "Cut Type", "AttributeValue": "Through Cut", "attributeId": "3171"},
                            {"optionId": 2241, "Heading": "Graphic Shape", "AttributeValue": "Rectangle", "attributeId": "3152"},
                            {"optionId": 2237, "Heading": "Corner Radius", "AttributeValue": "None", "attributeId": "3143"},
                            {"optionId": 2232, "Heading": "Production Time", "AttributeValue": "RUSH (1 Day)", "attributeId": "3134"},
                            {"optionId": 2575, "Heading": "Proof", "AttributeValue": "Digital Proof", "attributeId": "3990"}
                        ],
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
                        "quote_products_info": [
                            {"optionId": 0, "Heading": "Job Name", "AttributeValue": "Menu Cards", "attributeId": ""},
                            {"optionId": "", "Heading": "Product Sizes", "AttributeValue": "3.5\" x 8.5\"", "attributeId": 0}
                        ],
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
                        "quote_products_info": [
                            {"optionId": 0, "Heading": "Job Name", "AttributeValue": "Table Cards", "attributeId": ""},
                            {"optionId": "", "Heading": "Product Sizes", "AttributeValue": "11\" x 8.5\"", "attributeId": 0}
                        ],
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
                        "products_title": "ACP Sign",
                        "quote_products_quantity": 1,
                        "quote_products_price": 74.11,
                        "quote_products_vendor_price": 21.1752,
                        "quote_products_info": [
                            {"optionId": 0, "Heading": "Job Name", "AttributeValue": "Realty Sign", "attributeId": ""},
                            {"optionId": "", "Heading": "Product Sizes", "AttributeValue": "<b>24</b> Width x <b>36</b> Height <span class=\"text-danger\"> (Inch)</span>", "attributeId": ""},
                            {"optionId": 6519, "Heading": "Substrate Class", "AttributeValue": "Sheet", "attributeId": "11443"},
                            {"optionId": 2258, "Heading": "Print Sides", "AttributeValue": "Double", "attributeId": "6887"},
                            {"optionId": 2261, "Heading": "Ink Type", "AttributeValue": "CMYK", "attributeId": "3193"},
                            {"optionId": 2267, "Heading": "Ink Finish", "AttributeValue": "Gloss", "attributeId": "3203"},
                            {"optionId": 2269, "Heading": "Substrate", "AttributeValue": "ACP 3mm - White", "attributeId": "3526"},
                            {"optionId": 4064, "Heading": "Sheet Size", "AttributeValue": "4' x 8'", "attributeId": "7072"},
                            {"optionId": 2272, "Heading": "Cut Type", "AttributeValue": "Through Cut", "attributeId": "10858"},
                            {"optionId": 2352, "Heading": "Drill Holes / Grommets", "AttributeValue": "Yes", "attributeId": "3448"},
                            {"optionId": 2300, "Heading": "Placement", "AttributeValue": "Realty Spaced", "attributeId": "3273"},
                            {"optionId": 2571, "Heading": "Proof", "AttributeValue": "Digital Proof", "attributeId": "3982"},
                            {"optionId": 2255, "Heading": "Production Time", "AttributeValue": "Standard", "attributeId": "3181"},
                            {"optionId": 2275, "Heading": "Sign Type", "AttributeValue": "Realty Signs", "attributeId": "6185"}
                        ],
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
                        "products_title": "Installation",
                        "quote_products_quantity": 1,
                        "quote_products_price": 35,
                        "quote_products_vendor_price": 35,
                        "quote_products_info": [
                            {"optionId": 0, "Heading": "Job Name", "AttributeValue": "None", "attributeId": ""},
                            {"optionId": "", "Heading": "Product Sizes", "AttributeValue": "None", "attributeId": "226"}
                        ],
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
    """Sync quotes with full product options"""

    quotes = QUOTES_DATA['get_quote']['quote']
    print(f"Syncing {len(quotes)} quotes with product options...")

    for quote_data in quotes:
        quote_id = quote_data.get('quote_id')
        print(f"\n=== Syncing Quote ID: {quote_id} ===")
        print(f"  Title: {quote_data.get('quote_title')}")

        try:
            # Delete existing quote to resync with options
            if frappe.db.exists('OPS Quote', {'quote_id': quote_id}):
                frappe.delete_doc('OPS Quote', str(quote_id), ignore_permissions=True)
                print(f"  Deleted existing quote for resync")

            # Create new quote
            doc = frappe.new_doc('OPS Quote')
            doc.quote_id = quote_id
            doc.sync_from_onprintshop(quote_data)
            doc.save(ignore_permissions=True)

            print(f"  SUCCESS: Quote {quote_id} synced!")
            print(f"    - Products: {len(doc.quote_products or [])}")
            print(f"    - Product Options: {len(doc.quote_product_options or [])}")

            # Show options breakdown by product
            for product in doc.quote_products or []:
                product_options = [o for o in (doc.quote_product_options or [])
                                   if o.quote_products_id == product.quote_products_id]
                print(f"      {product.products_title}: {len(product_options)} options")

        except Exception as e:
            print(f"  ERROR syncing quote {quote_id}: {str(e)}")
            import traceback
            traceback.print_exc()

    frappe.db.commit()
    print("\n=== Sync Complete ===")


if __name__ == "__main__":
    sync_quotes()
