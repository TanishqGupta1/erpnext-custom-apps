app_name = "chat_bridge"
app_title = "Chat Bridge"
app_publisher = "VisualGraphX"
app_description = "Unified Chat integration for ERPNext Support, CRM, and NextCRM"
app_email = "dev@visualgraphx.com"
app_license = "MIT"

# Required apps
required_apps = ["erpnext"]

page_js = {
	"chat-inbox": "public/js/chat_inbox.js",
}

# Add to Settings page
get_settings_link = "chat_bridge.config.docs.get_data"

# Scheduled sync every 5 minutes (if sync is enabled)
scheduler_events = {
	"cron": {
		"*/5 * * * *": [
			"chat_bridge.customer_support.doctype.chat_conversation.sync.sync_chat_conversations"
		]
	},
}

# Extend Support Workspace
extend_bootinfo = "chat_bridge.config.support.extend_bootinfo"
