"""Compare queries directly."""

import frappe

@frappe.whitelist()
def compare_queries():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from datetime import datetime, timedelta

    client = OnPrintShopClient()

    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # Simple query that works
    simple_query = """
        query($limit: Int, $from_date: String, $to_date: String) {
            orders(limit: $limit, from_date: $from_date, to_date: $to_date) {
                orders {
                    orders_id
                    order_status
                    order_name
                }
                totalOrders
            }
        }
    """

    simple_vars = {
        "limit": 5,
        "from_date": from_date,
        "to_date": to_date
    }

    # The full query from get_orders
    full_query = """
            query($limit: Int, $offset: Int, $order_status: String, $from_date: String, $to_date: String) {
                orders(limit: $limit, offset: $offset, order_status: $order_status, from_date: $from_date, to_date: $to_date) {
                    orders {
                        orders_id
                        order_status
                        orders_status_id
                        order_name
                        total_amount
                        order_amount
                        shipping_amount
                        tax_amount
                        coupon_amount
                        payment_method_name
                        customer {
                            customers_id
                            customers_name
                            customers_email_address
                            customers_telephone
                        }
                        delivery_detail {
                            delivery_name
                            delivery_company
                            delivery_street_address
                            delivery_suburb
                            delivery_city
                            delivery_state
                            delivery_postcode
                            delivery_country
                        }
                        billing_detail {
                            billing_name
                            billing_street_address
                            billing_suburb
                            billing_city
                            billing_state
                            billing_postcode
                            billing_country
                        }
                    }
                    totalOrders
                }
            }
        """

    full_vars = {
        "limit": 5,
        "offset": 0,
        "order_status": None,
        "from_date": from_date,
        "to_date": to_date
    }

    simple_result = client._execute_graphql(simple_query, simple_vars)
    full_result = client._execute_graphql(full_query, full_vars)

    return {
        'simple_result': simple_result,
        'full_result': full_result
    }
