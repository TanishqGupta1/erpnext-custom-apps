# remove_sent_card.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.remove_sent_card.remove

import frappe
import json

def remove():
    """Remove Sent card from OPS Dashboard"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    # Remove from content JSON (page builder)
    if workspace.content:
        content = json.loads(workspace.content)
        original_count = len(content)

        # Filter out the Sent number card
        content = [item for item in content if not (
            item.get('type') == 'number_card' and
            item.get('data', {}).get('number_card_name') == 'Sent'
        )]

        if len(content) < original_count:
            workspace.content = json.dumps(content)
            print(f"Removed 'Sent' card from content (was {original_count} items, now {len(content)})")
        else:
            print("'Sent' card not found in content")

    # Remove from number_cards child table if present
    cards_to_remove = []
    for card in (workspace.number_cards or []):
        if card.number_card_name == 'Sent':
            cards_to_remove.append(card)

    for card in cards_to_remove:
        workspace.number_cards.remove(card)
        print(f"Removed 'Sent' from number_cards child table")

    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print("Done!")


if __name__ == "__main__":
    remove()
