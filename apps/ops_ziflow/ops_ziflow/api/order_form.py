"""
OPS Order Form API
Provides backend functionality for the enhanced OPS Order form view
"""
import frappe
from frappe import _
import json


@frappe.whitelist()
def get_order_enriched_data(order_name):
    """
    Get order with all related data for enhanced form display

    Returns: customer details, proofs with previews, parsed product options, status history
    """
    doc = frappe.get_doc("OPS Order", order_name)

    # Get all proofs for this order
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={"ops_order": order_name},
        fields=[
            "name", "proof_name", "proof_status", "ziflow_url", "preview_url",
            "deadline", "approved_at", "ops_order_product"
        ]
    )

    # Count proofs by status
    proof_summary = {
        "total": len(proofs),
        "approved": sum(1 for p in proofs if p.proof_status == "Approved"),
        "pending": sum(1 for p in proofs if p.proof_status in ("Pending", "In Review")),
        "rejected": sum(1 for p in proofs if p.proof_status == "Rejected")
    }

    # Get customer details
    customer = None
    ops_customer = getattr(doc, 'ops_customer', None) or getattr(doc, 'customer', None)
    if ops_customer:
        try:
            cust_doc = frappe.get_doc("OPS Customer", ops_customer)
            customer = {
                "name": cust_doc.name,
                "customer_name": getattr(cust_doc, "customer_name", None) or cust_doc.name,
                "email": getattr(cust_doc, "email", None),
                "phone": getattr(cust_doc, "phone", None),
                "company": getattr(cust_doc, "company_name", None),
                "address": get_customer_address(cust_doc),
                "total_orders": frappe.db.count("OPS Order", {"customer": ops_customer}),
                "total_spent": frappe.db.sql("""
                    SELECT COALESCE(SUM(total_amount), 0)
                    FROM `tabOPS Order`
                    WHERE customer = %s
                """, ops_customer)[0][0]
            }
        except Exception:
            pass

    # If no linked customer, use order customer fields
    if not customer:
        customer = {
            "name": None,
            "customer_name": getattr(doc, "customer_name", None) or getattr(doc, "customer", None),
            "email": getattr(doc, "customer_email", None) or getattr(doc, "email", None),
            "phone": getattr(doc, "customer_telephone", None) or getattr(doc, "phone", None),
            "company": getattr(doc, "customer_company", None) or getattr(doc, "company", None),
            "address": format_delivery_address(doc),
            "total_orders": None,
            "total_spent": None
        }

    # Get order status history (from comments/versions)
    status_history = get_order_status_history(order_name)

    # Get ALL options from order's child table (order_product_options)
    all_order_options = frappe.get_all(
        "OPS Order Product Option",
        filters={"parent": order_name, "parenttype": "OPS Order"},
        fields=["option_name", "option_value", "option_group", "option_price", "orders_products_id", "product_name"],
        order_by="idx"
    )

    # Group options by orders_products_id
    options_by_product_id = {}
    for opt in all_order_options:
        pid = opt.get("orders_products_id")
        if pid:
            if pid not in options_by_product_id:
                options_by_product_id[pid] = []
            options_by_product_id[pid].append(opt)

    # Parse products with options
    products_enriched = []
    for product in doc.ops_order_products:
        product_data = product.as_dict()

        # Get options for this product by orders_products_id
        product_id = product.orders_products_id
        product_opts = options_by_product_id.get(product_id, [])

        if product_opts:
            # Group options by option_group
            product_options = group_product_options(product_opts)
        else:
            # Fallback to parsing features_details JSON
            product_options = parse_features_details(product.features_details)

        product_data["parsed_options"] = product_options

        # Get master options linked to this product
        master_options = get_master_options_for_product(product.name, product_id)
        product_data["master_options"] = master_options

        # Get proof linked to this product
        product_proofs = [p for p in proofs if p.ops_order_product == product.name]
        product_data["proofs"] = product_proofs
        product_data["proof_status"] = product_proofs[0].proof_status if product_proofs else None
        product_data["proof_preview_url"] = product_proofs[0].preview_url if product_proofs else None

        products_enriched.append(product_data)

    return {
        "order": doc.as_dict(),
        "customer": customer,
        "proofs": proofs,
        "proof_summary": proof_summary,
        "products": products_enriched,
        "status_history": status_history
    }


