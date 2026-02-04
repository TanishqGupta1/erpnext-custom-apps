# Script to disable the old Customer 360 Client Script button

import frappe


def disable_button():
    """Disable the old Customer 360 Client Script that adds buttons."""

    cs_name = frappe.db.get_value("Client Script", {"name": "Customer 360", "dt": "Customer"})

    if cs_name:
        frappe.db.set_value("Client Script", cs_name, "enabled", 0)
        frappe.db.commit()
        print(f"Disabled Client Script: {cs_name}")
    else:
        print("Client Script 'Customer 360' not found")

    frappe.clear_cache(doctype="Customer")
    print("Cache cleared. Please reload the Customer form.")


if __name__ == "__main__":
    disable_button()
