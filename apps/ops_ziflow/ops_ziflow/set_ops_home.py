# set_ops_home.py
import frappe

def setup():
    """Set OPS Dashboard as the default home page"""

    # List workspaces
    print("=== Available Workspaces ===")
    workspaces = frappe.db.sql("""
        SELECT name, title FROM `tabWorkspace` ORDER BY name
    """, as_dict=True)

    for ws in workspaces:
        print(f"  - {ws.name}")

    # Set OPS Dashboard as public and ensure it shows on home
    if frappe.db.exists('Workspace', 'OPS Dashboard'):
        ws = frappe.get_doc('Workspace', 'OPS Dashboard')
        ws.is_standard = 0
        ws.public = 1
        ws.save(ignore_permissions=True)
        print("\nOPS Dashboard set as public")

    frappe.db.commit()

    print("\n=== Navigation ===")
    print("The charts are on: /app/ops-dashboard")
    print("The /app/home shows the default ERPNext home workspace")
    print("\nTo make OPS Dashboard your home, use Setup > Settings > System Settings")


if __name__ == "__main__":
    setup()
