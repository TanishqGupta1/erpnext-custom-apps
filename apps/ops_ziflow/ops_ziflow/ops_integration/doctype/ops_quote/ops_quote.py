# Copyright (c) 2024, Visual Graphx and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, flt
import json


class OPSQuote(Document):
    def before_save(self):
        """Calculate totals before saving"""
        self.calculate_totals()
        self.calculate_profit()

    def calculate_totals(self):
        """Calculate quote totals from products"""
        subtotal = 0
        vendor_total = 0

        if self.quote_products:
            for product in self.quote_products:
                qty = flt(product.quote_products_quantity) or 1
                price = flt(product.quote_products_price) or 0
                vendor_price = flt(product.quote_products_vendor_price) or 0

                # Calculate line totals
                product.final_price = qty * price
                product.vendor_total = qty * vendor_price

                subtotal += product.final_price
                vendor_total += product.vendor_total

        self.subtotal = subtotal

        # Calculate total amount
        quote_price = flt(self.quote_price) or subtotal
        ship_amt = flt(self.ship_amt) or 0
        tax_amt = flt(self.tax_amt) or 0

        self.total_amount = quote_price + ship_amt + tax_amt

        # Update vendor price total if not set
        if not self.quote_vendor_price:
            self.quote_vendor_price = vendor_total

    def calculate_profit(self):
        """Calculate profit margin and percentage"""
        quote_price = flt(self.quote_price) or 0
        vendor_price = flt(self.quote_vendor_price) or 0

        self.profit_margin = quote_price - vendor_price

        if quote_price > 0:
            self.profit_percentage = (self.profit_margin / quote_price) * 100
        else:
            self.profit_percentage = 0

    def sync_from_onprintshop(self, quote_data):
        """Sync quote data from OnPrintShop API response"""
        # Update basic fields
        self.quote_title = quote_data.get('quote_title', self.quote_title)
        self.quote_status = self._map_status(quote_data.get('quote_status'))
        self.quote_date = quote_data.get('quote_date')
        self.user_id = quote_data.get('user_id')
        self.quote_price = flt(quote_data.get('quote_price'))
        self.quote_vendor_price = flt(quote_data.get('quote_vendor_price'))
        self.ship_amt = flt(quote_data.get('ship_amt'))
        self.quote_tax_exempt = quote_data.get('quote_tax_exampt') == 1
        self.admin_notes = quote_data.get('admin_notes')
        self.sort_order = quote_data.get('sort_order', 0)

        # Link to OPS Customer if user_id provided
        if self.user_id:
            customer = frappe.db.get_value('OPS Customer',
                {'userid': self.user_id}, 'name')
            if customer:
                self.ops_customer = customer

        # Parse and store shipping address
        shipping_addr = quote_data.get('quote_shipping_addr')
        if shipping_addr:
            if isinstance(shipping_addr, str):
                try:
                    shipping_addr = json.loads(shipping_addr)
                except:
                    pass
            if isinstance(shipping_addr, dict):
                self.shipping_name = shipping_addr.get('name') or shipping_addr.get('delivery_name')
                self.shipping_company = shipping_addr.get('company') or shipping_addr.get('delivery_company')
                self.shipping_street_address = shipping_addr.get('street_address') or shipping_addr.get('delivery_street_address')
                self.shipping_city = shipping_addr.get('city') or shipping_addr.get('delivery_city')
                self.shipping_state = shipping_addr.get('state') or shipping_addr.get('delivery_state')
                self.shipping_postcode = shipping_addr.get('postcode') or shipping_addr.get('delivery_postcode')
                self.shipping_country = shipping_addr.get('country') or shipping_addr.get('delivery_country')
                self.shipping_telephone = shipping_addr.get('telephone') or shipping_addr.get('delivery_telephone')
            self.raw_shipping_addr = json.dumps(shipping_addr) if isinstance(shipping_addr, dict) else shipping_addr

        # Parse and store billing address
        billing_addr = quote_data.get('quote_billing_addr')
        if billing_addr:
            if isinstance(billing_addr, str):
                try:
                    billing_addr = json.loads(billing_addr)
                except:
                    pass
            if isinstance(billing_addr, dict):
                self.billing_name = billing_addr.get('name') or billing_addr.get('billing_name')
                self.billing_company = billing_addr.get('company') or billing_addr.get('billing_company')
                self.billing_street_address = billing_addr.get('street_address') or billing_addr.get('billing_street_address')
                self.billing_city = billing_addr.get('city') or billing_addr.get('billing_city')
                self.billing_state = billing_addr.get('state') or billing_addr.get('billing_state')
                self.billing_postcode = billing_addr.get('postcode') or billing_addr.get('billing_postcode')
                self.billing_country = billing_addr.get('country') or billing_addr.get('billing_country')
                self.billing_telephone = billing_addr.get('telephone') or billing_addr.get('billing_telephone')
            self.raw_billing_addr = json.dumps(billing_addr) if isinstance(billing_addr, dict) else billing_addr

        # Sync products and their options
        if 'quoteproduct' in quote_data:
            self.quote_products = []
            self.quote_product_options = []  # Clear existing options

            for product in quote_data['quoteproduct']:
                quote_products_id = product.get('quote_products_id')
                products_title = product.get('products_title')

                product_row = {
                    'quote_products_id': quote_products_id,
                    'products_id': product.get('products_id'),
                    'products_title': products_title,
                    'products_name': product.get('products_name'),
                    'quote_product_sku': product.get('quote_product_sku'),
                    'quote_products_quantity': product.get('quote_products_quantity', 1),
                    'quote_products_price': flt(product.get('quote_products_price')),
                    'quote_products_vendor_price': flt(product.get('quote_products_vendor_price')),
                    'is_custom_product': product.get('isCustomProduct') == 1,
                    'products_prd_day': product.get('products_prd_day'),
                    'products_weight': flt(product.get('products_weight')),
                    'product_size_details': product.get('product_size_details'),
                    'features_details': product.get('features_details'),
                    'quote_product_notes': product.get('quote_product_notes'),
                }

                # Link to OPS Product if products_id provided
                if product.get('products_id'):
                    ops_product = frappe.db.get_value('OPS Product',
                        {'product_id': product.get('products_id')}, 'name')
                    if ops_product:
                        product_row['ops_product'] = ops_product

                # Store quote_products_info as JSON string
                product_info = product.get('quote_products_info')
                if product_info:
                    if isinstance(product_info, (dict, list)):
                        product_row['quote_products_info'] = json.dumps(product_info)
                    else:
                        product_row['quote_products_info'] = product_info

                    # Also sync options to the child table
                    options_list = product_info if isinstance(product_info, list) else [product_info]
                    for option in options_list:
                        if isinstance(option, dict) and option.get('Heading'):
                            option_row = {
                                'quote_products_id': quote_products_id,
                                'product_title': products_title,
                                'option_id': str(option.get('optionId', '')) if option.get('optionId') else '',
                                'attribute_id': str(option.get('attributeId', '')) if option.get('attributeId') else '',
                                'option_name': option.get('Heading', ''),
                                'option_value': option.get('AttributeValue', ''),
                            }
                            self.append('quote_product_options', option_row)

                self.append('quote_products', product_row)

        # Update sync status
        self.sync_status = 'Synced'
        self.last_synced = now_datetime()
        self.raw_payload = json.dumps(quote_data)

    def _map_status(self, ops_status):
        """Map OnPrintShop status to Frappe status"""
        if ops_status is None:
            return 'Draft'

        status_map = {
            '0': 'Draft',
            '1': 'Pending',
            '2': 'Sent',
            '3': 'Accepted',
            '4': 'Rejected',
            '5': 'Expired',
            '6': 'Converted',
            'draft': 'Draft',
            'pending': 'Pending',
            'sent': 'Sent',
            'accepted': 'Accepted',
            'rejected': 'Rejected',
            'expired': 'Expired',
            'converted': 'Converted'
        }
        return status_map.get(str(ops_status).lower(), 'Draft')


def sync_quote_from_onprintshop(quote_id, quote_data):
    """Create or update OPS Quote from OnPrintShop data"""
    if frappe.db.exists('OPS Quote', {'quote_id': quote_id}):
        doc = frappe.get_doc('OPS Quote', {'quote_id': quote_id})
    else:
        doc = frappe.new_doc('OPS Quote')
        doc.quote_id = quote_id

    doc.sync_from_onprintshop(quote_data)
    doc.save(ignore_permissions=True)
    return doc


@frappe.whitelist()
def get_quote_summary(quote_id):
    """Get quote summary for dashboard display"""
    quote = frappe.get_doc('OPS Quote', quote_id)
    return {
        'quote_id': quote.quote_id,
        'quote_title': quote.quote_title,
        'quote_status': quote.quote_status,
        'quote_date': quote.quote_date,
        'customer_name': quote.customer_name,
        'quote_price': quote.quote_price,
        'total_amount': quote.total_amount,
        'profit_margin': quote.profit_margin,
        'profit_percentage': quote.profit_percentage,
        'product_count': len(quote.quote_products or [])
    }
