#!/usr/bin/env python3
"""Script to create Chatwoot Bridge DocTypes"""
import frappe
import json
import os

def create_doctypes():
    frappe.init(site='test-chatwoot.localhost')
    frappe.connect()
    
    doctypes = [
        'chatwoot_integration_settings',
        'chatwoot_user_token',
        'chatwoot_contact_mapping',
        'chatwoot_conversation_mapping'
    ]
    
    base_path = '/home/frappe/frappe-bench/apps/chatwoot_bridge/chatwoot_bridge/doctype'
    
    for doctype_name in doctypes:
        json_path = os.path.join(base_path, doctype_name, f'{doctype_name}.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                doc = json.load(f)
            
            # Check if DocType exists
            if not frappe.db.exists('DocType', doc['name']):
                print(f"Creating DocType: {doc['name']}")
                dt = frappe.get_doc(doc)
                dt.insert(ignore_permissions=True)
                frappe.db.commit()
                print(f"✓ Created {doc['name']}")
            else:
                print(f"DocType {doc['name']} already exists")
        else:
            print(f"File not found: {json_path}")
    
    frappe.destroy()

if __name__ == '__main__':
    create_doctypes()