def get_customer_address(cust_doc):
    """Format customer address from OPS Customer"""
    parts = []
    if hasattr(cust_doc, 'street') and cust_doc.street:
        parts.append(cust_doc.street)
    if hasattr(cust_doc, 'city') and cust_doc.city:
        parts.append(cust_doc.city)
    if hasattr(cust_doc, 'state') and cust_doc.state:
        parts.append(cust_doc.state)
    if hasattr(cust_doc, 'country') and cust_doc.country:
        parts.append(cust_doc.country)
    if hasattr(cust_doc, 'postal_code') and cust_doc.postal_code:
        parts.append(cust_doc.postal_code)
    return ", ".join(parts) if parts else None


def format_delivery_address(doc):
    """Format delivery address from order fields"""
    parts = []
    if doc.delivery_street_address:
        parts.append(doc.delivery_street_address)
    if doc.delivery_city:
        parts.append(doc.delivery_city)
    if doc.delivery_state:
        parts.append(doc.delivery_state)
    if doc.delivery_country:
        parts.append(doc.delivery_country)
    if doc.delivery_postcode:
        parts.append(doc.delivery_postcode)
    return ", ".join(parts) if parts else None


def get_order_status_history(order_name):
    """Get status change history from versions/comments"""
    history = []

    # Get version history
    versions = frappe.get_all(
        "Version",
        filters={"docname": order_name, "ref_doctype": "OPS Order"},
        fields=["creation", "data"],
        order_by="creation desc",
        limit=10
    )

    for v in versions:
        try:
            data = json.loads(v.data) if isinstance(v.data, str) else v.data
            if "changed" in data:
                for change in data["changed"]:
                    if len(change) >= 3 and change[0] == "order_status":
                        history.append({
                            "date": v.creation,
                            "from_status": change[1],
                            "to_status": change[2]
                        })
        except Exception:
            pass

    return history


def get_master_options_for_product(product_name, orders_products_id):
    """
    Get master options from OPS Master Option Attribute linked to a product
    Returns list of master option attributes with their values
    """
    master_options = []

    # Try to get master options via product options child table
    if frappe.db.exists("DocType", "OPS Master Option Attribute"):
        try:
            # Get options that have master_option links
            options_with_master = frappe.get_all(
                "OPS Order Product Option",
                filters={
                    "parent": product_name,
                    "parenttype": "OPS Order Product",
                    "master_option": ["is", "set"]
                },
                fields=["option_name", "option_value", "option_price", "master_option"]
            )

            for opt in options_with_master:
                if opt.master_option:
                    # Get master option details
                    master_info = frappe.db.get_value(
                        "OPS Master Option Attribute",
                        opt.master_option,
                        ["name", "option_name", "group_name", "display_order", "option_type"],
                        as_dict=True
                    )
                    if master_info:
                        master_options.append({
                            "name": master_info.name,
                            "option_name": master_info.option_name or opt.option_name,
                            "option_value": opt.option_value,
                            "option_price": float(opt.option_price or 0),
                            "group_name": master_info.group_name,
                            "option_type": master_info.option_type
                        })

            # Also try to get master options linked directly via orders_products_id
            if not master_options and orders_products_id:
                direct_master_opts = frappe.get_all(
                    "OPS Order Product Option",
                    filters={
                        "orders_products_id": orders_products_id,
                        "master_option": ["is", "set"]
                    },
                    fields=["option_name", "option_value", "option_price", "master_option"]
                )

                for opt in direct_master_opts:
                    if opt.master_option:
                        master_info = frappe.db.get_value(
                            "OPS Master Option Attribute",
                            opt.master_option,
                            ["name", "option_name", "group_name", "display_order", "option_type"],
                            as_dict=True
                        )
                        if master_info:
                            master_options.append({
                                "name": master_info.name,
                                "option_name": master_info.option_name or opt.option_name,
                                "option_value": opt.option_value,
                                "option_price": float(opt.option_price or 0),
                                "group_name": master_info.group_name,
                                "option_type": master_info.option_type
                            })
        except Exception as e:
            frappe.log_error(f"Error fetching master options: {str(e)}", "OPS Order Form")

    return master_options


