#!/bin/bash
# Comprehensive renaming script: Chatwoot → Chat

cd /e/Docker/Frappe/apps/chat_bridge/chat_bridge

echo "=== Renaming DocType Directories ==="
mv ./customer_support/doctype/chatwoot_contact_mapping ./customer_support/doctype/chat_contact_mapping
mv ./customer_support/doctype/chatwoot_conversation ./customer_support/doctype/chat_conversation
mv ./customer_support/doctype/chatwoot_conversation_label ./customer_support/doctype/chat_conversation_label
mv ./customer_support/doctype/chatwoot_conversation_mapping ./customer_support/doctype/chat_conversation_mapping
mv ./customer_support/doctype/chatwoot_integration_settings ./customer_support/doctype/chat_integration_settings
mv ./customer_support/doctype/chatwoot_message ./customer_support/doctype/chat_message
mv ./customer_support/doctype/chatwoot_user_token ./customer_support/doctype/chat_user_token
echo "✓ DocType directories renamed"

echo "=== Renaming Page Directory ==="
mv ./page/chatwoot_inbox ./page/chat_inbox
echo "✓ Page directory renamed"

echo "=== Renaming Patch Directory ==="
mv ./patches/add_chatwoot_support_shortcut ./patches/add_chat_support_shortcut
echo "✓ Patch directory renamed"

echo "=== Renaming Files in chat_contact_mapping ==="
cd ./customer_support/doctype/chat_contact_mapping
mv chatwoot_contact_mapping.json chat_contact_mapping.json 2>/dev/null || true
mv chatwoot_contact_mapping.py chat_contact_mapping.py 2>/dev/null || true

echo "=== Renaming Files in chat_conversation ==="
cd ../chat_conversation
mv chatwoot_conversation.json chat_conversation.json 2>/dev/null || true
mv chatwoot_conversation.py chat_conversation.py 2>/dev/null || true
mv chatwoot_conversation.js chat_conversation.js 2>/dev/null || true
mv chatwoot_conversation_list.js chat_conversation_list.js 2>/dev/null || true
mv test_chatwoot_conversation.py test_chat_conversation.py 2>/dev/null || true
mv sync.py sync.py  # Keep sync.py name but update contents

echo "=== Renaming Files in chat_conversation_label ==="
cd ../chat_conversation_label
mv chatwoot_conversation_label.json chat_conversation_label.json 2>/dev/null || true
mv chatwoot_conversation_label.py chat_conversation_label.py 2>/dev/null || true

echo "=== Renaming Files in chat_conversation_mapping ==="
cd ../chat_conversation_mapping
mv chatwoot_conversation_mapping.json chat_conversation_mapping.json 2>/dev/null || true
mv chatwoot_conversation_mapping.py chat_conversation_mapping.py 2>/dev/null || true

echo "=== Renaming Files in chat_integration_settings ==="
cd ../chat_integration_settings
mv chatwoot_integration_settings.json chat_integration_settings.json 2>/dev/null || true
mv chatwoot_integration_settings.py chat_integration_settings.py 2>/dev/null || true

echo "=== Renaming Files in chat_message ==="
cd ../chat_message
mv chatwoot_message.json chat_message.json 2>/dev/null || true
mv chatwoot_message.py chat_message.py 2>/dev/null || true

echo "=== Renaming Files in chat_user_token ==="
cd ../chat_user_token
mv chatwoot_user_token.json chat_user_token.json 2>/dev/null || true
mv chatwoot_user_token.py chat_user_token.py 2>/dev/null || true

echo "=== Renaming Page Files ==="
cd /e/Docker/Frappe/apps/chat_bridge/chat_bridge/page/chat_inbox
mv chatwoot_inbox.json chat_inbox.json 2>/dev/null || true
mv chatwoot_inbox.py chat_inbox.py 2>/dev/null || true
mv chatwoot_inbox.js chat_inbox.js 2>/dev/null || true
mv chatwoot_inbox.html chat_inbox.html 2>/dev/null || true
mv chatwoot_inbox.css chat_inbox.css 2>/dev/null || true

echo "=== Renaming API Files ==="
cd /e/Docker/Frappe/apps/chat_bridge/chat_bridge/api
mv chatwoot.py chat.py 2>/dev/null || true

echo "=== Renaming Public JS Files ==="
cd /e/Docker/Frappe/apps/chat_bridge/chat_bridge/public/js
mv chatwoot_inbox.js chat_inbox.js 2>/dev/null || true
mv chatwoot_conversations.js chat_conversations.js 2>/dev/null || true
mv chatwoot_quick_actions.js chat_quick_actions.js 2>/dev/null || true

echo "✓ All files and directories renamed successfully!"
