"""Debug get_orders method."""

import frappe

@frappe.whitelist()
def debug_get_orders():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from datetime import datetime, timedelta

    client = OnPrintShopClient()

    # Check the module's datetime inside get_orders
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # Direct query test
    query = """
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
                        userid
                        customers_name
                        customers_email_address
                        customers_telephone
                    }
                }
                totalOrders
            }
        }
    """

    variables = {
        "limit": 5,
        "offset": 0,
        "order_status": None,
        "from_date": from_date,
        "to_date": to_date,
    }

    direct_result = client._execute_graphql(query, variables)

    return {
        'dates': {'from': from_date, 'to': to_date},
        'direct_result': direct_result,
        'get_orders_result': client.get_orders(limit=5)
    }
