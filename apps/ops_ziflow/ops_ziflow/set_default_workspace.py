# set_default_workspace.py
# Run with: bench --site erp.visualgraphx.com execute scripts.set_default_workspace.set_ops_dashboard

import frappe

def set_ops_dashboard():
    """Set OPS Dashboard as the default workspace for all users."""

    # First verify OPS Dashboard exists
    if not frappe.db.exists("Workspace", "OPS Dashboard"):
        print("ERROR: OPS Dashboard workspace not found!")
        return

    print("Setting OPS Dashboard as default workspace for all users...")

    # Get all users (excluding Guest and Administrator)
    users = frappe.get_all("User",
        filters={"enabled": 1, "name": ["not in", ["Guest"]]},
        pluck="name"
    )

    updated = 0
    for user in users:
        frappe.db.set_value("User", user, "default_workspace", "OPS Dashboard", update_modified=False)
        updated += 1
        print(f"  Updated: {user}")

    frappe.db.commit()
    print(f"\nDone! Updated {updated} users to use OPS Dashboard as default workspace.")
    print("\nUsers may need to refresh/re-login to see the change.")

if __name__ == "__main__":
    set_ops_dashboard()
