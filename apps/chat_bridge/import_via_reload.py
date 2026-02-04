#!/usr/bin/env python3
"""Import DocTypes using frappe.reload_doc"""
import frappe

doctypes = [
    ('chatwoot_bridge', 'doctype', 'chatwoot_integration_settings', 'Chatwoot Integration Settings'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_user_token', 'Chatwoot User Token'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_contact_mapping', 'Chatwoot Contact Mapping'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_conversation_mapping', 'Chatwoot Conversation Mapping'),
]

for app, module, doctype, name in doctypes:
    try:
        print(f'Reloading {name}...')
        frappe.reload_doc(app, module, doctype, force=True, reset_permissions=True)
        print(f'  ✓ {name} imported')
    except Exception as e:
        print(f'  ✗ Error: {e}')

frappe.db.commit()
print('\nDone!')


