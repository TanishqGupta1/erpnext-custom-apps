import frappe
from frappe.model.document import Document
import json

class OPSOrderViewSettings(Document):
    pass


@frappe.whitelist()
def get_view_settings():
    """Get Order View Settings for frontend"""
    settings = frappe.get_single("OPS Order View Settings")

    # If no cards configured, return defaults
    if not settings.cards or len(settings.cards) == 0:
        return get_default_settings()

    # Build response
    cards = []
    for card in sorted(settings.cards, key=lambda x: x.sort_order or 0):
        if not card.is_visible:
            continue

        fields = []
        for field in card.fields:
            if not field.is_visible:
                continue
            fields.append({
                "label": field.field_label,
                "field": field.source_field,
                "source": field.linked_doctype or "order",
                "type": field.field_type or "Text",
                "is_link": field.is_link,
                "link_template": field.link_template
            })

        cards.append({
            "id": card.card_name,
            "title": card.card_title,
            "icon": card.icon or "fa-file-text-o",
            "color": card.icon_color or "blue",
            "collapsible": card.is_collapsible,
            "fields": fields
        })

    return {
        "page_title": settings.page_title or "Order #{ops_order_id}",
        "show_breadcrumb": settings.show_breadcrumb,
        "cards_per_row": int(settings.cards_per_row or 3),
        "enable_product_inline_edit": settings.enable_product_inline_edit,
        "show_products_table": settings.show_products_table,
        "products_columns": json.loads(settings.products_columns or "[]"),
        "show_totals_panel": settings.show_totals_panel,
        "totals_position": settings.totals_position or "Right Sidebar",
        "cards": cards
    }


@frappe.whitelist()
def initialize_default_settings():
    """Initialize default card configuration"""
    settings = frappe.get_single("OPS Order View Settings")

    if settings.cards and len(settings.cards) > 0:
        return {"message": "Settings already configured"}

    # Default cards configuration
    default_cards = [
        {
            "card_name": "order_details",
            "card_title": "Order Details",
            "icon": "fa-file-text-o",
            "icon_color": "blue",
            "sort_order": 1,
            "is_visible": 1,
            "fields": [
                {"field_label": "Order ID", "source_field": "ops_order_id", "linked_doctype": "order", "field_type": "Text", "is_visible": 1},
                {"field_label": "Order Date", "source_field": "orders_date_finished", "linked_doctype": "order", "field_type": "Datetime", "is_visible": 1},
                {"field_label": "Production Due", "source_field": "production_due_date", "linked_doctype": "order", "field_type": "Date", "is_visible": 1},
                {"field_label": "Order Due", "source_field": "orders_due_date", "linked_doctype": "order", "field_type": "Date", "is_visible": 1},
                {"field_label": "Invoice #", "source_field": "invoice_number", "linked_doctype": "order", "field_type": "Text", "is_visible": 1}
            ]
        },
        {
            "card_name": "customer",
            "card_title": "Customer",
            "icon": "fa-user",
            "icon_color": "green",
            "sort_order": 2,
            "is_visible": 1,
            "fields": [
                {"field_label": "Name", "source_field": "customer_name", "linked_doctype": "customer", "field_type": "Text", "is_visible": 1},
                {"field_label": "Email", "source_field": "email", "linked_doctype": "customer", "field_type": "Email", "is_visible": 1, "is_link": 1, "link_template": "mailto:{value}"},
                {"field_label": "Phone", "source_field": "customers_telephone", "linked_doctype": "order", "field_type": "Phone", "is_visible": 1, "is_link": 1, "link_template": "tel:{value}"},
                {"field_label": "Company", "source_field": "company", "linked_doctype": "customer", "field_type": "Text", "is_visible": 1}
            ]
        },
        {
            "card_name": "billing",
            "card_title": "Billing Address",
            "icon": "fa-building",
            "icon_color": "orange",
            "sort_order": 3,
            "is_visible": 1,
            "fields": [
                {"field_label": "Name", "source_field": "name", "linked_doctype": "billing_address", "field_type": "Text", "is_visible": 1},
                {"field_label": "Company", "source_field": "company", "linked_doctype": "billing_address", "field_type": "Text", "is_visible": 1},
                {"field_label": "Address", "source_field": "street_address", "linked_doctype": "billing_address", "field_type": "Text", "is_visible": 1}
            ]
        },
        {
            "card_name": "shipping",
            "card_title": "Shipping Address",
            "icon": "fa-truck",
            "icon_color": "purple",
            "sort_order": 4,
            "is_visible": 1,
            "fields": [
                {"field_label": "Name", "source_field": "name", "linked_doctype": "shipping_address", "field_type": "Text", "is_visible": 1},
                {"field_label": "Company", "source_field": "company", "linked_doctype": "shipping_address", "field_type": "Text", "is_visible": 1},
                {"field_label": "Address", "source_field": "street_address", "linked_doctype": "shipping_address", "field_type": "Text", "is_visible": 1}
            ]
        },
        {
            "card_name": "blind_shipping",
            "card_title": "Blind Shipping",
            "icon": "fa-eye-slash",
            "icon_color": "teal",
            "sort_order": 5,
            "is_visible": 1,
            "fields": [
                {"field_label": "Name", "source_field": "name", "linked_doctype": "blind_shipping", "field_type": "Text", "is_visible": 1},
                {"field_label": "Company", "source_field": "company", "linked_doctype": "blind_shipping", "field_type": "Text", "is_visible": 1}
            ]
        },
        {
            "card_name": "payment",
            "card_title": "Payment & Shipping",
            "icon": "fa-credit-card",
            "icon_color": "pink",
            "sort_order": 6,
            "is_visible": 1,
            "fields": [
                {"field_label": "Shipping Method", "source_field": "shipping_mode", "linked_doctype": "order", "field_type": "Text", "is_visible": 1},
                {"field_label": "Carrier", "source_field": "courirer_company_name", "linked_doctype": "order", "field_type": "Text", "is_visible": 1},
                {"field_label": "Payment Method", "source_field": "payment_method_name", "linked_doctype": "order", "field_type": "Text", "is_visible": 1},
                {"field_label": "Transaction ID", "source_field": "transactionid", "linked_doctype": "order", "field_type": "Text", "is_visible": 1}
            ]
        }
    ]

    for card_data in default_cards:
        fields = card_data.pop("fields", [])
        card = settings.append("cards", card_data)
        for field_data in fields:
            card.append("fields", field_data)

    settings.save()
    frappe.db.commit()

    return {"message": "Default settings initialized", "cards_count": len(default_cards)}


