#!/usr/bin/env python3
"""
Direct database import - bypasses Frappe's import system
This is a workaround when bench commands fail
"""
import frappe
import json
import os

app_path = '/home/frappe/frappe-bench/apps/chatwoot_bridge'

doctypes = [
    ('chatwoot_integration_settings', 'Chatwoot Integration Settings'),
    ('chatwoot_user_token', 'Chatwoot User Token'),
    ('chatwoot_contact_mapping', 'Chatwoot Contact Mapping'),
    ('chatwoot_conversation_mapping', 'Chatwoot Conversation Mapping'),
]

# Disable hooks temporarily
frappe.flags.in_import = True
frappe.flags.in_install = True
frappe.flags.in_migrate = True

print("Importing DocTypes directly to database...")
for dt_folder, dt_name in doctypes:
    json_path = os.path.join(app_path, 'chatwoot_bridge', 'doctype', dt_folder, f'{dt_folder}.json')
    
    if os.path.exists(json_path):
        try:
            if not frappe.db.exists('DocType', dt_name):
                print(f"  Creating {dt_name}...")
                with open(json_path, 'r') as f:
                    dt_data = json.load(f)
                
                # Insert with flags to skip hooks
                doc = frappe.get_doc(dt_data)
                doc.flags.ignore_links = True
                doc.flags.ignore_validate = True
                doc.flags.ignore_permissions = True
                doc.insert(ignore_permissions=True, ignore_links=True, ignore_validate=True)
                frappe.db.commit()
                print(f"    ✓ Created {dt_name}")
            else:
                print(f"    - {dt_name}: Already exists")
        except Exception as e:
            print(f"    ✗ {dt_name}: {str(e)[:150]}")
    else:
        print(f"    ✗ {dt_name}: File not found")

# Re-enable hooks
frappe.flags.in_import = False
frappe.flags.in_install = False
frappe.flags.in_migrate = False

print("\nDone!")

