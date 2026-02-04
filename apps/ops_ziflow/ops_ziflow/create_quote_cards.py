# create_quote_cards.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.create_quote_cards.create_cards

import frappe

def create_cards():
    """Create OPS Quote Number Cards and add to dashboard"""

    # Step 1: Create Number Cards
    print("=== Step 1: Creating Number Cards ===")

    # Card 1: Total Quotes
    card_name = "OPS Quote Count"
    if not frappe.db.exists('Number Card', card_name):
        card = frappe.get_doc({
            'doctype': 'Number Card',
            'name': card_name,
            'label': 'Total Quotes',
            'document_type': 'OPS Quote',
            'function': 'Count',
            'is_public': 1,
            'show_percentage_stats': 1,
            'stats_time_interval': 'Monthly',
            'color': '#ff6b6b'
        })
        card.insert(ignore_permissions=True)
        print(f"Created: {card_name}")
    else:
        print(f"Exists: {card_name}")

    # Card 2: Pending Quotes
    card_name2 = "OPS Pending Quotes"
    if not frappe.db.exists('Number Card', card_name2):
        card2 = frappe.get_doc({
            'doctype': 'Number Card',
            'name': card_name2,
            'label': 'Pending Quotes',
            'document_type': 'OPS Quote',
            'function': 'Count',
            'is_public': 1,
            'show_percentage_stats': 1,
            'stats_time_interval': 'Monthly',
            'color': '#ffa726',
            'filters_json': '[["OPS Quote", "quote_status", "in", ["Draft", "Pending", "Sent"]]]'
        })
        card2.insert(ignore_permissions=True)
        print(f"Created: {card_name2}")
    else:
        print(f"Exists: {card_name2}")

    # Commit the cards first
    frappe.db.commit()
    print("Cards committed to database")

    # Step 2: Verify cards exist
    print("\n=== Step 2: Verifying Cards ===")
    for name in [card_name, card_name2]:
        if frappe.db.exists('Number Card', name):
            print(f"  Verified: {name}")
        else:
            print(f"  MISSING: {name}")

    # Step 3: Add to workspace
    print("\n=== Step 3: Adding to Workspace ===")
    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    existing_cards = [c.number_card_name for c in (workspace.number_cards or [])]
    print(f"Current cards: {len(existing_cards)}")

    added = False
    for name in [card_name, card_name2]:
        if name not in existing_cards:
            workspace.append('number_cards', {
                'number_card_name': name
            })
            print(f"  Added: {name}")
            added = True
        else:
            print(f"  Already in workspace: {name}")

    if added:
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"\nWorkspace saved with {len(workspace.number_cards)} cards")
    else:
        print("\nNo changes needed")

    print("\n=== Done ===")


if __name__ == "__main__":
    create_cards()
