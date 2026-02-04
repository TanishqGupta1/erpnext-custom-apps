#!/bin/bash
# Import all chatwoot_bridge DocTypes into ERPNext

cd /home/frappe/frappe-bench

echo "Importing Chatwoot Integration Settings..."
bench --site erp.visualgraphx.com import-doc chatwoot_bridge/doctype/chatwoot_integration_settings/chatwoot_integration_settings.json

echo "Importing Chatwoot User Token..."
bench --site erp.visualgraphx.com import-doc chatwoot_bridge/doctype/chatwoot_user_token/chatwoot_user_token.json

echo "Importing Chatwoot Contact Mapping..."
bench --site erp.visualgraphx.com import-doc chatwoot_bridge/doctype/chatwoot_contact_mapping/chatwoot_contact_mapping.json

echo "Importing Chatwoot Conversation Mapping..."
bench --site erp.visualgraphx.com import-doc chatwoot_bridge/doctype/chatwoot_conversation_mapping/chatwoot_conversation_mapping.json

echo "Running migrations..."
bench --site erp.visualgraphx.com migrate

echo "Clearing cache..."
bench --site erp.visualgraphx.com clear-cache

echo "Done! DocTypes should now be accessible."


