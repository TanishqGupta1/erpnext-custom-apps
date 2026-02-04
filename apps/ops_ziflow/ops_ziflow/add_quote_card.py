# add_quote_card.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.add_quote_card.add_card

import frappe

def add_card():
    """Add OPS Quote Number Card to OPS Dashboard"""

    # First, check existing workspaces
    print("=== Checking Workspaces ===")
    workspaces = frappe.get_all('Workspace', fields=['name', 'label', 'module'])
    for ws in workspaces:
        if 'OPS' in ws.name or 'OPS' in (ws.label or ''):
            print(f"  Found: {ws.name} (label: {ws.label}, module: {ws.module})")

    # Check OPS Dashboard details
    print("\n=== OPS Dashboard Details ===")
    if frappe.db.exists('Workspace', 'OPS Dashboard'):
        workspace = frappe.get_doc('Workspace', 'OPS Dashboard')
        print(f"Shortcuts: {len(workspace.shortcuts)}")
        for s in workspace.shortcuts:
            print(f"  - {s.label}: {s.link_to} ({s.type})")
        print(f"\nLinks: {len(workspace.links)}")
        for l in workspace.links:
            ltype = getattr(l, 'type', 'unknown')
            label = getattr(l, 'label', 'no label')
            link_to = getattr(l, 'link_to', '')
            print(f"  - [{ltype}] {label}: {link_to}")
    else:
        print("OPS Dashboard workspace not found!")

    # Create Number Card for OPS Quote count
    print("\n=== Creating OPS Quote Number Card ===")
    card_name = "OPS Quote Count"

    if frappe.db.exists('Number Card', card_name):
        print(f"Number Card '{card_name}' already exists, updating...")
        card = frappe.get_doc('Number Card', card_name)
    else:
        print(f"Creating new Number Card '{card_name}'...")
        card = frappe.new_doc('Number Card')
        card.name = card_name

    card.label = "Total Quotes"
    card.document_type = "OPS Quote"
    card.function = "Count"
    card.is_public = 1
    card.show_percentage_stats = 1
    card.stats_time_interval = "Monthly"
    card.color = "#ff6b6b"
    card.save(ignore_permissions=True)
    print(f"Number Card '{card_name}' saved!")

    # Create another card for Pending Quotes
    card_name2 = "OPS Pending Quotes"
    if frappe.db.exists('Number Card', card_name2):
        print(f"Number Card '{card_name2}' already exists, updating...")
        card2 = frappe.get_doc('Number Card', card_name2)
    else:
        print(f"Creating new Number Card '{card_name2}'...")
        card2 = frappe.new_doc('Number Card')
        card2.name = card_name2

    card2.label = "Pending Quotes"
    card2.document_type = "OPS Quote"
    card2.function = "Count"
    card2.is_public = 1
    card2.show_percentage_stats = 1
    card2.stats_time_interval = "Monthly"
    card2.color = "#ffa726"
    card2.filters_json = '[["OPS Quote", "quote_status", "in", ["Draft", "Pending", "Sent"]]]'
    card2.save(ignore_permissions=True)
    print(f"Number Card '{card_name2}' saved!")

    # Now add cards to OPS Dashboard
    print("\n=== Adding Cards to OPS Dashboard ===")
    if frappe.db.exists('Workspace', 'OPS Dashboard'):
        workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

        # Check existing number cards
        existing_cards = [c.number_card for c in workspace.number_cards] if workspace.number_cards else []
        print(f"Existing cards: {existing_cards}")

        # Add OPS Quote Count card if not exists
        if card_name not in existing_cards:
            workspace.append('number_cards', {
                'number_card': card_name
            })
            print(f"Added '{card_name}' to workspace")
        else:
            print(f"'{card_name}' already in workspace")

        # Add OPS Pending Quotes card if not exists
        if card_name2 not in existing_cards:
            workspace.append('number_cards', {
                'number_card': card_name2
            })
            print(f"Added '{card_name2}' to workspace")
        else:
            print(f"'{card_name2}' already in workspace")

        workspace.save(ignore_permissions=True)
        print(f"\nWorkspace saved with {len(workspace.number_cards)} number cards")

    frappe.db.commit()
    print("\n=== Done ===")


if __name__ == "__main__":
    add_card()
