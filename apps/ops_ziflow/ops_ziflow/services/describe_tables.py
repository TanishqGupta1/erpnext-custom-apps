"""Describe OPS Product tables."""
import frappe

@frappe.whitelist()
def describe():
    """Get column names for product-related tables."""

    tables = [
        "tabOPS Product Option",
        "tabOPS Product Attribute",
        "tabOPS Master Option Attribute"
    ]

    result = {}
    for table in tables:
        try:
            cols = frappe.db.sql(f"DESCRIBE `{table}`", as_dict=True)
            result[table] = [c["Field"] for c in cols]
        except Exception as e:
            result[table] = str(e)

    for table, cols in result.items():
        print(f"\n{table}:")
        if isinstance(cols, list):
            for c in cols:
                print(f"  - {c}")
        else:
            print(f"  Error: {cols}")

    return result
