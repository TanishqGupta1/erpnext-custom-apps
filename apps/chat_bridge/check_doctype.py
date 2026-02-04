#!/usr/bin/env python3
"""Check if Chatwoot Integration Settings DocType exists and is accessible"""
import frappe

# Check if DocType exists
if frappe.db.exists('DocType', 'Chatwoot Integration Settings'):
    print('✓ DocType exists')
    
    dt = frappe.get_doc('DocType', 'Chatwoot Integration Settings')
    print(f'✓ DocType loaded: {dt.name}')
    print(f'  Module: {dt.module}')
    print(f'  Custom: {dt.custom}')
    
    # Try to create a test record
    try:
        # Check if record already exists
        existing = frappe.get_all('Chatwoot Integration Settings', limit=1)
        if existing:
            print(f'✓ Record already exists: {existing[0].name}')
        else:
            print('✓ DocType is ready - no records exist yet')
            print('  You can create a new record via UI')
    except Exception as e:
        print(f'✗ Error checking records: {e}')
else:
    print('✗ DocType does not exist - needs to be imported')