def get_product_options_from_child_table(product_name):
    """
    Get product options from OPS Order Product Option child table
    with master option details for proper display
    """
    # Get options from child table
    options = frappe.get_all(
        "OPS Order Product Option",
        filters={"parent": product_name, "parenttype": "OPS Order Product"},
        fields=["option_name", "option_value", "option_price", "master_option"],
        order_by="idx"
    )

    if not options:
        return {"groups": [], "total_options_price": 0, "options_count": 0}

    # Group options by category (derive from option_name or master_option)
    groups = {}
    total_price = 0

    # Cache master option lookups
    master_options_cache = {}

    for opt in options:
        # Get master option details if available
        master_info = None
        if opt.master_option:
            if opt.master_option not in master_options_cache:
                master_info = frappe.db.get_value(
                    "OPS Master Option Attribute",
                    opt.master_option,
                    ["option_name", "group_name", "display_order"],
                    as_dict=True
                )
                master_options_cache[opt.master_option] = master_info
            else:
                master_info = master_options_cache[opt.master_option]

        # Determine group name
        group_name = "Options"
        if master_info and master_info.get("group_name"):
            group_name = master_info.get("group_name")
        elif opt.option_name:
            # Derive group from option name pattern
            group_name = derive_group_from_option_name(opt.option_name)

        if group_name not in groups:
            groups[group_name] = []

        price = float(opt.option_price or 0)
        total_price += price

        groups[group_name].append({
            "label": opt.option_name or "",
            "value": opt.option_value or "",
            "price": price,
            "price_formatted": f"+${price:.2f}" if price > 0 else "included",
            "master_option": opt.master_option,
            "master_option_name": master_info.get("option_name") if master_info else None
        })

    # Convert to list format with icons
    groups_list = [
        {"name": name, "options": opts, "icon": get_group_icon(name)}
        for name, opts in groups.items()
    ]

    return {
        "groups": groups_list,
        "total_options_price": total_price,
        "total_formatted": f"${total_price:.2f}",
        "options_count": len(options)
    }


def derive_group_from_option_name(option_name):
    """Derive option group from option name"""
    option_lower = option_name.lower()

    if any(kw in option_lower for kw in ["paper", "stock", "material", "substrate"]):
        return "Paper & Material"
    elif any(kw in option_lower for kw in ["size", "dimension", "width", "height"]):
        return "Size"
    elif any(kw in option_lower for kw in ["lamination", "coating", "finish", "uv"]):
        return "Finishing"
    elif any(kw in option_lower for kw in ["cut", "die", "perforation", "fold"]):
        return "Cutting & Finishing"
    elif any(kw in option_lower for kw in ["proof", "preview"]):
        return "Proofing"
    elif any(kw in option_lower for kw in ["print", "color", "ink", "sided"]):
        return "Printing"
    elif any(kw in option_lower for kw in ["bind", "staple", "coil"]):
        return "Binding"
    elif any(kw in option_lower for kw in ["ship", "delivery", "turnaround", "production time"]):
        return "Delivery"
    elif any(kw in option_lower for kw in ["design", "artwork", "graphic"]):
        return "Design"
    else:
        return "Options"


@frappe.whitelist()
def get_product_options_parsed(order_product_name):
    """
    Get product options from child table (primary) or parse features_details (fallback)
    Returns grouped options with prices and attributes
    """
    # Try child table first
    options = get_product_options_from_child_table(order_product_name)
    if options.get("options_count", 0) > 0:
        return options

    # Fallback to parsing features_details JSON
    product = frappe.get_doc("OPS Order Product", order_product_name)
    return parse_features_details(product.features_details)


