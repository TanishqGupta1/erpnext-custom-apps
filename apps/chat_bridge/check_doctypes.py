import frappe

doctypes = ['Chatwoot Integration Settings', 'Chatwoot User Token', 'Chatwoot Contact Mapping', 'Chatwoot Conversation Mapping']
for dt in doctypes:
    exists = frappe.db.exists('DocType', dt)
    status = 'EXISTS' if exists else 'MISSING'
    symbol = '✓' if exists else '✗'
    print(f'{symbol} {dt}: {status}')


