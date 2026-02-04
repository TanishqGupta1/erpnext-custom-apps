# create_ops_quote_cards.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.create_ops_quote_cards.create_cards

import frappe

def create_cards():
    """Create dedicated OPS Quote Number Cards"""

    cards_config = [
        {
            'name': 'OPS Total Quotes',
            'label': 'Total Quotes',
            'document_type': 'OPS Quote',
            'function': 'Count',
            'color': '#5e64ff',
            'filters_json': None
        },
        {
            'name': 'OPS Draft Quotes',
            'label': 'Draft',
            'document_type': 'OPS Quote',
            'function': 'Count',
            'color': '#gray',
            'filters_json': '[["OPS Quote", "quote_status", "=", "Draft"]]'
        },
        {
            'name': 'OPS Pending Quotes',
            'label': 'Pending',
            'document_type': 'OPS Quote',
            'function': 'Count',
            'color': '#ffa726',
            'filters_json': '[["OPS Quote", "quote_status", "=", "Pending"]]'
        },
        {
            'name': 'OPS Sent Quotes',
            'label': 'Sent',
            'document_type': 'OPS Quote',
            'function': 'Count',
            'color': '#29b6f6',
            'filters_json': '[["OPS Quote", "quote_status", "=", "Sent"]]'
        },
        {
            'name': 'OPS Accepted Quotes',
            'label': 'Accepted',
            'document_type': 'OPS Quote',
            'function': 'Count',
            'color': '#66bb6a',
            'filters_json': '[["OPS Quote", "quote_status", "=", "Accepted"]]'
        },
        {
            'name': 'OPS Rejected Quotes',
            'label': 'Rejected',
            'document_type': 'OPS Quote',
            'function': 'Count',
            'color': '#ef5350',
            'filters_json': '[["OPS Quote", "quote_status", "=", "Rejected"]]'
        },
        {
            'name': 'OPS Quote Revenue',
            'label': 'Quote Value',
            'document_type': 'OPS Quote',
            'function': 'Sum',
            'aggregate_function_based_on': 'quote_price',
            'color': '#ab47bc',
            'filters_json': None
        },
        {
            'name': 'OPS Quote Profit',
            'label': 'Total Profit',
            'document_type': 'OPS Quote',
            'function': 'Sum',
            'aggregate_function_based_on': 'profit_margin',
            'color': '#26a69a',
            'filters_json': None
        }
    ]

    created_cards = []

    print("=== Creating OPS Quote Number Cards ===\n")

    for config in cards_config:
        card_name = config['name']

        # Delete existing card if exists
        if frappe.db.exists('Number Card', card_name):
            frappe.delete_doc('Number Card', card_name, ignore_permissions=True)
            print(f"Deleted existing: {card_name}")

        # Create new card
        card = frappe.get_doc({
            'doctype': 'Number Card',
            'name': card_name,
            'label': config['label'],
            'type': 'Document Type',
            'document_type': config['document_type'],
            'function': config['function'],
            'aggregate_function_based_on': config.get('aggregate_function_based_on'),
            'is_public': 1,
            'show_percentage_stats': 1,
            'stats_time_interval': 'Monthly',
            'color': config['color'],
            'filters_json': config['filters_json']
        })
        card.insert(ignore_permissions=True)
        created_cards.append(card_name)
        print(f"Created: {card_name} ({config['label']})")

    frappe.db.commit()
    print(f"\n{len(created_cards)} cards created and committed")

    # Now add to workspace
    print("\n=== Adding Cards to OPS Dashboard ===\n")

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')
    existing_cards = [c.number_card_name for c in (workspace.number_cards or [])]

    added = 0
    for card_name in created_cards:
        if card_name not in existing_cards:
            workspace.append('number_cards', {
                'number_card_name': card_name
            })
            print(f"Added to workspace: {card_name}")
            added += 1
        else:
            print(f"Already in workspace: {card_name}")

    if added > 0:
        workspace.save(ignore_permissions=True)
        frappe.db.commit()

    print(f"\nWorkspace now has {len(workspace.number_cards)} total cards")
    print("\n=== Done ===")


if __name__ == "__main__":
    create_cards()
