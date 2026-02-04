"""Script to set up ZiFlow dashboard components."""
import frappe

def create_number_cards():
    """Create number cards for ZiFlow dashboard."""
    # Rename existing cards to have proper names
    renames = [
        ("Total Proofs-1", "Total ZiFlow Proofs"),
        ("Pending Review-1", "Pending ZiFlow Proofs"),
        ("Approved-1", "Approved ZiFlow Proofs"),
        ("Overdue-1", "Overdue ZiFlow Proofs"),
    ]
    for old_name, new_name in renames:
        if frappe.db.exists("Number Card", old_name) and not frappe.db.exists("Number Card", new_name):
            frappe.rename_doc("Number Card", old_name, new_name, force=True)
            print(f"Renamed '{old_name}' to '{new_name}'")

    number_cards = [
        {
            "name": "Total ZiFlow Proofs",
            "label": "Total ZiFlow Proofs",
            "document_type": "OPS ZiFlow Proof",
            "function": "Count",
            "color": "#449CF0",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly",
        },
        {
            "name": "Pending ZiFlow Proofs",
            "label": "Pending ZiFlow Proofs",
            "document_type": "OPS ZiFlow Proof",
            "function": "Count",
            "color": "#ECAD4B",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly",
            "filters_json": '[["OPS ZiFlow Proof","proof_status","in",["Draft","In Review","Changes Requested"]]]',
        },
        {
            "name": "Approved ZiFlow Proofs",
            "label": "Approved ZiFlow Proofs",
            "document_type": "OPS ZiFlow Proof",
            "function": "Count",
            "color": "#48BB74",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly",
            "filters_json": '[["OPS ZiFlow Proof","proof_status","=","Approved"]]',
        },
        {
            "name": "Overdue ZiFlow Proofs",
            "label": "Overdue ZiFlow Proofs",
            "document_type": "OPS ZiFlow Proof",
            "function": "Count",
            "color": "#E53E3E",
            "is_public": 1,
            "show_percentage_stats": 0,
            "type": "Custom",
            "method": "ops_ziflow.api.dashboard.get_overdue_count",
            "filters_json": "[]",
        },
    ]

    for card_def in number_cards:
        if frappe.db.exists("Number Card", card_def["name"]):
            # Update existing card
            doc = frappe.get_doc("Number Card", card_def["name"])
            doc.update(card_def)
            doc.save(ignore_permissions=True)
            print(f"Updated Number Card: {card_def['name']}")
        else:
            try:
                doc = frappe.get_doc({"doctype": "Number Card", **card_def})
                doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
                print(f"Created Number Card: {card_def['name']}")
            except Exception as e:
                print(f"Failed to create Number Card '{card_def['name']}': {e}")

    frappe.db.commit()

