"""Debug poll function - detailed."""

import frappe

@frappe.whitelist()
def debug_poll():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from datetime import datetime, timedelta

    client = OnPrintShopClient()

    # Manually calculate date range
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    query = """
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

    variables = {
        "limit": 5,
        "from_date": from_date,
        "to_date": to_date
    }

    # Direct GraphQL call
    raw_result = client._execute_graphql(query, variables)

    # Now via get_orders
    get_orders_result = client.get_orders(limit=5)

    return {
        'from_date': from_date,
        'to_date': to_date,
        'direct_raw': raw_result,
        'get_orders_result': get_orders_result,
    }
