# add_cards_to_workspace.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.add_cards_to_workspace.add_cards

import frappe

def add_cards():
    """Add Number Cards to OPS Dashboard workspace"""

    print("=== Adding Number Cards to OPS Dashboard ===")

    # Check existing number cards
    print("\nExisting Number Cards:")
    cards = frappe.get_all('Number Card', fields=['name', 'label', 'document_type'])
    for c in cards:
        if 'OPS' in c.name or 'Quote' in c.name:
            print(f"  - {c.name}: {c.label} ({c.document_type})")

    # Get workspace
    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    # Check workspace number_cards child table structure
    print(f"\nWorkspace number_cards count: {len(workspace.number_cards or [])}")

    # Print all attributes of first number card if exists
    if workspace.number_cards:
        first_card = workspace.number_cards[0]
        print(f"Number card attributes: {[a for a in dir(first_card) if not a.startswith('_')]}")
        # Try to get the correct field name
        for attr in ['number_card', 'number_card_name', 'label', 'name']:
            if hasattr(first_card, attr):
                val = getattr(first_card, attr)
                print(f"  {attr}: {val}")

    # Get existing card names
    existing_cards = []
    for c in (workspace.number_cards or []):
        # Try different attribute names
        card_name = getattr(c, 'number_card_name', None) or getattr(c, 'label', None) or getattr(c, 'name', None)
        if card_name:
            existing_cards.append(card_name)

    print(f"\nExisting cards in workspace: {existing_cards}")

    # Add cards
    cards_to_add = ['OPS Quote Count', 'OPS Pending Quotes']
    for card_name in cards_to_add:
        if card_name not in existing_cards:
            workspace.append('number_cards', {
                'number_card_name': card_name
            })
            print(f"Added: {card_name}")
        else:
            print(f"Already exists: {card_name}")

    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"\nFinal number_cards count: {len(workspace.number_cards)}")
    print("=== Done ===")


if __name__ == "__main__":
    add_cards()