def update_workspace():
    """Update OPS ZiFlow workspace with number cards."""
    import json

    workspace = None
    if frappe.db.exists("Workspace", "OPS ZiFlow"):
        workspace = frappe.get_doc("Workspace", "OPS ZiFlow")
    else:
        workspace = frappe.new_doc("Workspace")
        workspace.name = "OPS ZiFlow"

    workspace.update({
        "app": "ops_ziflow",
        "label": "OPS ZiFlow",
        "title": "ZiFlow Proofing",
        "module": "OPS Integration",
        "public": 1,
        "is_hidden": 0,
        "icon": "octicon octicon-checklist",
    })

    content = [
        {"id": "dashboard_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>ZiFlow Dashboard</b></span>", "col": 12}},
        {"id": "total_proofs_card", "type": "number_card", "data": {"number_card_name": "Total ZiFlow Proofs", "col": 3}},
        {"id": "pending_proofs_card", "type": "number_card", "data": {"number_card_name": "Pending ZiFlow Proofs", "col": 3}},
        {"id": "approved_proofs_card", "type": "number_card", "data": {"number_card_name": "Approved ZiFlow Proofs", "col": 3}},
        {"id": "overdue_proofs_card", "type": "number_card", "data": {"number_card_name": "Overdue ZiFlow Proofs", "col": 3}},
        {"id": "spacer1", "type": "spacer", "data": {"col": 12}},
        {"id": "shortcuts_header", "type": "header", "data": {"text": "<span class=\"h5\"><b>Quick Access</b></span>", "col": 12}},
        {"id": "proofs_shortcut", "type": "shortcut", "data": {"shortcut_name": "ZiFlow Proofs", "col": 4}},
        {"id": "portal_shortcut", "type": "shortcut", "data": {"shortcut_name": "ZiFlow Portal", "col": 4}},
    ]
    workspace.content = json.dumps(content)

    workspace.set("shortcuts", [])
    workspace.append("shortcuts", {
        "label": "ZiFlow Proofs",
        "type": "DocType",
        "link_to": "OPS ZiFlow Proof",
        "doc_view": "List",
        "color": "blue",
    })
    workspace.append("shortcuts", {
        "label": "ZiFlow Portal",
        "type": "URL",
        "url": "https://app.ziflow.com/#/proofs/folders",
        "color": "green",
    })

    workspace.set("number_cards", [])
    workspace.append("number_cards", {"number_card_name": "Total ZiFlow Proofs"})
    workspace.append("number_cards", {"number_card_name": "Pending ZiFlow Proofs"})
    workspace.append("number_cards", {"number_card_name": "Approved ZiFlow Proofs"})
    workspace.append("number_cards", {"number_card_name": "Overdue ZiFlow Proofs"})

    workspace.flags.ignore_permissions = True
    if workspace.is_new():
        workspace.insert(ignore_if_duplicate=True)
        print("Created Workspace: OPS ZiFlow")
    else:
        workspace.save(ignore_version=True)
        print("Updated Workspace: OPS ZiFlow")

def create_ops_dashboard():
    """Create main OPS Dashboard as the home page with navigation to ZiFlow."""
    import json

    workspace = None
    if frappe.db.exists("Workspace", "OPS Dashboard"):
        workspace = frappe.get_doc("Workspace", "OPS Dashboard")
    else:
        workspace = frappe.new_doc("Workspace")
        workspace.name = "OPS Dashboard"

    workspace.update({
        "app": "ops_ziflow",
        "label": "OPS Dashboard",
        "title": "OPS Dashboard",
        "module": "OPS Integration",
        "public": 1,
        "is_hidden": 0,
        "icon": "octicon octicon-home",
        "sequence_id": 1,  # Make it appear first
    })

    content = [
        # Header
        {"id": "main_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>OPS Dashboard</b></span>", "col": 12}},

        # Overview Cards Row
        {"id": "orders_card", "type": "number_card", "data": {"number_card_name": "Total OPS Orders", "col": 3}},
        {"id": "customers_card", "type": "number_card", "data": {"number_card_name": "Total OPS Customers", "col": 3}},
        {"id": "products_card", "type": "number_card", "data": {"number_card_name": "Total OPS Products", "col": 3}},
        {"id": "new_orders_card", "type": "number_card", "data": {"number_card_name": "New Orders", "col": 3}},

        {"id": "spacer1", "type": "spacer", "data": {"col": 12}},

        # ZiFlow Section
        {"id": "ziflow_header", "type": "header", "data": {"text": "<span class=\"h5\"><b>ZiFlow Proofing</b></span>", "col": 12}},
        {"id": "ziflow_total", "type": "number_card", "data": {"number_card_name": "Total ZiFlow Proofs", "col": 3}},
        {"id": "ziflow_pending", "type": "number_card", "data": {"number_card_name": "Pending ZiFlow Proofs", "col": 3}},
        {"id": "ziflow_approved", "type": "number_card", "data": {"number_card_name": "Approved ZiFlow Proofs", "col": 3}},
        {"id": "ziflow_overdue", "type": "number_card", "data": {"number_card_name": "Overdue ZiFlow Proofs", "col": 3}},

        {"id": "spacer2", "type": "spacer", "data": {"col": 12}},

        # Quick Navigation
        {"id": "nav_header", "type": "header", "data": {"text": "<span class=\"h5\"><b>Quick Navigation</b></span>", "col": 12}},
        {"id": "ziflow_shortcut", "type": "shortcut", "data": {"shortcut_name": "ZiFlow Dashboard", "col": 3}},
        {"id": "orders_shortcut", "type": "shortcut", "data": {"shortcut_name": "OPS Orders", "col": 3}},
        {"id": "customers_shortcut", "type": "shortcut", "data": {"shortcut_name": "OPS Customers", "col": 3}},
        {"id": "products_shortcut", "type": "shortcut", "data": {"shortcut_name": "OPS Products", "col": 3}},
    ]
    workspace.content = json.dumps(content)

    workspace.set("shortcuts", [])
    workspace.append("shortcuts", {
        "label": "ZiFlow Dashboard",
        "type": "URL",
        "url": "/app/ops-ziflow",
        "color": "blue",
    })
    workspace.append("shortcuts", {
        "label": "OPS Orders",
        "type": "DocType",
        "link_to": "OPS Order",
        "doc_view": "List",
        "color": "green",
    })
    workspace.append("shortcuts", {
        "label": "OPS Customers",
        "type": "DocType",
        "link_to": "OPS Customer",
        "doc_view": "List",
        "color": "orange",
    })
    workspace.append("shortcuts", {
        "label": "OPS Products",
        "type": "DocType",
        "link_to": "OPS Product",
        "doc_view": "List",
        "color": "purple",
    })

    workspace.set("number_cards", [])
    workspace.append("number_cards", {"number_card_name": "Total OPS Orders"})
    workspace.append("number_cards", {"number_card_name": "Total OPS Customers"})
    workspace.append("number_cards", {"number_card_name": "Total OPS Products"})
    workspace.append("number_cards", {"number_card_name": "New Orders"})
    workspace.append("number_cards", {"number_card_name": "Total ZiFlow Proofs"})
    workspace.append("number_cards", {"number_card_name": "Pending ZiFlow Proofs"})
    workspace.append("number_cards", {"number_card_name": "Approved ZiFlow Proofs"})
    workspace.append("number_cards", {"number_card_name": "Overdue ZiFlow Proofs"})

    workspace.flags.ignore_permissions = True
    if workspace.is_new():
        workspace.insert(ignore_if_duplicate=True)
        print("Created Workspace: OPS Dashboard")
    else:
        workspace.save(ignore_version=True)
        print("Updated Workspace: OPS Dashboard")


