#!/usr/bin/env python3
"""
Cleanup script for broken Chat User Token records.
Run with: bench --site erp.visualgraphx.com execute chat_bridge.cleanup_broken_tokens.cleanup
"""
import frappe

def cleanup():
    """Delete Chat User Token records with chat_user_id = 0"""
    frappe.init(site='erp.visualgraphx.com')
    frappe.connect()

    # Find broken tokens
    broken_tokens = frappe.get_all(
        'Chat User Token',
        filters=[['chat_user_id', '=', 0]],
        fields=['name', 'user', 'chat_user_id'],
        order_by='modified desc'
    )

    print(f'\nFound {len(broken_tokens)} broken tokens with chat_user_id = 0:')
    for token in broken_tokens:
        print(f'  - {token.name}: user={token.user or "(empty)"}')

    if broken_tokens:
        print('\nDeleting broken tokens...')
        for token in broken_tokens:
            try:
                frappe.delete_doc('Chat User Token', token.name, ignore_permissions=True, force=True)
                print(f'  ✓ Deleted: {token.name}')
            except Exception as e:
                print(f'  ✗ Failed to delete {token.name}: {e}')

        frappe.db.commit()
        print('\n✓ Cleanup complete!')
    else:
        print('\n✓ No broken tokens found.')

    # Show remaining valid tokens
    valid_tokens = frappe.get_all(
        'Chat User Token',
        filters=[['chat_user_id', '>', 0]],
        fields=['name', 'user', 'chat_user_id', 'account_id'],
        order_by='modified desc'
    )

    print(f'\nRemaining valid tokens: {len(valid_tokens)}')
    for token in valid_tokens:
        print(f'  - {token.user}: Chat User ID {token.chat_user_id}, Account {token.account_id}')

    frappe.destroy()

if __name__ == "__main__":
    cleanup()
