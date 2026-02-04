# add_quote_shortcut.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.add_quote_shortcut.add_shortcut

import frappe
import json

def add_shortcut():
    """Add OPS Quote to Quick Navigation section"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    # Parse content
    content = json.loads(workspace.content) if workspace.content else []

    print(f"Current content items: {len(content)}")

    # Find Quick Navigation section and add OPS Quote shortcut after it
    quick_nav_index = None
    for i, item in enumerate(content):
        if item.get('type') == 'header' and 'Quick Navigation' in str(item.get('data', {}).get('text', '')):
            quick_nav_index = i
            print(f"Found Quick Navigation at index {i}")
            break

    # Check if OPS Quote shortcut already exists
    has_quote_shortcut = False
    for item in content:
        if item.get('type') == 'shortcut' and item.get('data', {}).get('shortcut_name') == 'OPS Quote':
            has_quote_shortcut = True
            print("OPS Quote shortcut already exists")
            break

    if has_quote_shortcut:
        return

    # Find where to insert (after the last shortcut in Quick Navigation section)
    insert_index = len(content)  # Default to end
    if quick_nav_index is not None:
        # Find the last shortcut after Quick Navigation header
        for i in range(quick_nav_index + 1, len(content)):
            item = content[i]
            if item.get('type') == 'header':
                # Next section started
                insert_index = i
                break
            elif item.get('type') == 'shortcut':
                insert_index = i + 1

    # Create OPS Quote shortcut
    quote_shortcut = {
        'type': 'shortcut',
        'data': {
            'shortcut_name': 'OPS Quote',
            'col': 3
        }
    }

    # Insert at the right position
    content.insert(insert_index, quote_shortcut)
    print(f"Inserted OPS Quote shortcut at index {insert_index}")

    # Save
    workspace.content = json.dumps(content)
    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"Workspace saved with {len(content)} content items")
    print("Done!")


if __name__ == "__main__":
    add_shortcut()
