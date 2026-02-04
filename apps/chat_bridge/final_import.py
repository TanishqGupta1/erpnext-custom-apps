import frappe

# Remove problematic apps from Installed Applications
print("Removing problematic apps from Installed Applications...")
installed = frappe.get_single('Installed Applications')
apps_list = [a.app_name for a in installed.installed_applications]
print(f"Current apps: {apps_list}")

# Save original list
original = apps_list.copy()

# Remove problematic apps
installed.installed_applications = [
    {'app_name': app} for app in apps_list 
    if app not in ['frappe_search', 'next_crm']
]
installed.save(ignore_permissions=True)
frappe.db.commit()
print("Removed frappe_search and next_crm")

# Now import DocTypes
print("\nImporting DocTypes...")
from frappe.modules import import_file

doctypes = [
    ('chatwoot_bridge', 'doctype', 'chatwoot_integration_settings', 'Chatwoot Integration Settings'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_user_token', 'Chatwoot User Token'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_contact_mapping', 'Chatwoot Contact Mapping'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_conversation_mapping', 'Chatwoot Conversation Mapping'),
]

for app, module, doctype, name in doctypes:
    try:
        if not frappe.db.exists('DocType', name):
            print(f"  Importing {name}...")
            import_file(app, module, doctype, force=True)
            print(f"    ✓ {name}")
        else:
            print(f"    - {name}: Already exists")
    except Exception as e:
        print(f"    ✗ {name}: {str(e)[:80]}")

frappe.db.commit()

# Restore apps
print("\nRestoring apps...")
installed = frappe.get_single('Installed Applications')
installed.installed_applications = [{'app_name': app} for app in original]
installed.save(ignore_permissions=True)
frappe.db.commit()
print("Done!")


