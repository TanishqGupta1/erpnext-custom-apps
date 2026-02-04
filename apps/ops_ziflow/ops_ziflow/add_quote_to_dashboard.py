# add_quote_to_dashboard.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.add_quote_to_dashboard.add_quote

import frappe

def add_quote():
    """Add OPS Quote shortcut to OPS Dashboard workspace"""

    # Try to find the OPS Dashboard workspace
    workspace_name = None
    for name in ['OPS Dashboard', 'OPS ZiFlow', 'Home']:
        if frappe.db.exists('Workspace', name):
            workspace_name = name
            break

    if not workspace_name:
        print("No suitable workspace found. Creating OPS Dashboard...")
        workspace_name = 'OPS Dashboard'

    print(f"Adding OPS Quote to workspace: {workspace_name}")

    # Get or create workspace
    if frappe.db.exists('Workspace', workspace_name):
        workspace = frappe.get_doc('Workspace', workspace_name)
    else:
        workspace = frappe.new_doc('Workspace')
        workspace.name = workspace_name
        workspace.label = 'OPS Dashboard'
        workspace.module = 'OPS Integration'
        workspace.public = 1
        workspace.type = 'Workspace'

    # Check if OPS Quote shortcut already exists
    existing_shortcuts = [s.link_to for s in workspace.shortcuts if s.link_to == 'OPS Quote']
    if existing_shortcuts:
        print("OPS Quote shortcut already exists in workspace")
    else:
        # Add OPS Quote shortcut
        workspace.append('shortcuts', {
            'label': 'OPS Quote',
            'link_to': 'OPS Quote',
            'type': 'DocType',
            'color': '#ff6b6b',
            'icon': 'file-text'
        })
        print("Added OPS Quote shortcut")

    # Check if OPS Quote link already exists
    existing_links = [l.link_to for l in workspace.links if hasattr(l, 'link_to') and l.link_to == 'OPS Quote']
    if not existing_links:
        # Find or create Sales/Quotes section
        sales_section_exists = False
        for link in workspace.links:
            if hasattr(link, 'label') and link.label in ['Sales', 'Quotes', 'OPS Quotes']:
                sales_section_exists = True
                break

        if not sales_section_exists:
            # Add section header
            workspace.append('links', {
                'type': 'Card Break',
                'label': 'Quotes'
            })

        # Add OPS Quote link
        workspace.append('links', {
            'type': 'Link',
            'link_type': 'DocType',
            'label': 'OPS Quote',
            'link_to': 'OPS Quote',
            'icon': 'file-text'
        })
        print("Added OPS Quote link to workspace")

    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"\nWorkspace '{workspace_name}' updated successfully!")
    print(f"Total shortcuts: {len(workspace.shortcuts)}")
    print(f"Total links: {len(workspace.links)}")


if __name__ == "__main__":
    add_quote()
