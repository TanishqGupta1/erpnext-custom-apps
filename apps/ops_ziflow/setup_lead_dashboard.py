"""Script to add Chatwoot Leads section to OPS Dashboard."""
import frappe
import json


def create_lead_number_cards():
    """Create number cards for Chatwoot Lead statistics."""
    number_cards = [
        {
            "name": "Total Chatwoot Leads",
            "label": "Total Leads",
            "document_type": "Chatwoot Lead",
            "function": "Count",
            "color": "#667eea",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly",
        },
        {
            "name": "New Chatwoot Leads",
            "label": "New Leads",
            "document_type": "Chatwoot Lead",
            "function": "Count",
            "color": "#f6ad55",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily",
            "filters_json": '[["Chatwoot Lead","status","=","New"]]',
        },
        {
            "name": "Pending Callbacks",
            "label": "Pending Callbacks",
            "document_type": "Chatwoot Lead",
            "function": "Count",
            "color": "#48bb78",
            "is_public": 1,
            "show_percentage_stats": 0,
            "filters_json": '[["Chatwoot Lead","callback_scheduled","=",1],["Chatwoot Lead","status","not in",["Won","Lost","Unqualified"]]]',
        },
        {
            "name": "Pending Quotes",
            "label": "Pending Quotes",
            "document_type": "Chatwoot Lead",
            "function": "Count",
            "color": "#e53e3e",
            "is_public": 1,
            "show_percentage_stats": 0,
            "filters_json": '[["Chatwoot Lead","quote_requested","=",1],["Chatwoot Lead","quote_sent","=",0]]',
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


def update_ops_dashboard():
    """Add Chatwoot Leads section to existing OPS Dashboard workspace."""
    if not frappe.db.exists("Workspace", "OPS Dashboard"):
        print("OPS Dashboard workspace not found. Creating it...")
        create_ops_dashboard_with_leads()
        return

    workspace = frappe.get_doc("Workspace", "OPS Dashboard")

    # Parse existing content
    try:
        content = json.loads(workspace.content) if workspace.content else []
    except json.JSONDecodeError:
        content = []

    # Check if Chatwoot Leads section already exists
    existing_ids = [item.get("id") for item in content]
    if "chatwoot_leads_header" in existing_ids:
        print("Chatwoot Leads section already exists in OPS Dashboard")
        return

    # Add Chatwoot Leads section after ZiFlow section (or at the end)
    leads_section = [
        {"id": "leads_spacer", "type": "spacer", "data": {"col": 12}},
        {"id": "chatwoot_leads_header", "type": "header", "data": {"text": "<span class=\"h5\"><b>Chatwoot Leads</b></span>", "col": 12}},
        {"id": "total_leads_card", "type": "number_card", "data": {"number_card_name": "Total Chatwoot Leads", "col": 3}},
        {"id": "new_leads_card", "type": "number_card", "data": {"number_card_name": "New Chatwoot Leads", "col": 3}},
        {"id": "pending_callbacks_card", "type": "number_card", "data": {"number_card_name": "Pending Callbacks", "col": 3}},
        {"id": "pending_quotes_card", "type": "number_card", "data": {"number_card_name": "Pending Quotes", "col": 3}},
    ]

    # Find where to insert (after ZiFlow section or at end)
    insert_index = len(content)
    for i, item in enumerate(content):
        if item.get("id") == "spacer2":  # After ZiFlow section spacer
            insert_index = i + 1
            break

    # Insert leads section
    for j, item in enumerate(leads_section):
        content.insert(insert_index + j, item)

    workspace.content = json.dumps(content)

    # Add number cards to workspace
    existing_card_names = [nc.number_card_name for nc in workspace.number_cards or []]
    lead_cards = ["Total Chatwoot Leads", "New Chatwoot Leads", "Pending Callbacks", "Pending Quotes"]

    for card_name in lead_cards:
        if card_name not in existing_card_names:
            workspace.append("number_cards", {"number_card_name": card_name})

    # Add shortcut if not exists
    existing_shortcuts = [s.label for s in workspace.shortcuts or []]
    if "Chatwoot Leads" not in existing_shortcuts:
        workspace.append("shortcuts", {
            "label": "Chatwoot Leads",
            "type": "DocType",
            "link_to": "Chatwoot Lead",
            "doc_view": "List",
            "color": "pink",
        })

    workspace.flags.ignore_permissions = True
    workspace.save(ignore_version=True)
    print("Updated OPS Dashboard with Chatwoot Leads section")


def create_ops_dashboard_with_leads():
    """Create OPS Dashboard workspace with Chatwoot Leads section included."""
    workspace = frappe.new_doc("Workspace")
    workspace.name = "OPS Dashboard"

    workspace.update({
        "app": "ops_integration",
        "label": "OPS Dashboard",
        "title": "OPS Dashboard",
        "module": "OPS Integration",
        "public": 1,
        "is_hidden": 0,
        "icon": "octicon octicon-home",
        "sequence_id": 1,
    })

    content = [
        # Header
        {"id": "main_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>OPS Dashboard</b></span>", "col": 12}},

        # Overview Cards Row (if other cards exist)
        {"id": "spacer1", "type": "spacer", "data": {"col": 12}},

        # Chatwoot Leads Section
        {"id": "chatwoot_leads_header", "type": "header", "data": {"text": "<span class=\"h5\"><b>Chatwoot Leads</b></span>", "col": 12}},
        {"id": "total_leads_card", "type": "number_card", "data": {"number_card_name": "Total Chatwoot Leads", "col": 3}},
        {"id": "new_leads_card", "type": "number_card", "data": {"number_card_name": "New Chatwoot Leads", "col": 3}},
        {"id": "pending_callbacks_card", "type": "number_card", "data": {"number_card_name": "Pending Callbacks", "col": 3}},
        {"id": "pending_quotes_card", "type": "number_card", "data": {"number_card_name": "Pending Quotes", "col": 3}},

        {"id": "spacer2", "type": "spacer", "data": {"col": 12}},

        # Quick Navigation
        {"id": "nav_header", "type": "header", "data": {"text": "<span class=\"h5\"><b>Quick Navigation</b></span>", "col": 12}},
        {"id": "leads_shortcut", "type": "shortcut", "data": {"shortcut_name": "Chatwoot Leads", "col": 3}},
    ]
    workspace.content = json.dumps(content)

    workspace.set("shortcuts", [])
    workspace.append("shortcuts", {
        "label": "Chatwoot Leads",
        "type": "DocType",
        "link_to": "Chatwoot Lead",
        "doc_view": "List",
        "color": "pink",
    })

    workspace.set("number_cards", [])
    workspace.append("number_cards", {"number_card_name": "Total Chatwoot Leads"})
    workspace.append("number_cards", {"number_card_name": "New Chatwoot Leads"})
    workspace.append("number_cards", {"number_card_name": "Pending Callbacks"})
    workspace.append("number_cards", {"number_card_name": "Pending Quotes"})

    workspace.flags.ignore_permissions = True
    workspace.insert(ignore_if_duplicate=True)
    print("Created OPS Dashboard workspace with Chatwoot Leads section")


def add_navbar_item():
    """Add Chatwoot Leads to the navbar for quick access."""
    try:
        navbar = frappe.get_single("Navbar Settings")

        existing_labels = [item.item_label for item in navbar.settings_dropdown or []]

        if "Chatwoot Leads" not in existing_labels:
            navbar.append("settings_dropdown", {
                "item_label": "Chatwoot Leads",
                "item_type": "Route",
                "route": "/app/chatwoot-lead",
                "is_standard": 0,
            })
            navbar.save(ignore_permissions=True)
            frappe.db.commit()
            print("Added 'Chatwoot Leads' to navbar")
        else:
            print("'Chatwoot Leads' already in navbar")
    except Exception as e:
        print(f"Could not update navbar: {e}")


def main():
    """Main function to set up Chatwoot Leads dashboard integration."""
    import os
    os.chdir("/home/frappe/frappe-bench")
    frappe.init(site="erp.visualgraphx.com", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()

    print("Setting up Chatwoot Leads dashboard integration...")

    # Step 1: Create number cards
    print("\n1. Creating number cards...")
    create_lead_number_cards()

    # Step 2: Update OPS Dashboard
    print("\n2. Updating OPS Dashboard workspace...")
    update_ops_dashboard()

    # Step 3: Add navbar item
    print("\n3. Adding navbar item...")
    add_navbar_item()

    frappe.db.commit()
    frappe.destroy()
    print("\nChatwoot Leads dashboard setup complete!")


if __name__ == "__main__":
    main()