def group_product_options(options_list):
    """
    Group product options from OPS Order Product Option child table
    """
    if not options_list:
        return {"groups": [], "total_options_price": 0, "options_count": 0}

    groups = {}
    total_price = 0

    for opt in options_list:
        group_name = opt.get("option_group") or "Options"
        if group_name not in groups:
            groups[group_name] = []

        price = float(opt.get("option_price") or 0)
        total_price += price

        groups[group_name].append({
            "label": opt.get("option_name", ""),
            "value": opt.get("option_value", ""),
            "price": price,
            "price_formatted": f"+${price:.2f}" if price > 0 else ""
        })

    groups_list = [
        {"name": name, "options": opts, "icon": get_group_icon(name)}
        for name, opts in groups.items()
    ]

    options_count = sum(len(g.get("options", [])) for g in groups_list)
    return {
        "groups": groups_list,
        "total_options_price": total_price,
        "total_formatted": f"${total_price:.2f}",
        "options_count": options_count
    }


def parse_features_details(features_json):
    """
    Parse features_details JSON into structured groups
    """
    if not features_json:
        return {"groups": [], "total_options_price": 0}

    try:
        if isinstance(features_json, str):
            features = json.loads(features_json)
        else:
            features = features_json
    except (json.JSONDecodeError, TypeError):
        return {"groups": [], "total_options_price": 0, "raw": str(features_json)}

    # Group options by category
    groups = {}
    total_price = 0

    # Handle different JSON structures from OPS
    if isinstance(features, list):
        for item in features:
            group_name = item.get("group", item.get("category", "Other"))
            if group_name not in groups:
                groups[group_name] = []

            price = float(item.get("price", 0) or 0)
            total_price += price

            groups[group_name].append({
                "label": item.get("name", item.get("label", "")),
                "value": item.get("value", item.get("selected", "")),
                "price": price,
                "price_formatted": f"+${price:.2f}" if price > 0 else "included"
            })

    elif isinstance(features, dict):
        # Handle dict structure (OPS format: AO-1, AO-2, etc.)
        for key, value in features.items():
            if isinstance(value, dict):
                # OPS JSON format: Heading, AttributeLabel, AttributeValue, optionGroup
                group_name = value.get("optionGroup", value.get("Heading", value.get("group", "Options")))
                if group_name not in groups:
                    groups[group_name] = []

                price = float(value.get("price", value.get("option_price", 0)) or 0)
                total_price += price

                # Get label and value from OPS format
                label = value.get("Heading", value.get("AttributeLabel", key))
                val = value.get("AttributeValue", value.get("AttributeLabel", value.get("value", value.get("selected", ""))))

                groups[group_name].append({
                    "label": label,
                    "value": val,
                    "price": price,
                    "price_formatted": f"+${price:.2f}" if price > 0 else ""
                })
            else:
                if "General" not in groups:
                    groups["General"] = []
                groups["General"].append({
                    "label": key,
                    "value": str(value),
                    "price": 0,
                    "price_formatted": ""
                })

    # Convert to list format
    groups_list = [
        {"name": name, "options": opts, "icon": get_group_icon(name)}
        for name, opts in groups.items()
    ]

    options_count = sum(len(g.get("options", [])) for g in groups_list)
    return {
        "groups": groups_list,
        "total_options_price": total_price,
        "total_formatted": f"${total_price:.2f}",
        "options_count": options_count
    }


def get_group_icon(group_name):
    """Get icon for option group"""
    icons = {
        "Paper": "fa-file",
        "Paper & Size": "fa-file",
        "Size": "fa-expand",
        "Finishing": "fa-magic",
        "Design": "fa-paint-brush",
        "Printing": "fa-print",
        "Binding": "fa-book",
        "Packaging": "fa-box",
        "Delivery": "fa-truck",
        "General": "fa-cog",
        "Other": "fa-list"
    }
    return icons.get(group_name, "fa-list")


