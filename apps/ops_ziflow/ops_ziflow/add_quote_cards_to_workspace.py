# add_quote_cards_to_workspace.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.add_quote_cards_to_workspace.add_cards

import frappe

def add_cards():
    """Add OPS Quote cards to workspace"""

    # Get all OPS Quote cards
    quote_cards = frappe.get_all('Number Card',
        filters=[['document_type', '=', 'OPS Quote']],
        fields=['name', 'label']
    )

    print(f"Found {len(quote_cards)} OPS Quote cards:")
    for c in quote_cards:
        print(f"  - {c.name}: {c.label}")

    # Cards to add (using actual names from database)
    cards_to_add = [
        'Total Quotes-1',  # Total Quotes count
        'Draft',           # Draft status
        'Pending',         # Pending status
        'Sent',            # Sent status
        'Accepted',        # Accepted status
        'Rejected',        # Rejected status
        'Quote Value',     # Sum of quote_price
        'Total Profit'     # Sum of profit_margin
    ]

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')
    existing_cards = [c.number_card_name for c in (workspace.number_cards or [])]

    print(f"\nExisting cards in workspace: {len(existing_cards)}")

    added = 0
    for card_name in cards_to_add:
        if frappe.db.exists('Number Card', card_name):
            if card_name not in existing_cards:
                workspace.append('number_cards', {
                    'number_card_name': card_name
                })
                print(f"Added: {card_name}")
                added += 1
            else:
                print(f"Already exists: {card_name}")
        else:
            print(f"Not found: {card_name}")

    if added > 0:
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"\nSaved! Workspace now has {len(workspace.number_cards)} cards")
    else:
        print("\nNo changes needed")


if __name__ == "__main__":
    add_cards()
