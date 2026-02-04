"""Check OPS Product structure and find sync pattern."""
import frappe
import json

@frappe.whitelist()
def check():
    """Check OPS Product and Option structure."""

    # Get sample OPS Product
    products = frappe.db.sql("""
        SELECT name, product_id, product_name
        FROM `tabOPS Product`
        LIMIT 3
    """, as_dict=True)

    result = {"products": []}

    for p in products:
        # Get its options
        options = frappe.db.sql("""
            SELECT name, option_id, prod_add_opt_id, option_title, master_option
            FROM `tabOPS Product Option`
            WHERE parent = %s
            LIMIT 3
        """, (p.name,), as_dict=True)

        p_data = {
            "name": p.name,
            "product_id": p.product_id,
            "product_name": p.product_name,
            "options": []
        }

        for opt in options:
            # Get its attributes
            attrs = frappe.db.sql("""
                SELECT name, attribute_id, label, master_attribute
                FROM `tabOPS Product Attribute`
                WHERE parent = %s
                LIMIT 3
            """, (opt.name,), as_dict=True)

            opt_data = {
                "name": opt.name,
                "option_id": opt.option_id,
                "prod_add_opt_id": opt.prod_add_opt_id,
                "option_title": opt.option_title,
                "master_option": opt.master_option,
                "attributes": list(attrs)
            }
            p_data["options"].append(opt_data)

        result["products"].append(p_data)

    print(json.dumps(result, indent=2, default=str))
    return result