@frappe.whitelist()
def quick_action(order_name, action, **kwargs):
    """
    Handle quick actions from the order form dropdown

    Actions: update_status, send_to_production, create_proofs, sync_order, print_order
    """
    doc = frappe.get_doc("OPS Order", order_name)

    if action == "update_status":
        new_status = kwargs.get("status")
        if not new_status:
            return {"success": False, "message": "Status is required"}

        old_status = doc.order_status
        doc.order_status = new_status
        doc.save(ignore_permissions=True)

        return {
            "success": True,
            "message": f"Status updated from '{old_status}' to '{new_status}'"
        }

    elif action == "send_to_production":
        doc.order_status = "In Production"
        doc.save(ignore_permissions=True)
        return {"success": True, "message": "Order sent to production"}

    elif action == "create_proofs":
        # Trigger proof creation for all products
        from ops_ziflow.services.proof_service import create_proofs_for_order
        try:
            result = create_proofs_for_order(order_name)
            return {"success": True, "message": f"Created {result.get('count', 0)} proofs"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    elif action == "sync_order":
        # Trigger sync from OPS
        from ops_ziflow.services.order_sync_service import sync_single_order
        try:
            sync_single_order(doc.ops_order_id)
            return {"success": True, "message": "Order synced from OPS"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    elif action == "mark_shipped":
        doc.shipping_status = "Shipped"
        doc.tracking_number = kwargs.get("tracking_number", "")
        doc.tracking_url = kwargs.get("tracking_url", "")
        doc.save(ignore_permissions=True)
        return {"success": True, "message": "Order marked as shipped"}

    elif action == "mark_complete":
        doc.order_status = "Order Completed"
        doc.save(ignore_permissions=True)
        return {"success": True, "message": "Order marked as complete"}

    elif action == "copy_details":
        # Return formatted order details for clipboard
        details = format_order_for_clipboard(doc)
        return {"success": True, "message": "Details copied", "data": details}

    else:
        return {"success": False, "message": f"Unknown action: {action}"}


def format_order_for_clipboard(doc):
    """Format order details for copying to clipboard"""
    lines = [
        f"Order: {doc.ops_order_id}",
        f"Customer: {doc.customer_name}",
        f"Email: {doc.customer_email}",
        f"Phone: {doc.customer_telephone}",
        f"Status: {doc.order_status}",
        f"Total: ${doc.total_amount or 0:.2f}",
        "",
        "Products:"
    ]

    for p in doc.ops_order_products:
        lines.append(f"  - {p.products_title} x{p.products_quantity} = ${p.final_price or 0:.2f}")

    if doc.delivery_street_address:
        lines.extend([
            "",
            "Shipping Address:",
            f"  {doc.delivery_street_address}",
            f"  {doc.delivery_city}, {doc.delivery_state} {doc.delivery_postcode}",
            f"  {doc.delivery_country}"
        ])

    return "\n".join(lines)


@frappe.whitelist()
def get_ziflow_proofs_for_order(order_name):
    """Get all proofs with preview URLs for an order"""
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={"ops_order": order_name},
        fields=[
            "name", "proof_name", "proof_status", "ziflow_url", "preview_url",
            "deadline", "approved_at", "ops_order_product",
            "creation", "modified"
        ],
        order_by="creation desc"
    )

    # Enrich with product info
    for proof in proofs:
        if proof.ops_order_product:
            product = frappe.db.get_value(
                "OPS Order Product",
                proof.ops_order_product,
                ["products_title", "products_sku"],
                as_dict=True
            )
            if product:
                proof["product_title"] = product.products_title
                proof["product_sku"] = product.products_sku

    # Summary
    summary = {
        "total": len(proofs),
        "approved": sum(1 for p in proofs if p.proof_status == "Approved"),
        "pending": sum(1 for p in proofs if p.proof_status in ("Pending", "In Review")),
        "rejected": sum(1 for p in proofs if p.proof_status == "Rejected")
    }

    return {
        "proofs": proofs,
        "summary": summary
    }


@frappe.whitelist()
def get_order_statuses():
    """Get available order statuses for dropdown"""
    return [
        "Pending",
        "Awaiting Payment",
        "Payment Received",
        "Proofing",
        "Awaiting Proof Approval",
        "In Production",
        "Ready to Ship",
        "Shipped",
        "Delivered",
        "Order Completed",
        "On Hold",
        "Cancelled",
        "Refunded"
    ]


@frappe.whitelist()
def update_proof_status(proof_name, status):
    """Quick update proof status from order form"""
    doc = frappe.get_doc("OPS ZiFlow Proof", proof_name)
    old_status = doc.proof_status
    doc.proof_status = status

    if status == "Approved":
        doc.approved_at = frappe.utils.now()

    doc.save(ignore_permissions=True)

    # Update parent order proof counts
    if doc.ops_order:
        update_order_proof_counts(doc.ops_order)

    return {
        "success": True,
        "message": f"Proof status updated from '{old_status}' to '{status}'"
    }


def update_order_proof_counts(order_name):
    """Update proof count fields on order"""
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={"ops_order": order_name},
        fields=["proof_status"]
    )

    pending = sum(1 for p in proofs if p.proof_status in ("Pending", "In Review"))
    approved = sum(1 for p in proofs if p.proof_status == "Approved")
    all_approved = len(proofs) > 0 and approved == len(proofs)

    frappe.db.set_value("OPS Order", order_name, {
        "pending_proof_count": pending,
        "all_proofs_approved": 1 if all_approved else 0
    })


