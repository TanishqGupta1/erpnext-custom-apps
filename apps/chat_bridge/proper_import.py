#!/usr/bin/env python3
"""
Proper DocType import using Frappe's reload_doc function
This runs in bench console context where Frappe is properly initialized
"""
import frappe

# Import DocTypes using Frappe's reload_doc (same as bench reload-doctype)
doctypes = [
    ('chatwoot_bridge', 'doctype', 'chatwoot_integration_settings', 'Chatwoot Integration Settings'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_user_token', 'Chatwoot User Token'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_contact_mapping', 'Chatwoot Contact Mapping'),
    ('chatwoot_bridge', 'doctype', 'chatwoot_conversation_mapping', 'Chatwoot Conversation Mapping'),
]

print("Importing DocTypes...")
for app, module, doctype, name in doctypes:
    try:
        print(f"  Reloading {name}...")
        frappe.reload_doc(app, module, doctype, force=True)
        print(f"    ✓ {name}")
    except Exception as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
            print(f"    ✗ {name}: File not found - may need to create via UI first")
        else:
            print(f"    ✗ {name}: {error_msg[:100]}")

frappe.db.commit()
print("\nDone!")

