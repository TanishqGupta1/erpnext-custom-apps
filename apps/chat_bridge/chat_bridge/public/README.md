# Chat Bridge Public Assets

This directory contains frontend assets for the Chat Bridge app.

## Structure

- `js/` - JavaScript files for CRM integration
  - `chatwoot_conversations.js` - Conversations widget
  - `chatwoot_quick_actions.js` - Quick action utilities

## Future Vue Components

When CRM frontend is ready, Vue components will be added here:
- `ChatwootConversations.vue` - Full conversations list component
- `ChatwootConversationDetail.vue` - Conversation detail view
- `ChatwootContactCard.vue` - Contact info panel
- `ChatwootQuickActions.vue` - Quick actions component

## Usage

Include in hooks.py:
```python
app_include_js = "/assets/chat_bridge/js/chatwoot_conversations.js"
```