# =========================================
# NEW ENDPOINTS FOR FORM REDESIGN
# =========================================

@frappe.whitelist()
def get_tab_data(order_name, tab):
    """Get data for specific tabs (lazy loading)"""
    doc = frappe.get_doc("OPS Order", order_name)

    if tab == "shipment":
        return get_shipment_data(doc)
    elif tab == "notes":
        return get_notes_data(doc)
    elif tab == "modify":
        return get_modify_data(doc)
    elif tab == "pickup-details":
        return get_pickup_data(doc)
    elif tab == "assign-job":
        return get_assign_job_data(doc)
    elif tab == "impose":
        return get_impose_data(doc)
    elif tab == "payment-request":
        return get_payment_request_data(doc)
    return None


def get_shipment_data(doc):
    """Get shipment-related data"""
    shipments = []
    if frappe.db.exists("DocType", "OPS Shipment"):
        shipments = frappe.get_all("OPS Shipment", filters={"ops_order": doc.name}, fields=["*"], order_by="creation desc")
    return {
        "shipping_company": getattr(doc, "shipping_company", None),
        "shipping_method": getattr(doc, "shipping_method", None),
        "shipping_type": getattr(doc, "shipping_type", None),
        "tracking_number": getattr(doc, "tracking_number", None),
        "tracking_url": getattr(doc, "tracking_url", None),
        "estimated_delivery": getattr(doc, "estimated_delivery_date", None),
        "shipments": shipments
    }


def get_notes_data(doc):
    """Get order notes and comments"""
    comments = frappe.get_all("Comment", filters={"reference_doctype": "OPS Order", "reference_name": doc.name, "comment_type": "Comment"}, fields=["name", "content", "comment_email", "creation", "owner"], order_by="creation desc")
    return {
        "admin_notes": getattr(doc, "admin_notes", None),
        "customer_notes": getattr(doc, "customer_notes", None),
        "comments": comments
    }


def get_modify_data(doc):
    """Get data for modify tab"""
    return {"order": doc.as_dict(), "editable_fields": ["customer_name", "customer_email", "customer_telephone", "delivery_street_address", "delivery_city", "delivery_state", "delivery_postcode", "delivery_country", "shipping_method", "tracking_number"]}


def get_pickup_data(doc):
    """Get pickup details data"""
    return {
        "is_pickup": getattr(doc, "is_pickup", False),
        "pickup_date": getattr(doc, "pickup_date", None),
        "pickup_time": getattr(doc, "pickup_time", None),
        "pickup_location": getattr(doc, "pickup_location", None),
        "pickup_notes": getattr(doc, "pickup_notes", None)
    }