def add_navbar_items():
    """Add OPS Dashboard and ZiFlow to the navbar for quick access."""
    try:
        navbar = frappe.get_single("Navbar Settings")

        # Check if items already exist
        existing_labels = [item.item_label for item in navbar.settings_dropdown or []]

        items_to_add = [
            {
                "item_label": "OPS Dashboard",
                "item_type": "Route",
                "route": "/app/ops-dashboard",
                "is_standard": 0,
            },
            {
                "item_label": "ZiFlow Proofing",
                "item_type": "Route",
                "route": "/app/ops-ziflow",
                "is_standard": 0,
            },
        ]

        for item in items_to_add:
            if item["item_label"] not in existing_labels:
                navbar.append("settings_dropdown", item)
                print(f"Added '{item['item_label']}' to navbar")
            else:
                print(f"'{item['item_label']}' already in navbar")

        navbar.save(ignore_permissions=True)
        frappe.db.commit()
        print("Navbar updated successfully")
    except Exception as e:
        print(f"Could not update navbar: {e}")


def set_default_workspace():
    """Set OPS Dashboard as the default home page for Administrator."""
    # Update user's default workspace
    try:
        frappe.db.set_value("User", "Administrator", "default_workspace", "OPS Dashboard")
        print("Set OPS Dashboard as default workspace for Administrator")
    except Exception as e:
        print(f"Could not set default workspace: {e}")


def main():
    import os
    os.chdir("/home/frappe/frappe-bench")
    frappe.init(site="erp.visualgraphx.com", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    create_number_cards()
    update_workspace()
    create_ops_dashboard()
    add_navbar_items()
    set_default_workspace()
    frappe.db.commit()
    frappe.destroy()
    print("Dashboard setup complete!")

if __name__ == "__main__":
    main()
