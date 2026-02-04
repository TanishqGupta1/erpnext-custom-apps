import frappe

def check_new_fields(order_name="2302"):
    doc = frappe.get_doc("OPS Order", order_name)

    print(f"Order: {order_name}")
    print(f"=== Delivery ===")
    print(f"  delivery_telephone: {doc.get('delivery_telephone')}")
    print(f"  delivery_state_code: {doc.get('delivery_state_code')}")
    print(f"  delivery_suburb: {doc.get('delivery_suburb')}")
    print(f"  delivery_company: {doc.get('delivery_company')}")
    print(f"=== Billing ===")
    print(f"  billing_phone: {doc.get('billing_phone')}")
    print(f"  billing_state_code: {doc.get('billing_state_code')}")
    print(f"  billing_suburb: {doc.get('billing_suburb')}")
    print(f"  billing_company: {doc.get('billing_company')}")
    print(f"=== Customer ===")
    print(f"  customer_company: {doc.get('customer_company')}")
    print(f"  customer_company_name: {doc.get('customer_company_name')}")
    print(f"=== Product Options ===")
    print(f"  Total options: {len(doc.get('order_product_options', []))}")

    return "Done"

def check_db_values(order_name="2302"):
    result = frappe.db.sql("""
        SELECT customer_company, customer_company_name, delivery_company, billing_company,
               delivery_telephone, billing_phone, delivery_state_code, billing_state_code
        FROM `tabOPS Order` WHERE name = %s
    """, (order_name,), as_dict=True)

    if result:
        r = result[0]
        for key, value in r.items():
            print(f"  {key}: {value}")

    return "Done"
