# copy_ops_to_home.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.copy_ops_to_home.copy_workspace

import frappe
import json

def copy_workspace():
    """Copy OPS Dashboard content to Home workspace."""

    # Get OPS Dashboard
    ops = frappe.get_doc("Workspace", "OPS Dashboard")
    print(f"OPS Dashboard title: {ops.title}")
    print(f"OPS Dashboard content length: {len(ops.content or '')}")

    # Get Home workspace
    home = frappe.get_doc("Workspace", "Home")
    print(f"Home title: {home.title}")
    print(f"Home content length: {len(home.content or '')}")

    # Copy content from OPS Dashboard to Home
    home.title = "OPS Dashboard"
    home.content = ops.content
    home.icon = ops.icon if ops.icon else home.icon

    # Copy number cards
    home.number_cards = []
    for nc in ops.number_cards or []:
        home.append("number_cards", {
            "number_card_name": nc.number_card_name
        })

    # Copy shortcuts
    home.shortcuts = []
    for sc in ops.shortcuts or []:
        home.append("shortcuts", {
            "label": sc.label,
            "type": sc.type,
            "link_to": sc.link_to,
            "doc_view": sc.doc_view,
            "color": sc.color,
            "icon": sc.icon,
            "restrict_to_domain": sc.restrict_to_domain,
            "stats_filter": sc.stats_filter,
        })

    # Copy links
    home.links = []
    for link in ops.links or []:
        home.append("links", {
            "label": link.label,
            "type": link.type,
            "link_to": link.link_to,
            "link_type": link.link_type,
            "link_count": link.link_count,
            "only_for": link.only_for,
            "dependencies": link.dependencies,
        })

    home.flags.ignore_permissions = True
    home.save()
    frappe.db.commit()

    print("\nSuccessfully copied OPS Dashboard content to Home workspace!")
    print("Users can now access OPS Dashboard at /app/home")

if __name__ == "__main__":
    copy_workspace()
