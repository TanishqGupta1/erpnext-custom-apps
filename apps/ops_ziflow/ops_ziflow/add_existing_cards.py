# add_existing_cards.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.add_existing_cards.add_cards

import frappe

def add_cards():
    """Add existing OPS Quote Number Cards to dashboard"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    existing_cards = [c.number_card_name for c in (workspace.number_cards or [])]
    print(f"Current cards in workspace: {existing_cards}")

    # Cards to add
    cards_to_add = ['Total Quotes', 'Pending Quotes-1']

    for card_name in cards_to_add:
        if frappe.db.exists('Number Card', card_name):
            if card_name not in existing_cards:
                workspace.append('number_cards', {
                    'number_card_name': card_name
                })
                print(f"Added: {card_name}")
            else:
                print(f"Already exists: {card_name}")
        else:
            print(f"Card not found: {card_name}")

    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"\nWorkspace now has {len(workspace.number_cards)} cards")
    print("Done!")


if __name__ == "__main__":
    add_cards()
