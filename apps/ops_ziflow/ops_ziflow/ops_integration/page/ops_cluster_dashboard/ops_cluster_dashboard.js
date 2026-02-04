/**
 * OPS Cluster Dashboard - Modern UI
 */

frappe.pages['ops-cluster-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'OPS Dashboard',
        single_column: true
    });

    // Store data for sorting and state
    page.dashboard_data = {
        attention: {},
        sort_state: {
            'overdue-orders': { field: 'production_due_date', order: 'desc' },
            'pending-proofs': { field: 'date_purchased', order: 'desc' },
            'pending-quotes': { field: 'quote_date', order: 'desc' },
            'overdue-proofs': { field: 'deadline', order: 'desc' }
        },
        last_updated: null,
        auto_refresh_interval: null
    };

    // Add refresh button
    page.set_primary_action(__('Refresh'), function() {
        load_dashboard(page, true);
    }, 'refresh');

    // Add menu items
    page.add_menu_item(__('Orders Dashboard'), function() {
        frappe.set_route('ops-orders-dashboard');
    });
    page.add_menu_item(__('Quotes Dashboard'), function() {
        frappe.set_route('ops-quotes-dashboard');
    });
    page.add_menu_item(__('ZiFlow Dashboard'), function() {
        frappe.set_route('ziflow-dashboard');
    });
    page.add_menu_item(__('Toggle Auto-Refresh'), function() {
        toggle_auto_refresh(page);
    });

    load_dashboard(page);
    start_auto_refresh(page);
};

frappe.pages['ops-cluster-dashboard'].on_page_hide = function(wrapper) {
    if (wrapper.page && wrapper.page.dashboard_data && wrapper.page.dashboard_data.auto_refresh_interval) {
        clearInterval(wrapper.page.dashboard_data.auto_refresh_interval);
    }
};

function start_auto_refresh(page) {
    page.dashboard_data.auto_refresh_interval = setInterval(function() {
        load_dashboard(page, false);
    }, 300000);
}

function toggle_auto_refresh(page) {
    if (page.dashboard_data.auto_refresh_interval) {
        clearInterval(page.dashboard_data.auto_refresh_interval);
        page.dashboard_data.auto_refresh_interval = null;
        frappe.show_alert({ message: 'Auto-refresh disabled', indicator: 'orange' });
    } else {
        start_auto_refresh(page);
        frappe.show_alert({ message: 'Auto-refresh enabled (5 min)', indicator: 'green' });
    }
}

function load_dashboard(page, show_loading) {
    if (show_loading !== false) {
        page.main.html(get_loading_html());
    }

    Promise.all([
        frappe.call({ method: 'ops_ziflow.api.ops_dashboard.get_dashboard_overview' }),
        frappe.call({ method: 'ops_ziflow.api.ops_dashboard.get_attention_items' }),
        frappe.call({ method: 'ops_ziflow.api.ops_dashboard.get_charts_data', args: { days: 30 } }),
        frappe.call({ method: 'ops_ziflow.api.ops_dashboard.get_pipeline_summary' })
    ]).then(function(results) {
        var overview = results[0].message;
        var attention = results[1].message;
        var charts = results[2].message;
        var pipeline = results[3].message;

        page.dashboard_data.attention = attention;
        page.dashboard_data.last_updated = new Date();

        render_dashboard(page, overview, attention, charts, pipeline);

        if (show_loading !== false) {
            frappe.show_alert({ message: 'Dashboard updated', indicator: 'green' }, 2);
        }
    }).catch(function(err) {
        page.main.html(get_error_html());
        console.error('Dashboard error:', err);
    });
}

function get_loading_html() {
    return get_styles() + '<div class="ops-cluster-dashboard"><div class="ops-loading"><div class="ops-loading-spinner"></div><div class="ops-loading-text">Loading dashboard...</div></div></div>';
}

function get_error_html() {
    return get_styles() + '<div class="ops-cluster-dashboard"><div class="ops-loading"><i class="fa fa-exclamation-triangle" style="font-size: 48px; color: #ef4444;"></i><div class="ops-loading-text" style="color: #ef4444;">Error loading dashboard</div><button class="btn btn-primary btn-sm" onclick="location.reload()">Retry</button></div></div>';
}

