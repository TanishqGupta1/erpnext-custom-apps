#!/usr/bin/env python3
"""
Fix Chatwoot references in workspace configurations
"""
import frappe

def fix_workspace_references():
    frappe.init(site='erp.visualgraphx.com')
    frappe.connect()

    # Find Chatwoot references in Workspace Shortcuts
    shortcuts = frappe.db.sql("""
        SELECT name, label, link_to, parent
        FROM `tabWorkspace Shortcut`
        WHERE label LIKE '%Chatwoot%' OR label LIKE '%chatwoot%' OR link_to LIKE '%Chatwoot%'
    """, as_dict=True)

    print("Found Chatwoot shortcuts:")
    for s in shortcuts:
        print(f"  - {s.name}: {s.label} -> {s.link_to} (in {s.parent})")

        # Update label and link_to
        new_label = s.label.replace('Chatwoot', 'Chat').replace('chatwoot', 'chat')
        new_link_to = s.link_to.replace('Chatwoot', 'Chat').replace('chatwoot', 'chat') if s.link_to else None

        frappe.db.sql("""
            UPDATE `tabWorkspace Shortcut`
            SET label = %s, link_to = %s
            WHERE name = %s
        """, (new_label, new_link_to, s.name))
        print(f"    Updated to: {new_label} -> {new_link_to}")

    # Find Chatwoot references in Workspace Links
    links = frappe.db.sql("""
        SELECT name, label, link_to, parent
        FROM `tabWorkspace Link`
        WHERE label LIKE '%Chatwoot%' OR label LIKE '%chatwoot%' OR link_to LIKE '%Chatwoot%'
    """, as_dict=True)

    print("\nFound Chatwoot links:")
    for l in links:
        print(f"  - {l.name}: {l.label} -> {l.link_to} (in {l.parent})")

        # Update label and link_to
        new_label = l.label.replace('Chatwoot', 'Chat').replace('chatwoot', 'chat')
        new_link_to = l.link_to.replace('Chatwoot', 'Chat').replace('chatwoot', 'chat') if l.link_to else None

        frappe.db.sql("""
            UPDATE `tabWorkspace Link`
            SET label = %s, link_to = %s
            WHERE name = %s
        """, (new_label, new_link_to, l.name))
        print(f"    Updated to: {new_label} -> {new_link_to}")

    frappe.db.commit()
    print("\nAll Chatwoot references updated!")
    frappe.destroy()

if __name__ == '__main__':
    fix_workspace_references()
