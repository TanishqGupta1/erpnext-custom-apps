import json
import frappe

def get_sample_features():
    result = frappe.db.sql("SELECT features_details FROM `tabOPS Order Product` WHERE features_details IS NOT NULL AND features_details != '' LIMIT 1")
    if result:
        data = json.loads(result[0][0])
        for key in list(data.keys())[:3]:
            print(f"{key}: {json.dumps(data[key], indent=2)}")
            print("---")
    return "Done"

def get_stats():
    products_with_features = frappe.db.sql("SELECT COUNT(*) FROM `tabOPS Order Product` WHERE features_details IS NOT NULL AND features_details != ''")[0][0]
    total_products = frappe.db.count("OPS Order Product")
    products_with_options = frappe.db.sql("SELECT COUNT(DISTINCT orders_products_id) FROM `tabOPS Order Product Option`")[0][0]
    total_options = frappe.db.count("OPS Order Product Option")

    print(f"Total products: {total_products}")
    print(f"Products with features_details: {products_with_features}")
    print(f"Products with options extracted: {products_with_options}")
    print(f"Total options: {total_options}")

    return "Done"

def check_missing_options():
    # Find products with features but no options
    result = frappe.db.sql("""
        SELECT p.orders_products_id, p.products_title, p.features_details, p.parent
        FROM `tabOPS Order Product` p
        LEFT JOIN `tabOPS Order Product Option` o ON o.orders_products_id = p.orders_products_id
        WHERE p.features_details IS NOT NULL AND p.features_details != ''
        AND o.name IS NULL
        LIMIT 5
    """, as_dict=True)

    for row in result:
        print(f"Product {row.orders_products_id}: {row.products_title} (Order: {row.parent})")
        try:
            data = json.loads(row.features_details)
            print(f"  Options: {list(data.keys())}")
            for key in list(data.keys())[:2]:
                opt = data[key]
                heading = opt.get("Heading") if isinstance(opt, dict) else None
                print(f"    {key}: Heading={heading}")
        except:
            print(f"  Invalid JSON: {row.features_details[:100]}")
        print("---")

    return "Done"

def resync_missing():
    # Find order IDs for products with missing options
    result = frappe.db.sql("""
        SELECT DISTINCT p.parent
        FROM `tabOPS Order Product` p
        LEFT JOIN `tabOPS Order Product Option` o ON o.orders_products_id = p.orders_products_id
        WHERE p.features_details IS NOT NULL AND p.features_details != ''
        AND o.name IS NULL
    """)

    order_names = [r[0] for r in result]
    print(f"Orders needing resync: {len(order_names)}")

    for name in order_names[:5]:
        print(f"  - {name}")

    return order_names

def do_resync():
    from ops_ziflow.services.order_sync_service import sync_order_from_onprintshop

    # Get order IDs needing resync
    result = frappe.db.sql("""
        SELECT DISTINCT o.ops_order_id
        FROM `tabOPS Order` o
        INNER JOIN `tabOPS Order Product` p ON p.parent = o.name
        LEFT JOIN `tabOPS Order Product Option` opt ON opt.orders_products_id = p.orders_products_id
        WHERE p.features_details IS NOT NULL AND p.features_details != ''
        AND opt.name IS NULL
    """)

    order_ids = [int(r[0]) for r in result if r[0]]
    print(f"Re-syncing {len(order_ids)} orders: {order_ids}")

    for order_id in order_ids:
        try:
            sync_order_from_onprintshop(order_id)
            frappe.db.commit()
            print(f"  Synced order {order_id}")
        except Exception as e:
            print(f"  Error syncing order {order_id}: {e}")

    return "Done"