def get_assign_job_data(doc):
    """Get job assignment data"""
    return {
        "assigned_to": getattr(doc, "assigned_to", None),
        "assigned_date": getattr(doc, "assigned_date", None),
        "production_team": getattr(doc, "production_team", None),
        "available_users": frappe.get_all("User", filters={"enabled": 1}, fields=["name", "full_name"])
    }


def get_impose_data(doc):
    """Get imposition data"""
    return {
        "impose_status": getattr(doc, "impose_status", None),
        "impose_notes": getattr(doc, "impose_notes", None),
        "products": [{"name": p.name, "title": p.products_title, "quantity": p.products_quantity, "width": getattr(p, "custom_width", None), "height": getattr(p, "custom_height", None)} for p in doc.ops_order_products]
    }


def get_payment_request_data(doc):
    """Get payment request data"""
    payment_requests = []
    if frappe.db.exists("DocType", "Payment Request"):
        payment_requests = frappe.get_all("Payment Request", filters={"reference_doctype": "OPS Order", "reference_name": doc.name}, fields=["*"], order_by="creation desc")
    return {
        "total_amount": doc.total_amount or 0,
        "paid_amount": getattr(doc, "paid_amount", 0),
        "payment_status": getattr(doc, "payment_status", None),
        "payment_method": getattr(doc, "payment_method", None),
        "payment_requests": payment_requests
    }


@frappe.whitelist()
def update_product_status(product_name, status):
    """Update order product status inline"""
    doc = frappe.get_doc("OPS Order Product", product_name)
    old_status = getattr(doc, "product_status", None)
    doc.product_status = status
    doc.save(ignore_permissions=True)
    return {"success": True, "message": "Status updated from '{}' to '{}'".format(old_status, status)}


@frappe.whitelist()
def bulk_update_product_status(product_names, status):
    """Bulk update product statuses"""
    if isinstance(product_names, str):
        product_names = json.loads(product_names)
    updated = 0
    for name in product_names:
        try:
            doc = frappe.get_doc("OPS Order Product", name)
            doc.product_status = status
            doc.save(ignore_permissions=True)
            updated += 1
        except Exception:
            pass
    return {"success": True, "updated": updated, "message": "Updated {} of {} products".format(updated, len(product_names))}


