# setup_quote_section.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.setup_quote_section.setup

import frappe
import json

def setup():
    """Setup OPS Quotes section in dashboard with cards"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    # Print current structure
    print("=== Current Workspace Structure ===")
    print(f"Number cards: {len(workspace.number_cards or [])}")
    for c in (workspace.number_cards or []):
        print(f"  - {c.number_card_name}")

    print(f"\nCharts: {len(workspace.charts or [])}")
    print(f"Shortcuts: {len(workspace.shortcuts or [])}")
    print(f"Links: {len(workspace.links or [])}")

    # Check the content field which stores the page builder content
    print(f"\nContent field type: {type(workspace.content)}")
    if workspace.content:
        print(f"Content length: {len(workspace.content)}")
        try:
            content = json.loads(workspace.content)
            print(f"Content is JSON with {len(content)} items")
            for i, item in enumerate(content[:5]):
                print(f"  [{i}] type: {item.get('type')}, data: {str(item.get('data', {}))[:100]}")
        except:
            print("Content is not JSON")

    # Get quote cards
    quote_cards = frappe.get_all('Number Card',
        filters=[['document_type', '=', 'OPS Quote']],
        fields=['name', 'label'],
        order_by='name'
    )
    print(f"\n=== OPS Quote Cards Available ===")
    for c in quote_cards:
        print(f"  - {c.name}")


def setup_v2():
    """Add OPS Quote section using page builder format"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    # Parse existing content
    content = []
    if workspace.content:
        try:
            content = json.loads(workspace.content)
        except:
            content = []

    print(f"Current content items: {len(content)}")

    # Check if OPS Quotes section already exists
    has_quote_section = False
    for item in content:
        if item.get('type') == 'header' and 'Quote' in str(item.get('data', {}).get('text', '')):
            has_quote_section = True
            break

    if has_quote_section:
        print("OPS Quotes section already exists")
        return

    # Add OPS Quotes section
    # First add a spacer
    content.append({
        'type': 'spacer',
        'data': {'height': 20}
    })

    # Add header
    content.append({
        'type': 'header',
        'data': {
            'text': 'OPS Quotes',
            'level': 4,
            'col': 12
        }
    })

    # Add number cards for quotes
    quote_cards = ['Total Quotes-1', 'Draft', 'Pending', 'Sent', 'Accepted', 'Rejected', 'Quote Value', 'Total Profit']

    for card_name in quote_cards:
        if frappe.db.exists('Number Card', card_name):
            content.append({
                'type': 'number_card',
                'data': {
                    'number_card_name': card_name,
                    'col': 3
                }
            })
            print(f"Added card: {card_name}")

    # Save
    workspace.content = json.dumps(content)
    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"\nWorkspace saved with {len(content)} content items")
    print("Done!")


if __name__ == "__main__":
    setup()
    print("\n" + "="*50 + "\n")
    setup_v2()
