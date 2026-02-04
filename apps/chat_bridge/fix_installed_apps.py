import frappe

frappe.connect()
installed = frappe.get_single('Installed Applications')
print('Current apps:', [a.app_name for a in installed.installed_applications])

# Remove problematic apps
installed.installed_applications = [{'app_name': app} for app in ['frappe', 'erpnext', 'chatwoot_bridge']]
installed.save(ignore_permissions=True)
frappe.db.commit()

print('Updated apps:', [a.app_name for a in installed.installed_applications])
frappe.disconnect()