function get_styles() {
    return '<style>' +
        ':root{--ops-primary:#6366f1;--ops-success:#10b981;--ops-warning:#f59e0b;--ops-danger:#ef4444;--ops-info:#3b82f6;--ops-purple:#8b5cf6;--ops-pink:#ec4899;--ops-dark:#1e293b;--ops-light:#f8fafc;--ops-border:#e2e8f0;--ops-shadow:0 4px 6px -1px rgba(0,0,0,0.1),0 2px 4px -1px rgba(0,0,0,0.06);--ops-shadow-lg:0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -2px rgba(0,0,0,0.05);--ops-shadow-xl:0 20px 25px -5px rgba(0,0,0,0.1),0 10px 10px -5px rgba(0,0,0,0.04)}' +
        '.ops-cluster-dashboard{background:linear-gradient(135deg,#f5f7fa 0%,#e4e8ec 100%);min-height:calc(100vh - 60px);padding:20px}' +
        '.ops-dashboard-header{margin-bottom:25px;animation:fadeInDown .5s ease}' +
        '.ops-greeting{font-size:28px;font-weight:700;color:var(--ops-dark);margin-bottom:5px}' +
        '.ops-subgreeting{color:#64748b;font-size:14px;display:flex;align-items:center;gap:15px}' +
        '.ops-last-updated{font-size:12px;color:#94a3b8}' +
        '.ops-entity-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:25px}' +
        '.ops-entity-card{background:linear-gradient(135deg,var(--card-start) 0%,var(--card-end) 100%);color:white;padding:24px;border-radius:16px;cursor:pointer;position:relative;overflow:hidden;transition:all .3s cubic-bezier(.4,0,.2,1);animation:fadeInUp .6s ease backwards}' +
        '.ops-entity-card:nth-child(1){animation-delay:.1s;--card-start:#6366f1;--card-end:#8b5cf6}' +
        '.ops-entity-card:nth-child(2){animation-delay:.2s;--card-start:#10b981;--card-end:#34d399}' +
        '.ops-entity-card:nth-child(3){animation-delay:.3s;--card-start:#ec4899;--card-end:#f472b6}' +
        '.ops-entity-card:nth-child(4){animation-delay:.4s;--card-start:#3b82f6;--card-end:#60a5fa}' +
        '.ops-entity-card:hover{transform:translateY(-8px) scale(1.02);box-shadow:var(--ops-shadow-xl)}' +
        '.ops-card-icon{position:absolute;right:20px;top:20px;font-size:48px;opacity:.2;transition:all .3s ease}' +
        '.ops-entity-card:hover .ops-card-icon{opacity:.4;transform:scale(1.1) rotate(-5deg)}' +
        '.ops-card-label{font-size:12px;opacity:.8;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px}' +
        '.ops-card-value{font-size:42px;font-weight:800;line-height:1;margin-bottom:12px}' +
        '.ops-card-stats{display:flex;gap:20px;font-size:13px;margin-bottom:10px}' +
        '.ops-card-stats span{opacity:.8}.ops-card-stats strong{font-weight:600}' +
        '.ops-card-highlight{color:#fef08a!important;font-weight:700!important}' +
        '.ops-card-revenue{font-size:20px;font-weight:700;margin-top:8px;padding-top:10px;border-top:1px solid rgba(255,255,255,.2)}' +
        '.ops-stat-panels{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-bottom:25px}' +
        '@media(max-width:768px){.ops-stat-panels{grid-template-columns:1fr}}' +
        '.ops-panel{background:white;border-radius:16px;padding:24px;box-shadow:var(--ops-shadow);transition:all .3s ease;animation:fadeIn .6s ease backwards}' +
        '.ops-panel:hover{box-shadow:var(--ops-shadow-lg)}' +
        '.ops-panel-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}' +
        '.ops-panel-title{font-size:16px;font-weight:600;color:var(--ops-dark);display:flex;align-items:center;gap:10px}' +
        '.ops-panel-title i{color:var(--ops-primary)}' +
        '.ops-panel-action{font-size:12px;color:var(--ops-primary);cursor:pointer;transition:color .2s}' +
        '.ops-panel-action:hover{color:var(--ops-purple)}' +
        '.ops-quick-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}' +
        '.ops-quick-stat{text-align:center;padding:15px;background:var(--ops-light);border-radius:12px;transition:all .3s ease}' +
        '.ops-quick-stat:hover{background:#e2e8f0;transform:translateY(-2px)}' +
        '.ops-quick-stat-value{font-size:32px;font-weight:700;line-height:1;margin-bottom:5px}' +
        '.ops-quick-stat-value.orders{color:var(--ops-primary)}' +
        '.ops-quick-stat-value.quotes{color:var(--ops-success)}' +
        '.ops-quick-stat-value.proofs{color:var(--ops-pink)}' +
        '.ops-quick-stat-value.revenue{color:var(--ops-success)}' +
        '.ops-quick-stat-label{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.5px}' +
        '.ops-pipeline{margin-bottom:15px}' +
        '.ops-pipeline-bar{display:flex;gap:4px;height:12px;margin-bottom:15px;border-radius:6px;overflow:hidden}' +
        '.ops-pipeline-segment{border-radius:6px;transition:all .3s ease;cursor:pointer;position:relative}' +
        '.ops-pipeline-segment:hover{transform:scaleY(1.3);z-index:1}' +
        '.ops-pipeline-legend{display:flex;flex-wrap:wrap;gap:12px}' +
        '.ops-pipeline-item{display:flex;align-items:center;gap:6px;font-size:12px;color:#475569}' +
        '.ops-pipeline-dot{width:10px;height:10px;border-radius:3px}' +
        '.ops-pipeline-item strong{color:var(--ops-dark)}' +
        '.ops-charts-row{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:25px}' +
        '@media(max-width:992px){.ops-charts-row{grid-template-columns:1fr}}' +
        '.ops-chart-container{min-height:280px}' +
        '.ops-status-charts{display:grid;grid-template-columns:1fr 1fr;gap:20px}' +
        '.ops-status-chart-item{text-align:center}' +
        '.ops-status-chart-label{font-size:11px;color:#64748b;margin-top:8px;text-transform:uppercase;letter-spacing:.5px}' +
        '.ops-attention-section{margin-bottom:25px}' +
        '.ops-attention-tabs{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}' +
        '.ops-attention-tab{padding:10px 18px;border-radius:25px;font-size:13px;font-weight:500;cursor:pointer;transition:all .3s ease;border:2px solid transparent;background:#e2e8f0;color:#475569;display:flex;align-items:center;gap:8px}' +
        '.ops-attention-tab:hover{background:#cbd5e1}' +
        '.ops-attention-tab.active{background:var(--ops-primary);color:white;border-color:var(--ops-primary)}' +
        '.ops-attention-tab .badge{background:rgba(255,255,255,.3);padding:2px 8px;border-radius:10px;font-size:11px;min-width:24px;text-align:center}' +
        '.ops-attention-tab.btn-default .badge{background:#94a3b8;color:white}' +
        '.ops-attention-content{max-height:400px;overflow-y:auto;border-radius:12px}' +
        '.ops-attention-pane{display:none}' +
        '.ops-attention-pane.active{display:block;animation:fadeIn .3s ease}' +
        '.ops-table{width:100%;border-collapse:separate;border-spacing:0}' +
        '.ops-table th{background:var(--ops-light);padding:12px 15px;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#64748b;font-weight:600;text-align:left;border-bottom:2px solid var(--ops-border)}' +
        '.ops-table th:first-child{border-radius:8px 0 0 0}' +
        '.ops-table th:last-child{border-radius:0 8px 0 0}' +
        '.ops-table td{padding:14px 15px;font-size:13px;border-bottom:1px solid var(--ops-border);color:#334155}' +
        '.ops-table tr:last-child td{border-bottom:none}' +
        '.ops-table tr:hover td{background:#f8fafc}' +
        '.ops-table th.sortable{cursor:pointer;user-select:none;transition:background .2s}' +
        '.ops-table th.sortable:hover{background:#e2e8f0}' +
        '.ops-table th.sortable i{margin-left:5px;opacity:.4}' +
        '.ops-table th.sortable.active i{opacity:1;color:var(--ops-primary)}' +
        '.ops-table a{color:var(--ops-primary);font-weight:500;text-decoration:none}' +
        '.ops-table a:hover{text-decoration:underline}' +
        '.ops-status-pill{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}' +
        '.ops-status-pill.danger{background:#fef2f2;color:#dc2626}' +
        '.ops-status-pill.warning{background:#fffbeb;color:#d97706}' +
        '.ops-status-pill.success{background:#f0fdf4;color:#16a34a}' +
        '.ops-status-pill.info{background:#eff6ff;color:#2563eb}' +
        '.ops-status-pill.purple{background:#faf5ff;color:#9333ea}' +
        '.ops-overdue-date{color:var(--ops-danger);font-weight:600}' +
        '.ops-quick-links{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;padding:10px 0}' +
        '.ops-quick-link{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:white;border-radius:25px;font-size:13px;color:#475569;text-decoration:none;border:1px solid var(--ops-border);transition:all .3s ease}' +
        '.ops-quick-link:hover{background:var(--ops-primary);color:white;border-color:var(--ops-primary);transform:translateY(-2px);box-shadow:var(--ops-shadow)}' +
        '.ops-quick-link i{font-size:16px}' +
        '.ops-loading{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:400px;gap:20px}' +
        '.ops-loading-spinner{width:50px;height:50px;border:4px solid #e2e8f0;border-top-color:var(--ops-primary);border-radius:50%;animation:spin 1s linear infinite}' +
        '.ops-loading-text{color:#64748b;font-size:14px}' +
        '.ops-empty-state{text-align:center;padding:40px 20px;color:#94a3b8}' +
        '.ops-empty-state i{font-size:48px;margin-bottom:15px;opacity:.5}' +
        '.ops-empty-state p{margin:0;font-size:14px}' +
        '.ops-refresh-indicator{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--ops-success);padding:4px 10px;background:#f0fdf4;border-radius:12px}' +
        '.ops-refresh-indicator i{animation:spin 2s linear infinite}' +
        '@keyframes fadeIn{from{opacity:0}to{opacity:1}}' +
        '@keyframes fadeInUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}' +
        '@keyframes fadeInDown{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}' +
        '@keyframes spin{to{transform:rotate(360deg)}}' +
        '@keyframes countUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}' +
        '.ops-animate-number{animation:countUp .5s ease forwards}' +
        '@media(max-width:576px){.ops-cluster-dashboard{padding:15px}.ops-greeting{font-size:22px}.ops-entity-card{padding:18px}.ops-card-value{font-size:32px}.ops-quick-stats{grid-template-columns:1fr}.ops-attention-tabs{overflow-x:auto;flex-wrap:nowrap;padding-bottom:10px}.ops-attention-tab{white-space:nowrap}}' +
        '</style>';
}