def get_default_settings():
    """Return default settings when none configured"""
    return {
        "page_title": "Order #{ops_order_id}",
        "show_breadcrumb": True,
        "cards_per_row": 3,
        "enable_product_inline_edit": True,
        "show_products_table": True,
        "products_columns": [
            {"field": "products_name", "label": "Product"},
            {"field": "product_status", "label": "Status"},
            {"field": "products_quantity", "label": "Qty"},
            {"field": "products_price", "label": "Price"},
            {"field": "final_price", "label": "Total"}
        ],
        "show_totals_panel": True,
        "totals_position": "Right Sidebar",
        "cards": [
            {
                "id": "order_details",
                "title": "Order Details",
                "icon": "fa-file-text-o",
                "color": "blue",
                "fields": [
                    {"label": "Order ID", "field": "ops_order_id", "source": "order", "type": "Text"},
                    {"label": "Order Date", "field": "orders_date_finished", "source": "order", "type": "Datetime"},
                    {"label": "Production Due", "field": "production_due_date", "source": "order", "type": "Date"},
                    {"label": "Order Due", "field": "orders_due_date", "source": "order", "type": "Date"},
                    {"label": "Invoice #", "field": "invoice_number", "source": "order", "type": "Text"}
                ]
            },
            {
                "id": "customer",
                "title": "Customer",
                "icon": "fa-user",
                "color": "green",
                "fields": [
                    {"label": "Name", "field": "customer_name", "source": "customer", "type": "Text"},
                    {"label": "Email", "field": "email", "source": "customer", "type": "Email", "is_link": True, "link_template": "mailto:{value}"},
                    {"label": "Phone", "field": "customers_telephone", "source": "order", "type": "Phone", "is_link": True, "link_template": "tel:{value}"},
                    {"label": "Company", "field": "company", "source": "customer", "type": "Text"}
                ]
            },
            {
                "id": "billing",
                "title": "Billing Address",
                "icon": "fa-building",
                "color": "orange",
                "fields": [
                    {"label": "Name", "field": "name", "source": "billing_address", "type": "Text"},
                    {"label": "Company", "field": "company", "source": "billing_address", "type": "Text"},
                    {"label": "Address", "field": "street_address", "source": "billing_address", "type": "Text"}
                ]
            },
            {
                "id": "shipping",
                "title": "Shipping Address",
                "icon": "fa-truck",
                "color": "purple",
                "fields": [
                    {"label": "Name", "field": "name", "source": "shipping_address", "type": "Text"},
                    {"label": "Company", "field": "company", "source": "shipping_address", "type": "Text"},
                    {"label": "Address", "field": "street_address", "source": "shipping_address", "type": "Text"}
                ]
            },
            {
                "id": "blind_shipping",
                "title": "Blind Shipping",
                "icon": "fa-eye-slash",
                "color": "teal",
                "fields": [
                    {"label": "Name", "field": "name", "source": "blind_shipping", "type": "Text"},
                    {"label": "Company", "field": "company", "source": "blind_shipping", "type": "Text"}
                ]
            },
            {
                "id": "payment",
                "title": "Payment & Shipping",
                "icon": "fa-credit-card",
                "color": "pink",
                "fields": [
                    {"label": "Shipping Method", "field": "shipping_mode", "source": "order", "type": "Text"},
                    {"label": "Carrier", "field": "courirer_company_name", "source": "order", "type": "Text"},
                    {"label": "Payment Method", "field": "payment_method_name", "source": "order", "type": "Text"},
                    {"label": "Transaction ID", "field": "transactionid", "source": "order", "type": "Text"}
                ]
            }
        ]
    }
