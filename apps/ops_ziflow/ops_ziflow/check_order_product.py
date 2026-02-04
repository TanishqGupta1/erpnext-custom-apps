# check_order_product.py
import frappe

def check_fields():
    """Check OPS Order Product fields."""
    print("=== OPS Order Product ===")
    meta = frappe.get_meta('OPS Order Product')
    for field in meta.fields[:20]:
        if field.fieldtype in ['Data', 'Int', 'Link', 'Select', 'Currency', 'Float', 'Text']:
            print(f"  {field.fieldname}: {field.fieldtype} ({field.label})")

if __name__ == "__main__":
    check_fields()