function get_greeting() {
    var hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
}

function get_user_first_name() {
    var full_name = frappe.session.user_fullname || frappe.session.user;
    return full_name.split(' ')[0];
}

function format_currency(value) {
    if (!value) return '$0';
    return '$' + parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function format_time_ago(date) {
    if (!date) return '';
    var seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'just now';
    var minutes = Math.floor(seconds / 60);
    if (minutes < 60) return minutes + 'm ago';
    var hours = Math.floor(minutes / 60);
    return hours + 'h ago';
}

function render_dashboard(page, overview, attention, charts, pipeline) {
    var html = get_styles() + '<div class="ops-cluster-dashboard">' +
        '<div class="ops-dashboard-header">' +
            '<div class="ops-greeting">' + get_greeting() + ', ' + get_user_first_name() + '</div>' +
            '<div class="ops-subgreeting">' +
                '<span>Here\'s your business overview</span>' +
                '<span class="ops-last-updated">Updated ' + format_time_ago(page.dashboard_data.last_updated) + '</span>' +
                (page.dashboard_data.auto_refresh_interval ? '<span class="ops-refresh-indicator"><i class="fa fa-sync-alt"></i> Auto</span>' : '') +
            '</div>' +
        '</div>' +
        '<div class="ops-entity-cards">' +
            '<div class="ops-entity-card" onclick="frappe.set_route(\'ops-orders-dashboard\')">' +
                '<i class="fa fa-shopping-cart ops-card-icon"></i>' +
                '<div class="ops-card-label">Orders</div>' +
                '<div class="ops-card-value ops-animate-number">' + overview.total_orders + '</div>' +
                '<div class="ops-card-stats">' +
                    '<div><span>Active</span> <strong>' + overview.active_orders + '</strong></div>' +
                    '<div><span>New</span> <strong>' + overview.new_orders + '</strong></div>' +
                    '<div><span>Overdue</span> <strong class="' + (overview.overdue_orders > 0 ? 'ops-card-highlight' : '') + '">' + overview.overdue_orders + '</strong></div>' +
                '</div>' +
                '<div class="ops-card-revenue">' + format_currency(overview.order_revenue) + '</div>' +
            '</div>' +
            '<div class="ops-entity-card" onclick="frappe.set_route(\'ops-quotes-dashboard\')">' +
                '<i class="fa fa-file-text-o ops-card-icon"></i>' +
                '<div class="ops-card-label">Quotes</div>' +
                '<div class="ops-card-value ops-animate-number">' + overview.total_quotes + '</div>' +
                '<div class="ops-card-stats">' +
                    '<div><span>Active</span> <strong>' + overview.active_quotes + '</strong></div>' +
                    '<div><span>Pending</span> <strong>' + overview.pending_quotes + '</strong></div>' +
                    '<div><span>Conv.</span> <strong>' + overview.conversion_rate + '%</strong></div>' +
                '</div>' +
                '<div class="ops-card-revenue">' + format_currency(overview.quote_value) + '</div>' +
            '</div>' +
            '<div class="ops-entity-card" onclick="frappe.set_route(\'ziflow-dashboard\')">' +
                '<i class="fa fa-check-circle ops-card-icon"></i>' +
                '<div class="ops-card-label">ZiFlow Proofs</div>' +
                '<div class="ops-card-value ops-animate-number">' + overview.total_proofs + '</div>' +
                '<div class="ops-card-stats">' +
                    '<div><span>Pending</span> <strong>' + overview.pending_proofs + '</strong></div>' +
                    '<div><span>Approved</span> <strong>' + overview.approved_proofs + '</strong></div>' +
                    '<div><span>Overdue</span> <strong class="' + (overview.overdue_proofs > 0 ? 'ops-card-highlight' : '') + '">' + overview.overdue_proofs + '</strong></div>' +
                '</div>' +
                '<div class="ops-card-revenue">' + (overview.total_proofs > 0 ? Math.round(overview.approved_proofs / overview.total_proofs * 100) : 0) + '% Approved</div>' +
            '</div>' +
            '<div class="ops-entity-card" onclick="frappe.set_route(\'List\', \'OPS Product\')">' +
                '<i class="fa fa-cube ops-card-icon"></i>' +
                '<div class="ops-card-label">Products</div>' +
                '<div class="ops-card-value ops-animate-number">' + overview.total_products + '</div>' +
                '<div class="ops-card-stats">' +
                    '<div><span>Active</span> <strong>' + overview.active_products + '</strong></div>' +
                    '<div><span>Customers</span> <strong>' + overview.total_customers + '</strong></div>' +
                '</div>' +
                '<div class="ops-card-revenue" style="font-size: 14px;"><a style="color: white; text-decoration: underline;">View Catalog</a></div>' +
            '</div>' +
        '</div>' +
        '<div class="ops-stat-panels">' +
            '<div class="ops-panel" style="animation-delay: 0.2s;">' +
                '<div class="ops-panel-header"><div class="ops-panel-title"><i class="fa fa-sun-o"></i> Today\'s Activity</div></div>' +
                '<div class="ops-quick-stats">' +
                    '<div class="ops-quick-stat"><div class="ops-quick-stat-value orders ops-animate-number">' + overview.orders_today + '</div><div class="ops-quick-stat-label">Orders</div></div>' +
                    '<div class="ops-quick-stat"><div class="ops-quick-stat-value quotes ops-animate-number">' + overview.quotes_today + '</div><div class="ops-quick-stat-label">Quotes</div></div>' +
                    '<div class="ops-quick-stat"><div class="ops-quick-stat-value proofs ops-animate-number">' + overview.pending_proofs + '</div><div class="ops-quick-stat-label">Pending Proofs</div></div>' +
                '</div>' +
            '</div>' +
            '<div class="ops-panel" style="animation-delay: 0.3s;">' +
                '<div class="ops-panel-header"><div class="ops-panel-title"><i class="fa fa-calendar"></i> This Month</div></div>' +
                '<div class="ops-quick-stats">' +
                    '<div class="ops-quick-stat"><div class="ops-quick-stat-value orders ops-animate-number">' + overview.orders_this_month + '</div><div class="ops-quick-stat-label">Orders</div></div>' +
                    '<div class="ops-quick-stat"><div class="ops-quick-stat-value quotes ops-animate-number">' + overview.quotes_this_month + '</div><div class="ops-quick-stat-label">Quotes</div></div>' +
                    '<div class="ops-quick-stat"><div class="ops-quick-stat-value revenue ops-animate-number">' + format_currency(overview.monthly_revenue) + '</div><div class="ops-quick-stat-label">Revenue</div></div>' +
                '</div>' +
            '</div>' +
        '</div>' +
        '<div class="ops-stat-panels">' +
            '<div class="ops-panel" style="animation-delay: 0.4s;">' +
                '<div class="ops-panel-header"><div class="ops-panel-title"><i class="fa fa-tasks"></i> Order Pipeline</div><span class="ops-panel-action" onclick="frappe.set_route(\'ops-orders-dashboard\')">View All</span></div>' +
                render_order_pipeline(pipeline.orders) +
            '</div>' +
            '<div class="ops-panel" style="animation-delay: 0.5s;">' +
                '<div class="ops-panel-header"><div class="ops-panel-title"><i class="fa fa-file-text-o"></i> Quote Pipeline</div><span class="ops-panel-action" onclick="frappe.set_route(\'ops-quotes-dashboard\')">View All</span></div>' +
                render_quote_pipeline(pipeline.quotes) +
            '</div>' +
        '</div>' +
        '<div class="ops-charts-row">' +
            '<div class="ops-panel" style="animation-delay: 0.6s;">' +
                '<div class="ops-panel-header"><div class="ops-panel-title"><i class="fa fa-line-chart"></i> Activity Timeline</div><span class="ops-panel-action">Last 30 Days</span></div>' +
                '<div class="ops-chart-container" id="activity-chart"></div>' +
            '</div>' +
            '<div class="ops-panel" style="animation-delay: 0.7s;">' +
                '<div class="ops-panel-header"><div class="ops-panel-title"><i class="fa fa-pie-chart"></i> Status Distribution</div></div>' +
                '<div class="ops-status-charts">' +
                    '<div class="ops-status-chart-item"><div id="orders-status-chart" style="height: 180px;"></div><div class="ops-status-chart-label">Orders</div></div>' +
                    '<div class="ops-status-chart-item"><div id="proofs-status-chart" style="height: 180px;"></div><div class="ops-status-chart-label">Proofs</div></div>' +
                '</div>' +
            '</div>' +
        '</div>' +
        '<div class="ops-panel ops-attention-section" style="animation-delay: 0.8s;">' +
            '<div class="ops-panel-header"><div class="ops-panel-title"><i class="fa fa-exclamation-circle"></i> Items Needing Attention</div></div>' +
            '<div class="ops-attention-tabs">' +
                '<div class="ops-attention-tab active" data-tab="overdue-orders-tab"><i class="fa fa-clock-o"></i> Overdue Orders <span class="badge">' + (attention.overdue_orders ? attention.overdue_orders.length : 0) + '</span></div>' +
                '<div class="ops-attention-tab" data-tab="pending-proofs-tab"><i class="fa fa-hourglass-half"></i> Pending Proofs <span class="badge">' + (attention.orders_pending_proofs ? attention.orders_pending_proofs.length : 0) + '</span></div>' +
                '<div class="ops-attention-tab" data-tab="pending-quotes-tab"><i class="fa fa-file-text-o"></i> Pending Quotes <span class="badge">' + (attention.pending_quotes ? attention.pending_quotes.length : 0) + '</span></div>' +
                '<div class="ops-attention-tab" data-tab="overdue-proofs-tab"><i class="fa fa-warning"></i> Overdue Proofs <span class="badge">' + (attention.overdue_proofs ? attention.overdue_proofs.length : 0) + '</span></div>' +
            '</div>' +
            '<div class="ops-attention-content">' +
                '<div class="ops-attention-pane active" id="overdue-orders-tab"></div>' +
                '<div class="ops-attention-pane" id="pending-proofs-tab"></div>' +
                '<div class="ops-attention-pane" id="pending-quotes-tab"></div>' +
                '<div class="ops-attention-pane" id="overdue-proofs-tab"></div>' +
            '</div>' +
        '</div>' +
        '<div class="ops-panel" style="animation-delay: 0.9s;">' +
            '<div class="ops-quick-links">' +
                '<a href="/app/ops-order" class="ops-quick-link"><i class="fa fa-shopping-cart"></i> All Orders</a>' +
                '<a href="/app/ops-quote" class="ops-quick-link"><i class="fa fa-file-text-o"></i> All Quotes</a>' +
                '<a href="/app/ops-ziflow-proof" class="ops-quick-link"><i class="fa fa-check-circle"></i> All Proofs</a>' +
                '<a href="/app/ops-product" class="ops-quick-link"><i class="fa fa-cube"></i> Products</a>' +
                '<a href="/app/ops-customer" class="ops-quick-link"><i class="fa fa-users"></i> Customers</a>' +
                '<a href="/app/ops-error-log" class="ops-quick-link"><i class="fa fa-bug"></i> Error Log</a>' +
            '</div>' +
        '</div>' +
    '</div>';

    page.main.html(html);

    render_overdue_orders_table(page);
    render_pending_proofs_table(page);
    render_pending_quotes_table(page);
    render_overdue_proofs_table(page);

    page.main.find('.ops-attention-tab').on('click', function() {
        var tab_id = $(this).data('tab');
        page.main.find('.ops-attention-tab').removeClass('active');
        $(this).addClass('active');
        page.main.find('.ops-attention-pane').removeClass('active');
        page.main.find('#' + tab_id).addClass('active');
    });

    setTimeout(function() {
        console.log('Rendering charts...');
        console.log('Charts data:', charts);
        console.log('Overview data:', overview);
        render_activity_chart(charts);
        render_status_charts(overview);
    }, 100);
}

function sort_data(data, field, order) {
    if (!data || !data.length) return data;
    return data.slice().sort(function(a, b) {
        var va = a[field] || '';
        var vb = b[field] || '';
        if (typeof va === 'number' && typeof vb === 'number') {
            return order === 'asc' ? va - vb : vb - va;
        }
        va = String(va).toLowerCase();
        vb = String(vb).toLowerCase();
        if (va < vb) return order === 'asc' ? -1 : 1;
        if (va > vb) return order === 'asc' ? 1 : -1;
        return 0;
    });
}

function get_sort_icon(current_field, current_order, field) {
    if (current_field === field) {
        return current_order === 'asc' ? '<i class="fa fa-sort-asc"></i>' : '<i class="fa fa-sort-desc"></i>';
    }
    return '<i class="fa fa-sort"></i>';
}

function render_overdue_orders_table(page) {
    var orders = page.dashboard_data.attention.overdue_orders || [];
    var sort = page.dashboard_data.sort_state['overdue-orders'];
    var sorted = sort_data(orders, sort.field, sort.order);

    if (!sorted || sorted.length === 0) {
        $('#overdue-orders-tab').html('<div class="ops-empty-state"><i class="fa fa-check-circle"></i><p>No overdue orders - great job!</p></div>');
        return;
    }

    var html = '<table class="ops-table"><thead><tr>' +
        '<th class="sortable ' + (sort.field === 'ops_order_id' ? 'active' : '') + '" data-field="ops_order_id" data-list="overdue-orders">Order ' + get_sort_icon(sort.field, sort.order, 'ops_order_id') + '</th>' +
        '<th class="sortable ' + (sort.field === 'customer_name' ? 'active' : '') + '" data-field="customer_name" data-list="overdue-orders">Customer ' + get_sort_icon(sort.field, sort.order, 'customer_name') + '</th>' +
        '<th class="sortable ' + (sort.field === 'order_status' ? 'active' : '') + '" data-field="order_status" data-list="overdue-orders">Status ' + get_sort_icon(sort.field, sort.order, 'order_status') + '</th>' +
        '<th class="sortable ' + (sort.field === 'production_due_date' ? 'active' : '') + '" data-field="production_due_date" data-list="overdue-orders">Due Date ' + get_sort_icon(sort.field, sort.order, 'production_due_date') + '</th>' +
        '<th class="sortable ' + (sort.field === 'order_amount' ? 'active' : '') + '" data-field="order_amount" data-list="overdue-orders">Amount ' + get_sort_icon(sort.field, sort.order, 'order_amount') + '</th>' +
        '</tr></thead><tbody>';

    sorted.forEach(function(o) {
        html += '<tr><td><a href="/app/ops-order/' + o.name + '">' + o.ops_order_id + '</a></td>' +
            '<td>' + (o.customer_name || '-') + '</td>' +
            '<td><span class="ops-status-pill danger">' + o.order_status + '</span></td>' +
            '<td class="ops-overdue-date">' + (o.production_due_date || '-') + '</td>' +
            '<td>' + format_currency(o.order_amount) + '</td></tr>';
    });
    html += '</tbody></table>';
    $('#overdue-orders-tab').html(html);
    setup_sort_handlers(page);
}

function render_pending_proofs_table(page) {
    var orders = page.dashboard_data.attention.orders_pending_proofs || [];
    var sort = page.dashboard_data.sort_state['pending-proofs'];
    var sorted = sort_data(orders, sort.field, sort.order);

    if (!sorted || sorted.length === 0) {
        $('#pending-proofs-tab').html('<div class="ops-empty-state"><i class="fa fa-check-circle"></i><p>All proofs are approved!</p></div>');
        return;
    }

    var html = '<table class="ops-table"><thead><tr>' +
        '<th class="sortable ' + (sort.field === 'ops_order_id' ? 'active' : '') + '" data-field="ops_order_id" data-list="pending-proofs">Order ' + get_sort_icon(sort.field, sort.order, 'ops_order_id') + '</th>' +
        '<th class="sortable ' + (sort.field === 'customer_name' ? 'active' : '') + '" data-field="customer_name" data-list="pending-proofs">Customer ' + get_sort_icon(sort.field, sort.order, 'customer_name') + '</th>' +
        '<th class="sortable ' + (sort.field === 'pending_proof_count' ? 'active' : '') + '" data-field="pending_proof_count" data-list="pending-proofs">Pending ' + get_sort_icon(sort.field, sort.order, 'pending_proof_count') + '</th>' +
        '<th class="sortable ' + (sort.field === 'date_purchased' ? 'active' : '') + '" data-field="date_purchased" data-list="pending-proofs">Date ' + get_sort_icon(sort.field, sort.order, 'date_purchased') + '</th>' +
        '</tr></thead><tbody>';

    sorted.forEach(function(o) {
        html += '<tr><td><a href="/app/ops-order/' + o.name + '">' + o.ops_order_id + '</a></td>' +
            '<td>' + (o.customer_name || '-') + '</td>' +
            '<td><span class="ops-status-pill warning">' + o.pending_proof_count + '</span></td>' +
            '<td>' + (o.date_purchased || '-') + '</td></tr>';
    });
    html += '</tbody></table>';
    $('#pending-proofs-tab').html(html);
    setup_sort_handlers(page);
}

function render_pending_quotes_table(page) {
    var quotes = page.dashboard_data.attention.pending_quotes || [];
    var sort = page.dashboard_data.sort_state['pending-quotes'];
    var sorted = sort_data(quotes, sort.field, sort.order);

    if (!sorted || sorted.length === 0) {
        $('#pending-quotes-tab').html('<div class="ops-empty-state"><i class="fa fa-check-circle"></i><p>No pending quotes</p></div>');
        return;
    }

    var html = '<table class="ops-table"><thead><tr>' +
        '<th class="sortable ' + (sort.field === 'quote_id' ? 'active' : '') + '" data-field="quote_id" data-list="pending-quotes">Quote ' + get_sort_icon(sort.field, sort.order, 'quote_id') + '</th>' +
        '<th class="sortable ' + (sort.field === 'customer_name' ? 'active' : '') + '" data-field="customer_name" data-list="pending-quotes">Customer ' + get_sort_icon(sort.field, sort.order, 'customer_name') + '</th>' +
        '<th class="sortable ' + (sort.field === 'quote_status' ? 'active' : '') + '" data-field="quote_status" data-list="pending-quotes">Status ' + get_sort_icon(sort.field, sort.order, 'quote_status') + '</th>' +
        '<th class="sortable ' + (sort.field === 'quote_price' ? 'active' : '') + '" data-field="quote_price" data-list="pending-quotes">Value ' + get_sort_icon(sort.field, sort.order, 'quote_price') + '</th>' +
        '<th class="sortable ' + (sort.field === 'quote_date' ? 'active' : '') + '" data-field="quote_date" data-list="pending-quotes">Date ' + get_sort_icon(sort.field, sort.order, 'quote_date') + '</th>' +
        '</tr></thead><tbody>';

    sorted.forEach(function(q) {
        var status_class = q.quote_status === 'Sent' ? 'info' : 'warning';
        html += '<tr><td><a href="/app/ops-quote/' + q.name + '">' + q.quote_id + '</a></td>' +
            '<td>' + (q.customer_name || '-') + '</td>' +
            '<td><span class="ops-status-pill ' + status_class + '">' + q.quote_status + '</span></td>' +
            '<td>' + format_currency(q.quote_price) + '</td>' +
            '<td>' + (q.quote_date || '-') + '</td></tr>';
    });
    html += '</tbody></table>';
    $('#pending-quotes-tab').html(html);
    setup_sort_handlers(page);
}

function render_overdue_proofs_table(page) {
    var proofs = page.dashboard_data.attention.overdue_proofs || [];
    var sort = page.dashboard_data.sort_state['overdue-proofs'];
    var sorted = sort_data(proofs, sort.field, sort.order);

    if (!sorted || sorted.length === 0) {
        $('#overdue-proofs-tab').html('<div class="ops-empty-state"><i class="fa fa-check-circle"></i><p>No overdue proofs</p></div>');
        return;
    }

    var html = '<table class="ops-table"><thead><tr>' +
        '<th class="sortable ' + (sort.field === 'proof_name' ? 'active' : '') + '" data-field="proof_name" data-list="overdue-proofs">Proof ' + get_sort_icon(sort.field, sort.order, 'proof_name') + '</th>' +
        '<th class="sortable ' + (sort.field === 'ops_order' ? 'active' : '') + '" data-field="ops_order" data-list="overdue-proofs">Order ' + get_sort_icon(sort.field, sort.order, 'ops_order') + '</th>' +
        '<th class="sortable ' + (sort.field === 'proof_status' ? 'active' : '') + '" data-field="proof_status" data-list="overdue-proofs">Status ' + get_sort_icon(sort.field, sort.order, 'proof_status') + '</th>' +
        '<th class="sortable ' + (sort.field === 'deadline' ? 'active' : '') + '" data-field="deadline" data-list="overdue-proofs">Deadline ' + get_sort_icon(sort.field, sort.order, 'deadline') + '</th>' +
        '</tr></thead><tbody>';

    sorted.forEach(function(p) {
        html += '<tr><td><a href="/app/ops-ziflow-proof/' + p.name + '">' + (p.proof_name || p.name) + '</a></td>' +
            '<td>' + (p.ops_order || '-') + '</td>' +
            '<td><span class="ops-status-pill warning">' + p.proof_status + '</span></td>' +
            '<td class="ops-overdue-date">' + (p.deadline || '-') + '</td></tr>';
    });
    html += '</tbody></table>';
    $('#overdue-proofs-tab').html(html);
    setup_sort_handlers(page);
}

function setup_sort_handlers(page) {
    $('.ops-table .sortable').off('click').on('click', function() {
        var field = $(this).data('field');
        var list = $(this).data('list');
        var current = page.dashboard_data.sort_state[list];

        if (current.field === field) {
            current.order = current.order === 'asc' ? 'desc' : 'asc';
        } else {
            current.field = field;
            current.order = 'desc';
        }

        if (list === 'overdue-orders') render_overdue_orders_table(page);
        else if (list === 'pending-proofs') render_pending_proofs_table(page);
        else if (list === 'pending-quotes') render_pending_quotes_table(page);
        else if (list === 'overdue-proofs') render_overdue_proofs_table(page);
    });
}

function render_order_pipeline(pipeline) {
    if (!pipeline) return '<div class="ops-empty-state"><p>No pipeline data</p></div>';

    var statuses = ['New Order', 'In Design', 'Order Processing', 'In Production', 'Ready for Fulfillment'];
    var colors = ['#94a3b8', '#f59e0b', '#3b82f6', '#8b5cf6', '#10b981'];
    var total_count = 0;

    statuses.forEach(function(s) { if (pipeline[s]) total_count += pipeline[s].count; });

    if (total_count === 0) return '<div class="ops-empty-state"><p>No orders in pipeline</p></div>';

    var html = '<div class="ops-pipeline"><div class="ops-pipeline-bar">';
    statuses.forEach(function(status, i) {
        var data = pipeline[status] || { count: 0 };
        var pct = total_count > 0 ? (data.count / total_count * 100) : 0;
        html += '<div class="ops-pipeline-segment" style="flex: ' + Math.max(pct, 3) + '; background: ' + colors[i] + ';" title="' + status + ': ' + data.count + '"></div>';
    });
    html += '</div><div class="ops-pipeline-legend">';
    statuses.forEach(function(status, i) {
        var data = pipeline[status] || { count: 0 };
        html += '<div class="ops-pipeline-item"><span class="ops-pipeline-dot" style="background: ' + colors[i] + ';"></span><span>' + status.replace('Order ', '').replace(' for ', ' ') + ': <strong>' + data.count + '</strong></span></div>';
    });
    html += '</div></div>';
    return html;
}

function render_quote_pipeline(pipeline) {
    if (!pipeline) return '<div class="ops-empty-state"><p>No pipeline data</p></div>';

    var statuses = ['Draft', 'Pending', 'Sent', 'Accepted'];
    var colors = ['#94a3b8', '#f59e0b', '#3b82f6', '#10b981'];
    var total_count = 0;

    statuses.forEach(function(s) { if (pipeline[s]) total_count += pipeline[s].count; });

    if (total_count === 0) return '<div class="ops-empty-state"><p>No quotes in pipeline</p></div>';

    var html = '<div class="ops-pipeline"><div class="ops-pipeline-bar">';
    statuses.forEach(function(status, i) {
        var data = pipeline[status] || { count: 0 };
        var pct = total_count > 0 ? (data.count / total_count * 100) : 0;
        html += '<div class="ops-pipeline-segment" style="flex: ' + Math.max(pct, 3) + '; background: ' + colors[i] + ';" title="' + status + ': ' + data.count + '"></div>';
    });
    html += '</div><div class="ops-pipeline-legend">';
    statuses.forEach(function(status, i) {
        var data = pipeline[status] || { count: 0, value: 0 };
        html += '<div class="ops-pipeline-item"><span class="ops-pipeline-dot" style="background: ' + colors[i] + ';"></span><span>' + status + ': <strong>' + data.count + '</strong> (' + format_currency(data.value) + ')</span></div>';
    });
    html += '</div></div>';
    return html;
}

function render_activity_chart(charts) {
    console.log("DEBUG: render_activity_chart called with:", JSON.stringify(charts ? {orders: charts.orders?.length, quotes: charts.quotes?.length, proofs: charts.proofs?.length} : null));
    try {
    var orders = charts.orders || [];
    var quotes = charts.quotes || [];
    var proofs = charts.proofs || [];

    var all_dates = {};
    orders.forEach(function(d) { if(d.date) all_dates[d.date] = true; });
    quotes.forEach(function(d) { if(d.date) all_dates[d.date] = true; });
    proofs.forEach(function(d) { if(d.date) all_dates[d.date] = true; });

    var labels = Object.keys(all_dates).sort();
    if (labels.length === 0) {
        $('#activity-chart').html('<div class="ops-empty-state"><i class="fa fa-chart-line"></i><p>No activity data available</p></div>');
        return;
    }

    var orders_map = {}, quotes_map = {}, proofs_map = {};
    orders.forEach(function(d) { if(d.date) orders_map[d.date] = d.count; });
    quotes.forEach(function(d) { if(d.date) quotes_map[d.date] = d.count; });
    proofs.forEach(function(d) { if(d.date) proofs_map[d.date] = d.count; });

    var orders_values = labels.map(function(d) { return orders_map[d] || 0; });
    var quotes_values = labels.map(function(d) { return quotes_map[d] || 0; });
    var proofs_values = labels.map(function(d) { return proofs_map[d] || 0; });
    var display_labels = labels.map(function(d) { return d.substring(5); });

    new frappe.Chart('#activity-chart', {
        data: {
            labels: display_labels,
            datasets: [
                { name: 'Orders', values: orders_values },
                { name: 'Quotes', values: quotes_values },
                { name: 'Proofs', values: proofs_values }
            ]
        },
        type: 'line',
        colors: ['#6366f1', '#10b981', '#ec4899'],
        height: 250,
        lineOptions: { regionFill: 1, hideDots: 0, dotSize: 4 },
        axisOptions: { xIsSeries: true }
    });
    console.log('Activity chart rendered');
    } catch(e) { console.error('Activity chart error:', e); $('#activity-chart').html('<div class="ops-empty-state"><p>Chart error</p></div>'); }
}

function render_status_charts(overview) {
    var order_statuses = overview.orders_by_status || {};
    var order_labels = Object.keys(order_statuses);
    var order_values = order_labels.map(function(s) { return order_statuses[s]; });

    if (order_labels.length > 0) {
        new frappe.Chart('#orders-status-chart', {
            data: { labels: order_labels, datasets: [{ values: order_values }] },
            type: 'pie',
            colors: ['#6366f1', '#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#94a3b8'],
            height: 180
        });
    } else {
        $('#orders-status-chart').html('<div class="ops-empty-state" style="padding: 20px;"><p>No data</p></div>');
    }

    var proof_statuses = overview.proofs_by_status || {};
    var proof_labels = Object.keys(proof_statuses);
    var proof_values = proof_labels.map(function(s) { return proof_statuses[s]; });

    if (proof_labels.length > 0) {
        new frappe.Chart('#proofs-status-chart', {
            data: { labels: proof_labels, datasets: [{ values: proof_values }] },
            type: 'pie',
            colors: ['#94a3b8', '#f59e0b', '#10b981', '#ef4444', '#3b82f6'],
            height: 180
        });
    } else {
        $('#proofs-status-chart').html('<div class="ops-empty-state" style="padding: 20px;"><p>No data</p></div>');
    }
}