def check_parent_mismatch():
    # Check if options are linked to correct parent
    result = frappe.db.sql("""
        SELECT p.parent as product_parent, p.orders_products_id
        FROM `tabOPS Order Product` p
        LEFT JOIN `tabOPS Order Product Option` o ON o.orders_products_id = p.orders_products_id
        WHERE p.features_details IS NOT NULL AND p.features_details != ''
        AND o.name IS NULL
        LIMIT 5
    """, as_dict=True)

    for row in result:
        print(f"Product parent: {row.product_parent}, Product ID: {row.orders_products_id}")
        # Check if there are any options for this product at all
        opts = frappe.db.sql("""
            SELECT parent, orders_products_id, option_name
            FROM `tabOPS Order Product Option`
            WHERE orders_products_id = %s
        """, (row.orders_products_id,), as_dict=True)
        if opts:
            for o in opts:
                print(f"  Found option parent: {o.parent}, option: {o.option_name}")
        else:
            print(f"  No options found for product ID {row.orders_products_id}")
        print("---")

    return "check complete"

def add_billing_company_field():
    # Check if field already exists
    existing = frappe.db.exists("DocField", {"parent": "OPS Order", "fieldname": "billing_company"})
    if existing:
        print("Field billing_company already exists")
        return "Already exists"

    # Find idx of billing_name
    billing_name_idx = frappe.db.get_value("DocField",
        {"parent": "OPS Order", "fieldname": "billing_name"}, "idx")

    # Create the new field
    field = frappe.new_doc("DocField")
    field.parent = "OPS Order"
    field.parenttype = "DocType"
    field.parentfield = "fields"
    field.fieldname = "billing_company"
    field.fieldtype = "Data"
    field.label = "Billing Company"
    field.idx = billing_name_idx + 1 if billing_name_idx else 100
    field.insert(ignore_permissions=True)

    # Clear doctype cache
    frappe.clear_cache(doctype="OPS Order")

    print(f"Added billing_company field with idx {field.idx}")
    return "Done"

def add_product_options_field():
    # Check if field already exists
    existing = frappe.db.exists("DocField", {"parent": "OPS Order", "fieldname": "order_product_options"})
    if existing:
        print("Field order_product_options already exists")
        return "Already exists"

    # Get the current highest idx
    max_idx = frappe.db.sql("""
        SELECT MAX(idx) FROM tabDocField WHERE parent = 'OPS Order'
    """)[0][0] or 0

    # Find idx of ops_order_products
    ops_order_products_idx = frappe.db.get_value("DocField",
        {"parent": "OPS Order", "fieldname": "ops_order_products"}, "idx")

    # Create the new field
    field = frappe.new_doc("DocField")
    field.parent = "OPS Order"
    field.parenttype = "DocType"
    field.parentfield = "fields"
    field.fieldname = "order_product_options"
    field.fieldtype = "Table"
    field.label = "Product Options"
    field.options = "OPS Order Product Option"
    field.description = "Product options extracted from features_details"
    field.idx = ops_order_products_idx + 1 if ops_order_products_idx else max_idx + 1
    field.insert(ignore_permissions=True)

    # Clear doctype cache
    frappe.clear_cache(doctype="OPS Order")

    print(f"Added order_product_options field with idx {field.idx}")
    return "Done"

def check_api_features(order_id=2302):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient

    client = OnPrintShopClient()
    order = client.get_order(order_id)

    if not order:
        print(f"Order {order_id} not found in API")
        return

    products = order.get("product", [])
    print(f"Order {order_id} has {len(products)} products from API")

    for p in products:
        prod_id = p.get("orders_products_id")
        features = p.get("features_details")
        print(f"  Product {prod_id}: features_details = {bool(features)}")
        if features and isinstance(features, dict):
            print(f"    Keys: {list(features.keys())[:5]}...")

    return "Done"

