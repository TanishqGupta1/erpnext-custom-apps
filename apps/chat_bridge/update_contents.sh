#!/bin/bash
# Update file contents: Chatwoot → Chat

cd /e/Docker/Frappe/apps/chat_bridge

echo "=== Updating JSON files ==="
find ./chat_bridge -type f -name "*.json" -exec sed -i 's/chatwoot_/chat_/g' {} \;
find ./chat_bridge -type f -name "*.json" -exec sed -i 's/Chatwoot /Chat /g' {} \;
find ./chat_bridge -type f -name "*.json" -exec sed -i 's/Chatwoot Conversation/Chat Conversation/g' {} \;
find ./chat_bridge -type f -name "*.json" -exec sed -i 's/Chatwoot Message/Chat Message/g' {} \;
find ./chat_bridge -type f -name "*.json" -exec sed -i 's/Chatwoot Integration/Chat Integration/g' {} \;
find ./chat_bridge -type f -name "*.json" -exec sed -i 's/"name": "Chatwoot/"name": "Chat/g' {} \;
echo "✓ JSON files updated"

echo "=== Updating Python files ==="
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/chatwoot_bridge/chat_bridge/g' {} \;
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/chatwoot_/chat_/g' {} \;
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/ChatwootConversation/ChatConversation/g' {} \;
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/ChatwootMessage/ChatMessage/g' {} \;
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/ChatwootIntegration/ChatIntegration/g' {} \;
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/Chatwoot /Chat /g' {} \;
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/"Chatwoot/"Chat/g' {} \;
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/'\''Chatwoot/'\''Chat/g' {} \;
find ./chat_bridge -type f -name "*.py" -exec sed -i 's/CHATWOOT_/CHAT_/g' {} \;
echo "✓ Python files updated"

echo "=== Updating JavaScript files ==="
find ./chat_bridge -type f -name "*.js" -exec sed -i 's/chatwoot_bridge/chat_bridge/g' {} \;
find ./chat_bridge -type f -name "*.js" -exec sed -i 's/chatwoot_/chat_/g' {} \;
find ./chat_bridge -type f -name "*.js" -exec sed -i 's/Chatwoot Conversation/Chat Conversation/g' {} \;
find ./chat_bridge -type f -name "*.js" -exec sed -i 's/Chatwoot Message/Chat Message/g' {} \;
find ./chat_bridge -type f -name "*.js" -exec sed -i 's/Chatwoot /Chat /g' {} \;
find ./chat_bridge -type f -name "*.js" -exec sed -i 's/"Chatwoot/"Chat/g' {} \;
find ./chat_bridge -type f -name "*.js" -exec sed -i 's/'\''Chatwoot/'\''Chat/g' {} \;
echo "✓ JavaScript files updated"

echo "=== Updating HTML files ==="
find ./chat_bridge -type f -name "*.html" -exec sed -i 's/chatwoot-/chat-/g' {} \;
find ./chat_bridge -type f -name "*.html" -exec sed -i 's/chatwoot_/chat_/g' {} \;
find ./chat_bridge -type f -name "*.html" -exec sed -i 's/Chatwoot/Chat/g' {} \;
echo "✓ HTML files updated"

echo "=== Updating CSS files ==="
find ./chat_bridge -type f -name "*.css" -exec sed -i 's/chatwoot-/chat-/g' {} \;
find ./chat_bridge -type f -name "*.css" -exec sed -i 's/\.chatwoot/\.chat/g' {} \;
find ./chat_bridge -type f -name "*.css" -exec sed -i 's/#chatwoot/#chat/g' {} \;
echo "✓ CSS files updated"

echo "=== Updating MD files ==="
find . -type f -name "*.md" -exec sed -i 's/chatwoot_bridge/chat_bridge/g' {} \;
find . -type f -name "*.md" -exec sed -i 's/Chatwoot Bridge/Chat Bridge/g' {} \;
find . -type f -name "*.md" -exec sed -i 's/Chatwoot integration/Chat integration/g' {} \;
echo "✓ MD files updated"

echo "✓ All file contents updated successfully!"
