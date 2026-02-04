"""OnPrintShop GraphQL API Client for quote and order synchronization."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import frappe
import requests


class OnPrintShopClient:
    """GraphQL client for OnPrintShop API with OAuth2 authentication."""

    def __init__(self, settings: Optional[Dict] = None):
        """Initialize with settings from OPS API Settings, OPS ZiFlow Settings, or provided dict."""
        if settings is None:
            settings = self._load_settings()

        self.base_url = settings.get("ops_api_url", "https://visualgraphx.com")
        self.graphql_url = settings.get("ops_graphql_url")  # Direct GraphQL URL if available
        self.client_id = settings.get("ops_client_id")
        self.client_secret = settings.get("ops_client_secret")
        self._token = None

    def _load_settings(self) -> Dict:
        """Load settings from OPS API Settings, OPS ZiFlow Settings, or defaults."""
        # First try OPS API Settings (used by ops_api.py)
        if frappe.db.exists("DocType", "OPS API Settings"):
            try:
                settings = frappe.get_doc("OPS API Settings")
                if getattr(settings, "enabled", False) and getattr(settings, "api_url", None):
                    return {
                        "ops_api_url": settings.api_url.rstrip('/').replace('/graphql', '').replace('/api', ''),
                        "ops_graphql_url": settings.api_url,
                        "ops_client_id": getattr(settings, "client_id", None),
                        "ops_client_secret": settings.get_password("client_secret") if hasattr(settings, "get_password") else getattr(settings, "client_secret", None),
                    }
            except Exception:
                pass

        # Try OPS ZiFlow Settings as fallback
        if frappe.db.exists("DocType", "OPS ZiFlow Settings"):
            try:
                settings = frappe.get_single("OPS ZiFlow Settings")
                return {
                    "ops_api_url": getattr(settings, "ops_api_url", None) or "https://visualgraphx.com",
                    "ops_client_id": getattr(settings, "ops_client_id", None),
                    "ops_client_secret": getattr(settings, "ops_client_secret", None),
                }
            except Exception:
                pass

        # Fallback to hardcoded values (from original scripts)
        return {
            "ops_api_url": "https://visualgraphx.com",
            "ops_client_id": "2190fd7c-596b-11ef-9e9f-06bd824fb541",
            "ops_client_secret": "1e7e95c890e62551b190bed822a39bef676b4d36c34a8a98ba4e092b6c6a0cb3",
        }

    def get_token(self) -> str:
        """Get OAuth2 access token using client_credentials flow."""
        if self._token:
            return self._token

        # Try to use cached token from OPS API Settings
        try:
            if frappe.db.exists("DocType", "OPS API Settings"):
                from datetime import datetime
                settings = frappe.get_doc("OPS API Settings")
                if settings.access_token and settings.token_expires:
                    # Parse expiry date
                    if isinstance(settings.token_expires, str):
                        try:
                            expires = datetime.strptime(settings.token_expires, "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            expires = datetime.strptime(settings.token_expires, "%Y-%m-%d %H:%M:%S")
                    else:
                        expires = settings.token_expires

                    # Use cached token if not expired (with 5 min buffer)
                    from datetime import timedelta
                    if expires > datetime.now() + timedelta(minutes=5):
                        self._token = settings.access_token
                        return self._token
        except Exception:
            pass

        # Fall back to getting new token
        token_url = f"{self.base_url}/api/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(token_url, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "access_token" not in data:
            raise Exception(f"No access token in response: {data}")

        self._token = data["access_token"]
        return self._token

    def _execute_graphql(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query/mutation."""
        token = self.get_token()
        # Use direct graphql_url if available, otherwise construct from base_url
        api_url = self.graphql_url if self.graphql_url else f"{self.base_url}/api/"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        return response.json()

    def get_quotes(self, limit: int = 50, offset: int = 0, quote_id: Optional[int] = None) -> Dict:
        """Fetch quotes from OnPrintShop API.

        Args:
            limit: Maximum number of quotes to fetch
            offset: Offset for pagination
            quote_id: Optional specific quote ID to fetch

        Returns:
            Dict with 'quote' list and 'totalQuote' count
        """
        query = """
            query get_quote($quote_id: Int, $user_id: Int, $limit: Int, $offset: Int) {
                get_quote(quote_id: $quote_id, user_id: $user_id, limit: $limit, offset: $offset) {
                    quote {
                        quote_id user_id quote_title quote_price quote_vendor_price sort_order quote_status
                        quote_date admin_notes quote_shipping_addr quote_billing_addr ship_amt quote_tax_exampt
                        quoteproduct {
                            isCustomProduct quote_products_id quote_id products_id products_title
                            quote_products_quantity quote_products_price quote_products_vendor_price
                            quote_products_info products_prd_day products_weight quote_product_sku quote_product_notes
                        }
                    }
                    totalQuote
                }
            }
        """

        variables = {
            "quote_id": quote_id,
            "user_id": None,
            "limit": limit,
            "offset": offset,
        }

        result = self._execute_graphql(query, variables)

        # Log errors but don't fail - some quotes may have invalid data
        if result.get("errors"):
            import frappe
            frappe.logger().warning(f"GraphQL warnings while fetching quotes: {len(result['errors'])} errors at offset {offset}")

        # Return data even if there were some errors (partial results)
        data = result.get("data", {}).get("get_quote", {"quote": [], "totalQuote": 0})
        if data is None:
            return {"quote": [], "totalQuote": 0}
        return data

    def get_all_quotes(self, batch_size: int = 50) -> List[Dict]:
        """Fetch all quotes with pagination.

        Args:
            batch_size: Number of quotes per API call

        Returns:
            List of all quote dictionaries
        """
        all_quotes = []
        offset = 0
        consecutive_errors = 0
        max_errors = 5

        while True:
            try:
                result = self.get_quotes(limit=batch_size, offset=offset)
                quotes = result.get("quote", [])

                if not quotes:
                    break

                all_quotes.extend(quotes)
                consecutive_errors = 0

                if len(quotes) < batch_size:
                    break

                offset += batch_size

            except Exception as e:
                consecutive_errors += 1
                frappe.log_error(f"Error fetching quotes at offset {offset}: {e}", "OnPrintShop Quote Sync")

                if consecutive_errors >= max_errors:
                    break

                offset += batch_size

        return all_quotes

    def update_quote(
        self,
        quote_id: int,
        user_id: int,
        quote_title: str,
        products: Optional[List[Dict]] = None,
        shipping_type: Optional[str] = None,
    ) -> Dict:
        """Update a quote in OnPrintShop via setQuote mutation.

        Args:
            quote_id: The quote ID to update
            user_id: The user ID owning the quote
            quote_title: Title of the quote
            products: Optional list of product data
            shipping_type: Optional shipping type

        Returns:
            Dict with result, message, and quote_id
        """
        mutation = """
            mutation setQuote($userid: Int!, $quote_id: Int, $selectedShippingType: String, $quote_title: String!, $input: SetQuoteInput!) {
                setQuote(userid: $userid, quote_title: $quote_title, selectedShippingType: $selectedShippingType, quote_id: $quote_id, input: $input) {
                    result
                    message
                    quote_id
                }
            }
        """

        variables = {
            "userid": int(user_id),
            "quote_id": int(quote_id),
            "quote_title": quote_title,
            "input": {
                "productsArr": products or []
            }
        }

        if shipping_type:
            variables["selectedShippingType"] = shipping_type

        result = self._execute_graphql(mutation, variables)

        if result.get("errors"):
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result.get("data", {}).get("setQuote", {})

    def create_quote(
        self,
        user_id: int,
        quote_title: str,
        products: Optional[List[Dict]] = None,
        shipping_type: Optional[str] = None,
    ) -> Dict:
        """Create a new quote in OnPrintShop.

        Args:
            user_id: The user ID owning the quote
            quote_title: Title of the quote
            products: Optional list of product data
            shipping_type: Optional shipping type

        Returns:
            Dict with result, message, and quote_id
        """
        # quote_id = 0 means create new
        return self.update_quote(
            quote_id=0,
            user_id=user_id,
            quote_title=quote_title,
            products=products,
            shipping_type=shipping_type,
        )

    # =========================================================================
    # ORDER METHODS - Updated with ALL fields
    # =========================================================================

    # Full GraphQL query for orders with ALL available fields
    ORDER_QUERY_FIELDS = """
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
        shipping_mode
        courirer_company_name
        airway_bill_number
        shipping_type_id
        customer {
            customers_name
            customers_company
            customers_email_address
            customers_telephone
            customers_first_name
            customers_last_name
        }
        delivery_detail {
            delivery_name
            delivery_company
            delivery_street_address
            delivery_suburb
            delivery_city
            delivery_postcode
            delivery_state
            delivery_state_code
            delivery_country
            delivery_telephone
        }
        billing_detail {
            billing_name
            billing_company
            billing_street_address
            billing_suburb
            billing_city
            billing_postcode
            billing_state
            billing_state_code
            billing_country
            billing_telephone
        }
        shipment_detail {
            shipment_tracking_number
            shipment_company
            shipment_shipping_type_id
            shipment_total_weight
        }
        product {
            orders_products_id
            product_id
            products_name
            products_title
            products_sku
            products_quantity
            products_price
            products_unit_price
            products_vendor_price
            products_weight
            product_status
            product_status_id
            product_production_due_date
            productsize
            ziflow_link
            features_details
            product_size_details
            template_type
            template_info
            product_info
            quote_id
            reprint
            original_order_id
            original_line_id
        }
    """

    def get_orders(
        self,
        limit: int = 50,
        offset: int = 0,
        order_status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict:
        """Fetch orders from OnPrintShop API with ALL fields.

        Args:
            limit: Maximum number of orders to fetch
            offset: Offset for pagination
            order_status: Optional status filter
            from_date: Optional start date filter (YYYY-MM-DD). Required if no to_date.
            to_date: Optional end date filter (YYYY-MM-DD). Required if no from_date.

        Returns:
            Dict with 'orders' list and 'totalOrders' count
        """
        # API requires either orders_id or date range
        # Default to last 365 days if no dates provided
        if not from_date and not to_date:
            from datetime import datetime, timedelta
            to_date = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        query = f"""
            query($limit: Int, $offset: Int, $order_status: String, $from_date: String, $to_date: String) {{
                orders(limit: $limit, offset: $offset, order_status: $order_status, from_date: $from_date, to_date: $to_date) {{
                    orders {{
                        {self.ORDER_QUERY_FIELDS}
                    }}
                    totalOrders
                }}
            }}
        """

        variables = {
            "limit": limit,
            "offset": offset,
            "order_status": order_status,
            "from_date": from_date,
            "to_date": to_date,
        }

        result = self._execute_graphql(query, variables)

        # Log errors but don't fail
        if result.get("errors"):
            import frappe
            frappe.logger().warning(f"GraphQL warnings while fetching orders: {len(result['errors'])} errors at offset {offset}")

        data = result.get("data", {}).get("orders", {"orders": [], "totalOrders": 0})
        if data is None:
            return {"orders": [], "totalOrders": 0}
        return data

    def get_order(self, order_id: int) -> Optional[Dict]:
        """Fetch single order with full details from OnPrintShop.

        Args:
            order_id: The OPS order ID

        Returns:
            Dict with full order details or None
        """
        query = f"""
            query($orders_id: Int!) {{
                orders(orders_id: $orders_id, limit: 1) {{
                    orders {{
                        {self.ORDER_QUERY_FIELDS}
                    }}
                }}
            }}
        """

        variables = {"orders_id": int(order_id)}

        result = self._execute_graphql(query, variables)

        if result.get("errors"):
            import frappe
            frappe.log_error(f"GraphQL errors fetching order {order_id}: {result['errors']}", "OnPrintShop Order Fetch")
            return None

        orders = result.get("data", {}).get("orders", {}).get("orders", [])
        return orders[0] if orders else None

    def get_all_orders(self, batch_size: int = 50) -> List[Dict]:
        """Fetch all orders with pagination.

        Args:
            batch_size: Number of orders per API call

        Returns:
            List of all order dictionaries
        """
        all_orders = []
        offset = 0
        consecutive_errors = 0
        max_errors = 5

        while True:
            try:
                result = self.get_orders(limit=batch_size, offset=offset)
                orders = result.get("orders", [])

                if not orders:
                    break

                all_orders.extend(orders)
                consecutive_errors = 0

                if len(orders) < batch_size:
                    break

                offset += batch_size

            except Exception as e:
                consecutive_errors += 1
                frappe.log_error(f"Error fetching orders at offset {offset}: {e}", "OnPrintShop Order Sync")

                if consecutive_errors >= max_errors:
                    break

                offset += batch_size

        return all_orders

    # Status ID to name mapping for OPS
    OPS_STATUS_NAMES = {
        1: "New Order",
        2: "Order Confirmed",
        3: "Awaiting Approval",
        4: "Awaiting Payment",
        5: "Payment Received",
        6: "In Prepress",
        7: "In Production",
        8: "Ready for Fulfillment",
        9: "Partially Shipped",
        10: "Shipped",
        11: "Delivered",
        12: "On Hold",
        13: "Cancelled",
        14: "Fulfilled",
        15: "Refunded",
        16: "Order Completed",
        26: "Order Completed",  # Alternate ID
    }

    def update_order_status(
        self,
        order_id: int,
        status_id: int = None,
        status_name: str = None,
        comment: str = None,
        notify: int = 0
    ) -> Dict:
        """Update order status in OnPrintShop.

        Args:
            order_id: The OPS order ID
            status_id: The status ID (will be converted to name)
            status_name: The status name (used directly if provided)
            comment: Optional comment for the status change
            notify: Whether to notify customer (0 or 1)

        Returns:
            Dict with result and message
        """
        # Convert status_id to name if not provided
        if not status_name and status_id:
            status_name = self.OPS_STATUS_NAMES.get(status_id, "New Order")

        mutation = """
            mutation updateOrderStatus($type: OrderStatusUpdateTypeEnum!, $orders_id: Int, $input: UpdateOrderStatusInput!) {
                updateOrderStatus(type: $type, orders_id: $orders_id, input: $input) {
                    result
                    message
                }
            }
        """

        variables = {
            "type": "order",
            "orders_id": int(order_id),
            "input": {
                "order_status": status_name,
            }
        }

        if comment:
            variables["input"]["comment"] = comment
        if notify:
            variables["input"]["notify"] = notify

        result = self._execute_graphql(mutation, variables)

        if result.get("errors"):
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result.get("data", {}).get("updateOrderStatus", {})

    def update_order_full(
        self,
        order_id: int,
        status_name: str = None,
        courier_company_name: str = None,
        tracking_number: str = None,
        comment: str = None,
        notify: int = 0
    ) -> Dict:
        """Update order with all supported fields in OnPrintShop.

        Args:
            order_id: The OPS order ID
            status_name: The status name
            courier_company_name: Shipping carrier name
            tracking_number: Shipment tracking number
            comment: Optional comment
            notify: Whether to notify customer (0 or 1)

        Returns:
            Dict with result and message
        """
        mutation = """
            mutation updateOrderStatus($type: OrderStatusUpdateTypeEnum!, $orders_id: Int, $input: UpdateOrderStatusInput!) {
                updateOrderStatus(type: $type, orders_id: $orders_id, input: $input) {
                    result
                    message
                }
            }
        """

        input_data = {}

        if status_name:
            input_data["order_status"] = status_name
        if courier_company_name:
            input_data["courier_company_name"] = courier_company_name
        if tracking_number:
            input_data["tracking_number"] = tracking_number
        if comment:
            input_data["comment"] = comment
        if notify:
            input_data["notify"] = notify

        # Need at least one field to update
        if not input_data:
            return {"result": False, "message": "No fields to update"}

        variables = {
            "type": "order",
            "orders_id": int(order_id),
            "input": input_data
        }

        result = self._execute_graphql(mutation, variables)

        if result.get("errors"):
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result.get("data", {}).get("updateOrderStatus", {})

    def set_shipment(
        self,
        order_id: int,
        tracking_number: str = None,
        shipment_id: int = None,
        shipment_info: Dict = None
    ) -> Dict:
        """Set/update shipment information for an order.

        Args:
            order_id: The OPS order ID
            tracking_number: Tracking number
            shipment_id: Existing shipment ID to update (optional)
            shipment_info: Additional shipment info as JSON

        Returns:
            Dict with result
        """
        mutation = """
            mutation setShipment($order_id: Int, $shipment_id: Int, $tracking_number: String, $shipmentinfo: JSON) {
                setShipment(order_id: $order_id, shipment_id: $shipment_id, tracking_number: $tracking_number, shipmentinfo: $shipmentinfo) {
                    result
                    message
                    shipment_id
                }
            }
        """

        variables = {
            "order_id": int(order_id),
        }

        if tracking_number:
            variables["tracking_number"] = tracking_number
        if shipment_id:
            variables["shipment_id"] = int(shipment_id)
        if shipment_info:
            variables["shipmentinfo"] = shipment_info

        result = self._execute_graphql(mutation, variables)

        if result.get("errors"):
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result.get("data", {}).get("setShipment", {})

    def update_product_status(
        self,
        orders_products_id: int,
        status_name: str,
        comment: str = None,
        notify: int = 0
    ) -> Dict:
        """Update product line status in OnPrintShop.

        Args:
            orders_products_id: The order product line ID
            status_name: The product status name
            comment: Optional comment
            notify: Whether to notify customer

        Returns:
            Dict with result and message
        """
        mutation = """
            mutation updateOrderStatus($type: OrderStatusUpdateTypeEnum!, $orders_products_id: Int, $input: UpdateOrderStatusInput!) {
                updateOrderStatus(type: $type, orders_products_id: $orders_products_id, input: $input) {
                    result
                    message
                }
            }
        """

        input_data = {
            "order_product_status": status_name
        }

        if comment:
            input_data["comment"] = comment
        if notify:
            input_data["notify"] = notify

        variables = {
            "type": "product",
            "orders_products_id": int(orders_products_id),
            "input": input_data
        }

        result = self._execute_graphql(mutation, variables)

        if result.get("errors"):
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result.get("data", {}).get("updateOrderStatus", {})
