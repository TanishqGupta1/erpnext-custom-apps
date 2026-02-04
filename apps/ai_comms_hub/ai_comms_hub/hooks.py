"""
Frappe hooks for AI Communications Hub
"""

app_name = "ai_comms_hub"
app_title = "AI Communications Hub"
app_publisher = "VisualGraphX"
app_description = "AI-First, omnichannel communications platform with 80% AI automation"
app_email = "dev@visualgraphx.com"
app_license = "MIT"
app_version = "0.0.1"

# Apps
# ----
required_apps = ["frappe", "erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "ai_comms_hub",
# 		"logo": "/assets/ai_comms_hub/logo.png",
# 		"title": "AI Communications Hub",
# 		"route": "/ai_comms_hub",
# 		"has_permission": "ai_comms_hub.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------
# app_include_css = "/assets/ai_comms_hub/css/ai_comms_hub.css"
# app_include_js = "/assets/ai_comms_hub/js/ai_comms_hub.js"

# Website
# --------
# website_route_rules = [
# 	{"from_route": "/ai-chat", "to_route": "ai_comms_hub"},
# ]

# Home Pages
# ----------
# application_home_page = "ai_comms_hub"
# role_home_page = {
# 	"Customer Support": "hitl-workspace"
# }

# Generators
# ----------
# Automatically create page for each record of this DocType
# website_generators = ["Communication Hub"]

# Jinja
# -----
# jinja = {
# 	"methods": [
# 		"ai_comms_hub.utils.get_customer_context",
# 	],
# 	"filters": [
# 		"ai_comms_hub.utils.format_phone_number",
# 	]
# }

# Installation
# ------------
# before_install = "ai_comms_hub.setup.install.before_install"
# after_install = "ai_comms_hub.setup.install.after_install"

# Uninstallation
# --------------
# before_uninstall = "ai_comms_hub.setup.uninstall.before_uninstall"
# after_uninstall = "ai_comms_hub.setup.uninstall.after_uninstall"

# Integration Setup
# -----------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument
# after_app_install = "ai_comms_hub.setup.install.after_app_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config
# notification_config = "ai_comms_hub.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways
# permission_query_conditions = {
# 	"Communication Hub": "ai_comms_hub.api.permission.get_permission_query_conditions",
# }
# has_permission = {
# 	"Communication Hub": "ai_comms_hub.api.permission.has_permission",
# }

# DocType Class
# -------------
# Override standard DocType classes
# override_doctype_class = {
# 	"Customer": "ai_comms_hub.overrides.CustomerOverride"
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
	"Customer": {
		"after_insert": "ai_comms_hub.api.customer.create_default_communication_settings",
		"on_update": "ai_comms_hub.api.customer.sync_customer_to_channels",
	},
	"Communication Hub": {
		"after_insert": "ai_comms_hub.api.communication.on_hub_created",
		"on_update": "ai_comms_hub.api.communication.on_hub_updated",
		"before_submit": "ai_comms_hub.api.communication.before_hub_closed",
	},
	"Communication Message": {
		"after_insert": "ai_comms_hub.api.message.on_message_created",
		"validate": "ai_comms_hub.api.message.validate_message",
	},
	"Chatwoot FAQ": {
		"after_insert": "ai_comms_hub.services.qdrant_faq_sync.on_faq_insert",
		"on_update": "ai_comms_hub.services.qdrant_faq_sync.on_faq_update",
		"on_trash": "ai_comms_hub.services.qdrant_faq_sync.on_faq_delete",
	}
}

# Scheduled Tasks
# ---------------
scheduler_events = {
	"all": [
		"ai_comms_hub.tasks.all.cleanup_old_sessions"
	],
	"hourly": [
		"ai_comms_hub.tasks.hourly.sync_pending_messages",
		"ai_comms_hub.tasks.hourly.check_conversation_timeouts"
	],
	"daily": [
		"ai_comms_hub.tasks.daily.generate_analytics_report",
		"ai_comms_hub.tasks.daily.cleanup_old_conversations",
		"ai_comms_hub.tasks.daily.sync_knowledge_base",
		"ai_comms_hub.services.qdrant_faq_sync.verify_sync_integrity"
	],
	"weekly": [
		"ai_comms_hub.tasks.weekly.generate_weekly_summary"
	],
	"monthly": [
		"ai_comms_hub.tasks.monthly.archive_old_data",
		"ai_comms_hub.tasks.monthly.generate_monthly_report"
	],
	# "cron": {
	# 	"*/5 * * * *": [
	# 		"ai_comms_hub.tasks.check_hitl_queue"
	# 	]
	# }
}

# Testing
# -------
# before_tests = "ai_comms_hub.setup.install.before_tests"

# Overriding Methods
# ------------------
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ai_comms_hub.event.get_events"
# }

# Each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Customer": "ai_comms_hub.customer.get_dashboard_data"
# }

# Exempt linked doctypes from being automatically cancelled
# ------------------------------------------
# auto_cancel_exempted_doctypes = ["Communication Hub"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------
# ignore_links_on_delete = ["Communication Message"]

# Request Events
# --------------
# before_request = ["ai_comms_hub.utils.before_request"]
# after_request = ["ai_comms_hub.utils.after_request"]

# Job Events
# ----------
# before_job = ["ai_comms_hub.utils.before_job"]
# after_job = ["ai_comms_hub.utils.after_job"]

# User Data Protection
# --------------------
# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# ]

# Authentication and authorization
# --------------------------------
# auth_hooks = [
# 	"ai_comms_hub.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
