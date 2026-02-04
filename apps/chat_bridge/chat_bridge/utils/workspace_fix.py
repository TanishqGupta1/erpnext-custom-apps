"""Fix workspace shortcuts"""
import frappe

@frappe.whitelist()
def fix_customer_support_workspace():
    """Remove token_status from Customer Support workspace shortcuts"""
    workspace = frappe.get_doc('Workspace', 'Customer Support')

    print(f"Workspace: {workspace.name}")
    print(f"Number of shortcuts: {len(workspace.shortcuts)}")

    # Find and fix the User Tokens shortcut
    fixed = False
    for shortcut in workspace.shortcuts:
        if shortcut.label == 'User Tokens':
            print(f"\nFound User Tokens shortcut:")
            print(f"  stats_filter before: {shortcut.stats_filter}")
            print(f"  format before: {shortcut.format}")

            if shortcut.stats_filter and 'token_status' in str(shortcut.stats_filter):
                shortcut.stats_filter = None
                shortcut.format = ''
                fixed = True
                print(f"  FIXED - Removed stats_filter and format")

    if fixed:
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "message": "Workspace updated"}
    else:
        return {"success": True, "message": "No token_status found"}
