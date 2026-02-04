import frappe
import requests
import json

def resync_all_direct():
    """Re-sync ALL orders using direct API calls"""
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from ops_ziflow.services.order_sync_service import sync_order_from_onprintshop
    
    client = OnPrintShopClient()
    
    # Get fresh token
    token_url = f"{client.base_url}/api/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client.client_id,
        "client_secret": client.client_secret,
    }
    resp = requests.post(token_url, json=payload, timeout=30)
    token = resp.json().get("access_token")
    
    api_url = client.graphql_url if client.graphql_url else f"{client.base_url}/api/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    
    stats = {"synced": 0, "errors": 0, "total_options": 0}
    offset = 0
    batch_size = 50
    
    while True:
        query = {
            "query": f"""
                query {{
                    orders(from_date: "2020-01-01", to_date: "2025-12-31", limit: {batch_size}, offset: {offset}) {{
                        orders {{
                            {client.ORDER_QUERY_FIELDS}
                        }}
                        totalOrders
                    }}
                }}
            """
        }
        
        resp = requests.post(api_url, json=query, headers=headers, timeout=60)
        result = resp.json()
        
        orders = result.get("data", {}).get("orders", {}).get("orders", [])
        total = result.get("data", {}).get("orders", {}).get("totalOrders", 0)
        
        if not orders:
            print(f"No more orders at offset {offset}")
            break
        
        print(f"Batch: offset={offset}, fetched={len(orders)}, total={total}")
        
        for order_data in orders:
            orders_id = order_data.get("orders_id")
            try:
                doc = sync_order_from_onprintshop(orders_id, order_data)
                if doc:
                    stats["synced"] += 1
                    stats["total_options"] += len(doc.order_product_options) if doc.order_product_options else 0
            except Exception as e:
                stats["errors"] += 1
        
        frappe.db.commit()
        
        if len(orders) < batch_size:
            break
        
        offset += batch_size
    
    print(f"Complete: {stats}")
    return stats
