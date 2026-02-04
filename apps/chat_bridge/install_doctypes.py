#!/usr/bin/env python3
"""Script to manually install chatwoot_bridge DocTypes"""
import frappe
import json
import os

def install_doctypes():
	"""Install all chatwoot_bridge DocTypes"""
	doctypes = [
		'chatwoot_integration_settings',
		'chatwoot_user_token', 
		'chatwoot_contact_mapping',
		'chatwoot_conversation_mapping'
	]
	
	app_path = frappe.get_app_path('chatwoot_bridge')
	
	for dt_name in doctypes:
		json_path = os.path.join(app_path, 'chatwoot_bridge', 'doctype', dt_name, f'{dt_name}.json')
		
		if os.path.exists(json_path):
			with open(json_path, 'r') as f:
				dt_data = json.load(f)
			
			dt_name_full = dt_data['name']
			if not frappe.db.exists('DocType', dt_name_full):
				print(f'Creating {dt_name_full}...')
				frappe.get_doc(dt_data).insert(ignore_permissions=True)
				print(f'  ✓ Created {dt_name_full}')
			else:
				print(f'  - {dt_name_full}: Already exists')
		else:
			print(f'  ✗ File not found: {json_path}')
	
	frappe.db.commit()
	print('\n✓ All DocTypes processed')

if __name__ == '__main__':
	install_doctypes()