@frappe.whitelist()
def send_order_email(order_name, email_type="manual"):
    """Send order email manually"""
    doc = frappe.get_doc("OPS Order", order_name)
    recipient = doc.customer_email
    if not recipient:
        return {"success": False, "message": "No customer email found"}
    subject = "Order #{} - Update".format(doc.ops_order_id)
    message = "<p>Hello {},</p><p>This is an update regarding your order #{}.</p><p>Current Status: <strong>{}</strong></p><p>Total Amount: ${:.2f}</p><p>Thank you for your business!</p>".format(doc.customer_name, doc.ops_order_id, doc.order_status, doc.total_amount or 0)
    try:
        frappe.sendmail(recipients=[recipient], subject=subject, message=message, reference_doctype="OPS Order", reference_name=order_name)
        return {"success": True, "message": "Email sent to {}".format(recipient)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def add_order_product(order_name, product_data):
    """Add new product to order"""
    if isinstance(product_data, str):
        product_data = json.loads(product_data)
    order = frappe.get_doc("OPS Order", order_name)
    product = order.append("ops_order_products", product_data)
    order.save(ignore_permissions=True)
    return {"success": True, "product_name": product.name, "message": "Product added successfully"}


@frappe.whitelist()
def get_order_full_data(order_name):
    """Enhanced enriched data with all required fields for redesigned form"""
    doc = frappe.get_doc("OPS Order", order_name)
    base_data = get_order_enriched_data(order_name)

    billing_address = {
        "company": getattr(doc, "billing_company", None),
        "street": getattr(doc, "billing_street_address", None),
        "city": getattr(doc, "billing_city", None),
        "state": getattr(doc, "billing_state", None),
        "postcode": getattr(doc, "billing_postcode", None),
        "country": getattr(doc, "billing_country", None),
        "phone": getattr(doc, "billing_telephone", None)
    }

    shipping_address = {
        "company": getattr(doc, "delivery_company", doc.customer_company),
        "street": doc.delivery_street_address,
        "city": doc.delivery_city,
        "state": doc.delivery_state,
        "postcode": doc.delivery_postcode,
        "country": doc.delivery_country,
        "phone": getattr(doc, "delivery_telephone", doc.customer_telephone)
    }

    shipping_info = {
        "company": getattr(doc, "shipping_company", None),
        "method": getattr(doc, "shipping_method", None),
        "type": getattr(doc, "shipping_type", None),
        "tracking_number": getattr(doc, "tracking_number", None),
        "tracking_url": getattr(doc, "tracking_url", None),
        "estimated_delivery": str(doc.estimated_delivery_date) if getattr(doc, "estimated_delivery_date", None) else None,
        "payment_method": getattr(doc, "payment_method", None),
        "payment_date": str(doc.payment_date) if getattr(doc, "payment_date", None) else None,
        "payment_due_date": str(doc.payment_due_date) if getattr(doc, "payment_due_date", None) else None,
        "transaction_id": getattr(doc, "transaction_id", None)
    }

    subtotal = float(getattr(doc, "subtotal", 0) or getattr(doc, "order_amount", 0) or 0)
    shipping_charges = float(getattr(doc, "shipping_amount", 0) or 0)
    tax = float(getattr(doc, "tax_amount", 0) or 0)
    processing_fees = float(getattr(doc, "processing_fees", 0) or 0)
    total = float(getattr(doc, "total_amount", 0) or 0)
    paid = float(getattr(doc, "paid_amount", 0) or 0)

    financial_summary = {
        "subtotal": subtotal,
        "shipping_charges": shipping_charges,
        "tax": tax,
        "processing_fees": processing_fees,
        "total": total,
        "paid_amount": paid,
        "outstanding": total - paid
    }

    blind_shipping = {
        "enabled": getattr(doc, "blind_shipping", False),
        "company": getattr(doc, "blind_ship_company", None),
        "address": getattr(doc, "blind_ship_address", None),
        "phone": getattr(doc, "blind_ship_phone", None)
    }

    customer_extra = {
        "job_title": getattr(doc, "customer_job_title", None),
        "website": getattr(doc, "customer_website", None),
        "business_category": getattr(doc, "primary_business_category", None)
    }

    base_data["billing_address"] = billing_address
    base_data["shipping_address"] = shipping_address
    base_data["shipping_info"] = shipping_info
    base_data["financial_summary"] = financial_summary
    base_data["blind_shipping"] = blind_shipping
    base_data["customer_extra"] = customer_extra

    return base_data


@frappe.whitelist()
def add_order_note(order_name, note_content, note_type="admin"):
    """Add a note to the order"""
    if note_type == "comment":
        comment = frappe.get_doc({"doctype": "Comment", "comment_type": "Comment", "reference_doctype": "OPS Order", "reference_name": order_name, "content": note_content})
        comment.insert(ignore_permissions=True)
        return {"success": True, "message": "Comment added", "comment_name": comment.name}
    else:
        doc = frappe.get_doc("OPS Order", order_name)
        if hasattr(doc, "admin_notes"):
            existing = doc.admin_notes or ""
            timestamp = frappe.utils.now()
            doc.admin_notes = "{}\n\n[{}]\n{}".format(existing, timestamp, note_content).strip()
            doc.save(ignore_permissions=True)
        return {"success": True, "message": "Note added"}


@frappe.whitelist()
def create_html_wrapper_field():
    """Create the HTML wrapper field for OPS Order form redesign"""
    if frappe.db.exists('Custom Field', {'dt': 'OPS Order', 'fieldname': 'customer_panel_html'}):
        return {"success": True, "message": "Field already exists"}

    try:
        doc = frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'OPS Order',
            'fieldname': 'customer_panel_html',
            'fieldtype': 'HTML',
            'label': 'Customer Panel',
            'insert_after': 'order_status',
            'read_only': 1
        })
        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "message": "Field created successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}
