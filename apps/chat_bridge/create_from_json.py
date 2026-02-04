#!/usr/bin/env python3
"""
Create DocTypes directly from JSON files
This is the standard Frappe way - create DocType documents from JSON
"""
import frappe
import json
import os

# Use absolute path since get_app_path might fail if app not fully installed
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

print("Creating DocTypes from JSON files...")
for dt_folder, dt_name in doctypes:
    json_path = os.path.join(app_path, 'chatwoot_bridge', 'doctype', dt_folder, f'{dt_folder}.json')
    
    if os.path.exists(json_path):
        try:
            if not frappe.db.exists('DocType', dt_name):
                print(f"  Creating {dt_name}...")
                with open(json_path, 'r') as f:
                    dt_data = json.load(f)
                
                # Create DocType document from JSON
                doc = frappe.get_doc(dt_data)
                doc.insert(ignore_permissions=True)
                print(f"    ✓ Created {dt_name}")
            else:
                print(f"    - {dt_name}: Already exists")
        except Exception as e:
            print(f"    ✗ {dt_name}: {str(e)[:150]}")
    else:
        print(f"    ✗ {dt_name}: JSON file not found at {json_path}")

frappe.db.commit()
print("\nDone!")

