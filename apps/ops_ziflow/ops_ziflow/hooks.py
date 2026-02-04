from . import __version__ as app_version

app_name = "ops_ziflow"
app_title = "OPS Sync"
app_publisher = "VisualGraphX"
app_description = "OPS integration for Orders, Proofing, and Sync services"
app_email = "dev@visualgraphx.com"
app_license = "MIT"

# Default guest home: login (prevents 404 when hitting root without auth)
home_page = "login"

# Role-based home pages (all roles go to dashboard)
role_home_page = {
    "System Manager": "ops-cluster-dashboard",
    "Sales Manager": "ops-cluster-dashboard",
    "Sales User": "ops-cluster-dashboard",
    "Administrator": "ops-cluster-dashboard",
}

# Include JS files in all pages
app_include_css = ["/assets/ops_ziflow/css/ops_sidebar.css", "/assets/ops_ziflow/css/ops_order.css"]

app_include_js = [
    "/assets/ops_ziflow/js/margin_visualizer.js",
    "/assets/ops_ziflow/js/ops_home_redirect.js",
    "/assets/ops_ziflow/js/ops_quick_nav.js"
]

# Doctype-specific JS
doctype_js = {
    "OPS Product": "public/js/ops_product_form.js",
    "Customer": "public/js/customer_360.js",
    "OPS Order": "public/js/ops_order.js"
}

# Doctype-specific CSS
doctype_css = {
    "OPS Order": "public/css/ops_order.css"
}

# Install bootstrapping
after_install = "ops_ziflow.setup.install.after_install"

# Boot session hook to set default home page
boot_session = "ops_ziflow.api.boot.set_ops_bootinfo"

# Website user home page - redirects logged-in users from / to dashboard
get_website_user_home_page = "ops_ziflow.api.boot.get_website_user_home_page"

# Fixtures to export/import
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "OPS Integration"]]},
    {"dt": "Number Card", "filters": [["name", "like", "%ZiFlow%"]]},
    {"dt": "Number Card", "filters": [["name", "=", "Orders with Pending Proofs"]]},
    {"dt": "Workspace", "filters": [["name", "=", "OPS ZiFlow"]]},
    {"dt": "Page", "filters": [["module", "=", "OPS Integration"]]},
    {"dt": "Report", "filters": [["name", "=", "Orders Pending Proofs"]]},
]

# Hook OPS Order to create/sync proofs on status changes and bidirectional sync with OnPrintShop
# Hook OPS Quote for bidirectional sync with OnPrintShop
doc_events = {
    "OPS Order": {
        "on_update": [
            "ops_ziflow.services.proof_service.handle_order_status_change",
            "ops_ziflow.services.order_sync_service.push_order_to_onprintshop",
        ],
    },
    "OPS Quote": {
        "on_update": "ops_ziflow.services.quote_sync_service.push_quote_to_onprintshop",
    }
}

# Scheduler jobs for background sync
scheduler_events = {
    "cron": {
        # Poll ZiFlow proofs every 6 hours
        "0 */6 * * *": [
            "ops_ziflow.services.sync_service.poll_pending_proofs",
        ],
        # Poll OnPrintShop quotes every 10 minutes
        "*/10 * * * *": [
            "ops_ziflow.services.quote_sync_service.poll_onprintshop_quotes",
        ],
        # Poll OnPrintShop orders every 6 hours (offset by 3 hours from proofs)
        "0 3,9,15,21 * * *": [
            "ops_ziflow.services.order_sync_service.poll_onprintshop_orders",
        ]
    }
}

# Jinja environment methods
jenv = {
    "methods": [
        "ops_ziflow.api.dashboard.get_dashboard_stats",
    ]
}
