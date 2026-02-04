"""Debug orders API call - check raw response."""

import frappe

@frappe.whitelist()
def debug_orders():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    import json

    client = OnPrintShopClient()

    # Debug: Print settings being used
    settings_info = {
        'base_url': client.base_url,
        'graphql_url': client.graphql_url,
        'client_id': client.client_id[:20] + '...' if client.client_id else None,
    }

    # Try a minimal query with the correct field names
    query = """
        query($limit: Int) {
            orders(limit: $limit) {
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

    variables = {"limit": 5}

    try:
        result = client._execute_graphql(query, variables)
        return {
            'success': True,
            'settings': settings_info,
            'raw_result': result
        }
    except Exception as e:
        import traceback
        return {
            'success': False,
            'settings': settings_info,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