def resync_all_orders():
    """Resync all orders to populate missing fields."""
    from ops_ziflow.services.order_sync_service import sync_order_from_onprintshop

    # Get all order IDs
    result = frappe.db.sql("""
        SELECT ops_order_id FROM `tabOPS Order` ORDER BY ops_order_id DESC
    """)

    order_ids = [int(r[0]) for r in result if r[0]]
    print(f"Re-syncing {len(order_ids)} orders...")

    synced = 0
    errors = 0
    for i, order_id in enumerate(order_ids):
        try:
            sync_order_from_onprintshop(order_id)
            frappe.db.commit()
            synced += 1
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{len(order_ids)} synced")
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error syncing order {order_id}: {e}")

    print(f"Done! Synced: {synced}, Errors: {errors}")
    return f"Synced {synced}, Errors {errors}"

def check_order_options(order_name="2302"):
    # Check options for specific order
    count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS Order Product Option` WHERE parent = %s
    """, (order_name,))[0][0]
    print(f"Order {order_name} has {count} options in DB")

    # Check if document has the options
    doc = frappe.get_doc("OPS Order", order_name)
    print(f"Document has {len(doc.get('order_product_options', []))} options via doc.get()")

    # Check if the meta recognizes the field
    meta = frappe.get_meta("OPS Order")
    field = meta.get_field("order_product_options")
    print(f"Meta has field: {field is not None}")
    if field:
        print(f"  Field options: {field.options}")

    return "check done"

def debug_sync_order(order_id=2302):
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from ops_ziflow.services.order_sync_service import _map_product_options

    client = OnPrintShopClient()
    order = client.get_order(order_id)

    if not order:
        print(f"Order {order_id} not found in API")
        return

    products = order.get("product", [])
    print(f"Order {order_id} has {len(products)} products from API")

    # Get the document
    doc = frappe.get_doc("OPS Order", str(order_id))
    print(f"Before _map_product_options: {len(doc.get('order_product_options', []))} options")

    # Call _map_product_options
    _map_product_options(doc, products)
    print(f"After _map_product_options: {len(doc.get('order_product_options', []))} options")

    # Try to save with flags to skip validation
    doc.sync_in_progress = 1
    doc.flags.ignore_links = True
    doc.flags.ignore_validate = True
    try:
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("Document saved")
    except Exception as e:
        print(f"Error saving: {e}")

    # Check DB again
    count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabOPS Order Product Option` WHERE parent = %s
    """, (str(order_id),))[0][0]
    print(f"After save: {count} options in DB")

    return "debug done"

def fix_all_missing_options():
    from ops_ziflow.services.onprintshop_client import OnPrintShopClient
    from ops_ziflow.services.order_sync_service import _map_product_options

    client = OnPrintShopClient()

    # Get order IDs needing resync
    result = frappe.db.sql("""
        SELECT DISTINCT o.name, o.ops_order_id
        FROM `tabOPS Order` o
        INNER JOIN `tabOPS Order Product` p ON p.parent = o.name
        LEFT JOIN `tabOPS Order Product Option` opt ON opt.orders_products_id = p.orders_products_id
        WHERE p.features_details IS NOT NULL AND p.features_details != ''
        AND opt.name IS NULL
    """, as_dict=True)

    print(f"Fixing {len(result)} orders with missing options")

    for row in result:
        order_name = row.name
        order_id = int(row.ops_order_id)

        try:
            order = client.get_order(order_id)
            if not order:
                print(f"  Order {order_id}: Not found in API")
                continue

            products = order.get("product", [])
            doc = frappe.get_doc("OPS Order", order_name)

            _map_product_options(doc, products)

            # Set required fields if missing
            if not doc.tracking_url:
                doc.tracking_url = "N/A"
            if not doc.carrier_raw_response:
                doc.carrier_raw_response = "{}"

            doc.sync_in_progress = 1
            doc.flags.ignore_links = True
            doc.flags.ignore_validate = True
            doc.flags.ignore_mandatory = True
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"  Order {order_name}: Added {len(doc.order_product_options)} options")
        except Exception as e:
            print(f"  Order {order_name}: Error - {e}")

    return "Done"
