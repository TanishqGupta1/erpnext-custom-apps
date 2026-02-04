# check_home.py
import frappe

def check():
    """Check workspaces and home page settings"""

    # List workspaces
    print("=== Available Workspaces ===")
    workspaces = frappe.get_all('Workspace',
        fields=['name', 'title', 'is_default'],
        order_by='name'
    )
    for ws in workspaces:
        default = " (DEFAULT)" if ws.is_default else ""
        print(f"  - {ws.name}: {ws.title}{default}")

    # Check user default
    print("\n=== Default Home Settings ===")
    default_home = frappe.db.get_value('User', 'Administrator', 'home_settings')
    print(f"Admin home_settings: {default_home}")

    # Check system settings
    print("\n=== To view OPS Dashboard ===")
    print("Navigate to: /app/ops-dashboard")


if __name__ == "__main__":
    check()
