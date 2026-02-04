#!/usr/bin/env python3
"""Manually install chatwoot_bridge app and import DocTypes"""
import frappe
import json
import os

# Step 1: Add app to Installed Applications
print("Step 1: Registering app...")
installed_apps = frappe.get_single('Installed Applications')
if 'chatwoot_bridge' not in installed_apps.installed_applications:
    installed_apps.append('installed_applications', {'app_name': 'chatwoot_bridge'})
    installed_apps.save(ignore_permissions=True)
    print("  ✓ App registered")
else:
    print("  - App already registered")

frappe.db.commit()

# Step 2: Import DocTypes
print("\nStep 2: Importing DocTypes...")
try:
    app_path = frappe.get_app_path('chatwoot_bridge')
except:
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
                
                doc = frappe.get_doc(dt_data)
                doc.insert(ignore_permissions=True)
                print(f'    ✓ Created {dt_name}')
            else:
                print(f'    - {dt_name}: Already exists')
        except Exception as e:
            print(f'    ✗ Error importing {dt_name}: {e}')
    else:
        print(f'    ✗ File not found: {json_path}')

frappe.db.commit()
print("\n✓ Installation complete!")

