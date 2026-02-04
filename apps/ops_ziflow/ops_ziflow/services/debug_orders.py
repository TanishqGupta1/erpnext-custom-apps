"""Debug orders API call."""

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

    # Try a minimal query
    query = """
        query($limit: Int) {
            orders(limit: $limit) {
                orders {
                    orders_id
                    orders_status
                    customers_name
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
        return {
            'success': False,
            'settings': settings_info,
            'error': str(e)
        }
