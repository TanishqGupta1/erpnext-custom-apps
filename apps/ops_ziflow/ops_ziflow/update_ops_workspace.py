# update_ops_workspace.py
# Run with: bench --site erp.visualgraphx.com execute update_ops_workspace.update_workspace

import frappe
import json

def update_workspace():
    """Add Chatwoot Leads section to OPS Dashboard workspace."""

    # Verify all cards exist first
    cards_needed = ["Total Chatwoot Leads", "New Chatwoot Leads", "Pending Callbacks", "Pending Quotes"]
    for name in cards_needed:
        if frappe.db.exists("Number Card", name):
            print(f"Found card: {name}")
        else:
            print(f"MISSING card: {name}")
            return

    print("\nAll cards verified. Updating OPS Dashboard...")

    # Get OPS Dashboard workspace
    if not frappe.db.exists("Workspace", "OPS Dashboard"):
        print("OPS Dashboard workspace not found!")
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

    # Add Chatwoot Leads section
    leads_section = [
        {"id": "leads_spacer", "type": "spacer", "data": {"col": 12}},
        {"id": "chatwoot_leads_header", "type": "header", "data": {"text": '<span class="h5"><b>Chatwoot Leads</b></span>', "col": 12}},
        {"id": "total_leads_card", "type": "number_card", "data": {"number_card_name": "Total Chatwoot Leads", "col": 3}},
        {"id": "new_leads_card", "type": "number_card", "data": {"number_card_name": "New Chatwoot Leads", "col": 3}},
        {"id": "pending_callbacks_card", "type": "number_card", "data": {"number_card_name": "Pending Callbacks", "col": 3}},
        {"id": "pending_quotes_card", "type": "number_card", "data": {"number_card_name": "Pending Quotes", "col": 3}},
    ]

    # Append to end
    content.extend(leads_section)
    workspace.content = json.dumps(content)

    # Add number cards to workspace links
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
    frappe.db.commit()
    print("Updated OPS Dashboard with Chatwoot Leads section")
