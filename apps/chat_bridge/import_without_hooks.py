import frappe
import json
import os

# Temporarily remove problematic apps from Installed Applications
print("Step 1: Temporarily removing problematic apps...")
installed_apps = frappe.get_single('Installed Applications')
original_apps = list(installed_apps.installed_applications)

# Remove frappe_search and next_crm temporarily
installed_apps.installed_applications = [
    app for app in installed_apps.installed_applications 
    if app.app_name not in ['frappe_search', 'next_crm']
]
installed_apps.save(ignore_permissions=True)
frappe.db.commit()
print("  ✓ Removed problematic apps temporarily")

# Add chatwoot_bridge if not present
if 'chatwoot_bridge' not in [a.app_name for a in installed_apps.installed_applications]:
    installed_apps.append('installed_applications', {'app_name': 'chatwoot_bridge'})
    installed_apps.save(ignore_permissions=True)
    frappe.db.commit()
    print("  ✓ Added chatwoot_bridge")

# Import DocTypes
print("\nStep 2: Importing DocTypes...")
app_path = '/home/frappe/frappe-bench/apps/chatwoot_bridge'

doctypes = [
    ('chatwoot_integration_settings', 'Chatwoot Integration Settings'),
    ('chatwoot_user_token', 'Chatwoot User Token'),
    ('chatwoot_contact_mapping', 'Chatwoot Contact Mapping'),
    ('chatwoot_conversation_mapping', 'Chatwoot Conversation Mapping'),
]

for dt_folder, dt_name in doctypes:
    json_path = os.path.join(app_path, 'chatwoot_bridge', 'doctype', dt_folder, f'{dt_folder}.json')
    
    if os.path.exists(json_path):
        try:
            if not frappe.db.exists('DocType', dt_name):
                print(f'  Importing {dt_name}...')
                with open(json_path, 'r') as f:
                    dt_data = json.load(f)
                
                # Insert directly without triggering hooks
                doc = frappe.get_doc(dt_data)
                doc.flags.ignore_links = True
                doc.flags.ignore_validate = True
                doc.insert(ignore_permissions=True, ignore_links=True, ignore_validate=True)
                print(f'    ✓ Created {dt_name}')
            else:
                print(f'    - {dt_name}: Already exists')
        except Exception as e:
            print(f'    ✗ Error: {str(e)[:100]}')
    else:
        print(f'    ✗ File not found: {json_path}')

frappe.db.commit()

# Restore original apps
print("\nStep 3: Restoring original apps...")
installed_apps = frappe.get_single('Installed Applications')
installed_apps.installed_applications = original_apps
installed_apps.save(ignore_permissions=True)
frappe.db.commit()
print("  ✓ Restored original apps")

print("\n✓ Installation complete!")


