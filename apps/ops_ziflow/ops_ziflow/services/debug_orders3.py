"""Debug orders API call - with date range."""

import frappe

@frappe.whitelist()
def debug_orders():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from datetime import datetime, timedelta

    client = OnPrintShopClient()

    # Calculate date range
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    query = """
        query($limit: Int, $from_date: String, $to_date: String) {
            orders(limit: $limit, from_date: $from_date, to_date: $to_date) {
                orders {
                    orders_id
                    order_status
                    order_name
                    total_amount
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

    try:
        result = client._execute_graphql(query, variables)
        return {
            'success': True,
            'from_date': from_date,
            'to_date': to_date,
            'raw_result': result
        }
    except Exception as e:
        import traceback
        return {
            'success': False,
            'from_date': from_date,
            'to_date': to_date,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
