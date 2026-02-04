"""Test fetching full order with all nested fields."""

import frappe
import time

@frappe.whitelist()
def test_full_order():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from datetime import datetime, timedelta

    # Wait to avoid rate limiting
    time.sleep(3)

    client = OnPrintShopClient()

    # Calculate date range
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # Query with all nested objects
    query = """
        query($limit: Int, $from_date: String, $to_date: String) {
            orders(limit: $limit, from_date: $from_date, to_date: $to_date) {
                orders {
                    orders_id
                    order_status
                    orders_status_id
                    order_name
                    user_id
                    corporate_id
                    total_amount
                    order_amount
                    shipping_amount
                    tax_amount
                    coupon_amount
                    coupon_code
                    coupon_type
                    order_vendor_amount
                    orders_due_date
                    orders_date_finished
                    local_orders_date_finished
                    order_last_modified_date
                    po_number
                    total_weight
                    refund_amount
                    payment_due_date
                    transactionid
                    sales_agent_name
                    payment_status_title
                    production_due_date
                    payment_date
                    invoice_number
                    invoice_date
                    payment_processing_fees
                    payment_method_name
                    customer {
                        customers_name
                        customers_company
                        customers_email_address
                        customers_telephone
                    }
                    delivery_detail {
                        delivery_name
                        delivery_company
                        delivery_street_address
                        delivery_suburb
                        delivery_city
                        delivery_postcode
                        delivery_state
                        delivery_country
                    }
                    billing_detail {
                        billing_name
                        billing_street_address
                        billing_suburb
                        billing_city
                        billing_postcode
                        billing_state
                        billing_country
                    }
                    product {
                        orders_products_id
                        product_id
                        products_name
                        products_title
                        products_quantity
                        products_price
                        products_unit_price
                        product_status
                        product_status_id
                    }
                }
                totalOrders
            }
        }
    """

    variables = {
        "limit": 1,
        "from_date": from_date,
        "to_date": to_date
    }

    try:
        result = client._execute_graphql(query, variables)
        return result
    except Exception as e:
        import traceback
        return {'error': str(e), 'traceback': traceback.format_exc()}
