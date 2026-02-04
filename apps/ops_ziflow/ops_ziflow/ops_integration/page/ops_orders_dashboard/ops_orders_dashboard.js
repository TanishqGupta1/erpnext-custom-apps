/**
 * OPS Orders Dashboard - Enhanced with Filters
 */

frappe.pages['ops-orders-dashboard'].on_page_load = function(wrapper) {
    // Ensure frappe-charts is loaded
    frappe.require('frappe-charts.bundle.js', function() {
        init_dashboard(wrapper);
    });
};

function init_dashboard(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Orders Dashboard',
        single_column: true
    });

    page.dashboard_data = {
        attention: {},
        filters: {
            date_range: 'this_month',
            status: 'all',
            customer: '',
            store: ''
        },
        sort_state: {
            'pending-proofs': { field: 'date_purchased', order: 'desc' },
            'overdue-orders': { field: 'production_due_date', order: 'desc' },
            'recent-orders': { field: 'date_purchased', order: 'desc' }
        },
        last_updated: null,
        auto_refresh_interval: null
    };

    page.set_primary_action(__('Refresh'), function() {
        load_dashboard(page, true);
    }, 'refresh');

    page.set_secondary_action(__('New Order'), function() {
        frappe.new_doc('OPS Order');
    });

    page.add_menu_item(__('Cluster Dashboard'), function() {
        frappe.set_route('ops-cluster-dashboard');
    });
    page.add_menu_item(__('Quotes Dashboard'), function() {
        frappe.set_route('ops-quotes-dashboard');
    });
    page.add_menu_item(__('ZiFlow Dashboard'), function() {
        frappe.set_route('ziflow-dashboard');
    });
    page.add_menu_item(__('Sync Orders'), function() {
        sync_orders(page);
    });
    page.add_menu_item(__('Export to Excel'), function() {
        export_orders(page);
    });
    page.add_menu_item(__('Toggle Auto-Refresh'), function() {
        toggle_auto_refresh(page);
    });

    load_dashboard(page);
    start_auto_refresh(page);
}

frappe.pages['ops-orders-dashboard'].on_page_hide = function(wrapper) {
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

function sync_orders(page) {
    frappe.show_alert({ message: 'Syncing orders...', indicator: 'blue' });
    frappe.call({
        method: 'ops_ziflow.services.order_sync_service.sync_recent_orders',
        args: { limit: 50 },
        callback: function(r) {
            frappe.show_alert({ message: 'Synced ' + (r.message?.synced || 0) + ' orders', indicator: 'green' });
            load_dashboard(page, true);
        }
    });
}

function export_orders(page) {
    var filters = get_date_filters(page.dashboard_data.filters.date_range);
    if (page.dashboard_data.filters.status !== 'all') {
        filters.order_status = page.dashboard_data.filters.status;
    }
    frappe.set_route('query-report', 'OPS Orders Summary', filters);
}

function get_date_filters(range) {
    var today = frappe.datetime.get_today();
    var filters = {};

    switch(range) {
        case 'today':
            filters.from_date = today;
            filters.to_date = today;
            break;
        case 'yesterday':
            var yesterday = frappe.datetime.add_days(today, -1);
            filters.from_date = yesterday;
            filters.to_date = yesterday;
            break;
        case 'this_week':
            filters.from_date = frappe.datetime.week_start();
            filters.to_date = today;
            break;
        case 'last_week':
            var last_week_end = frappe.datetime.add_days(frappe.datetime.week_start(), -1);
            filters.from_date = frappe.datetime.add_days(last_week_end, -6);
            filters.to_date = last_week_end;
            break;
        case 'this_month':
            filters.from_date = frappe.datetime.month_start();
            filters.to_date = today;
            break;
        case 'last_month':
            var last_month_end = frappe.datetime.add_days(frappe.datetime.month_start(), -1);
            filters.from_date = frappe.datetime.add_months(frappe.datetime.month_start(), -1);
            filters.to_date = last_month_end;
            break;
        case 'last_30':
            filters.from_date = frappe.datetime.add_days(today, -30);
            filters.to_date = today;
            break;
        case 'last_90':
            filters.from_date = frappe.datetime.add_days(today, -90);
            filters.to_date = today;
            break;
        case 'this_quarter':
            var month = new Date().getMonth();
            var quarter_start_month = Math.floor(month / 3) * 3;
            var quarter_start = new Date(new Date().getFullYear(), quarter_start_month, 1);
            filters.from_date = quarter_start.toISOString().split('T')[0];
            filters.to_date = today;
            break;
        case 'this_year':
            filters.from_date = new Date().getFullYear() + '-01-01';
            filters.to_date = today;
            break;
        case 'all':
        default:
            // No date filter
            break;
    }
    return filters;
}

function load_dashboard(page, show_loading) {
    if (show_loading !== false) {
        page.main.html(get_loading_html());
    }

    var date_filters = get_date_filters(page.dashboard_data.filters.date_range);
    var status_filter = page.dashboard_data.filters.status;
    var customer_filter = page.dashboard_data.filters.customer;

    Promise.all([
        frappe.call({
            method: 'ops_ziflow.api.orders_dashboard.get_orders_dashboard_stats',
            args: {
                from_date: date_filters.from_date,
                to_date: date_filters.to_date,
                status: status_filter !== 'all' ? status_filter : null,
                customer: customer_filter || null
            }
        }),
        frappe.call({
            method: 'ops_ziflow.api.orders_dashboard.get_orders_needing_attention',
            args: { limit: 20 }
        }),
        frappe.call({
            method: 'ops_ziflow.api.orders_dashboard.get_orders_timeline',
            args: { days: 30 }
        }),
        frappe.call({
            method: 'ops_ziflow.api.orders_dashboard.get_production_pipeline'
        }),
        frappe.call({
            method: 'ops_ziflow.api.orders_dashboard.get_recent_orders',
            args: {
                limit: 20,
                from_date: date_filters.from_date,
                to_date: date_filters.to_date,
                status: status_filter !== 'all' ? status_filter : null
            }
        }),
        frappe.call({
            method: 'ops_ziflow.api.orders_dashboard.get_shipment_stats'
        })
    ]).then(function(results) {
        var stats = results[0].message || {};
        var attention = results[1].message || {};
        var timeline = results[2].message || {};
        var pipeline = results[3].message || {};
        var recent = results[4].message || {};
        var shipments = results[5].message || {};

        page.dashboard_data.attention = attention;
        page.dashboard_data.recent = recent.orders || [];
        page.dashboard_data.last_updated = new Date();

        render_dashboard(page, stats, attention, timeline, pipeline, recent.orders || [], shipments);

        if (show_loading !== false) {
            frappe.show_alert({ message: 'Dashboard updated', indicator: 'green' }, 2);
        }
    }).catch(function(err) {
        page.main.html(get_error_html());
        console.error('Dashboard error:', err);
    });
}

function get_loading_html() {
    return get_styles() + '<div class="ops-orders-dashboard"><div class="ops-loading"><div class="ops-loading-spinner"></div><div class="ops-loading-text">Loading orders dashboard...</div></div></div>';
}

function get_error_html() {
    return get_styles() + '<div class="ops-orders-dashboard"><div class="ops-loading"><i class="fa fa-exclamation-triangle" style="font-size: 48px; color: #ef4444;"></i><div class="ops-loading-text" style="color: #ef4444;">Error loading dashboard</div><button class="btn btn-primary btn-sm" onclick="location.reload()">Retry</button></div></div>';
}

function get_styles() {
    return `<style>
        :root{--ops-primary:#6366f1;--ops-success:#10b981;--ops-warning:#f59e0b;--ops-danger:#ef4444;--ops-info:#3b82f6;--ops-purple:#8b5cf6;--ops-pink:#ec4899;--ops-dark:#1e293b;--ops-light:#f8fafc;--ops-border:#e2e8f0;--ops-shadow:0 4px 6px -1px rgba(0,0,0,0.1),0 2px 4px -1px rgba(0,0,0,0.06);--ops-shadow-lg:0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -2px rgba(0,0,0,0.05);--ops-shadow-xl:0 20px 25px -5px rgba(0,0,0,0.1),0 10px 10px -5px rgba(0,0,0,0.04)}
        .ops-orders-dashboard{background:linear-gradient(135deg,#f5f7fa 0%,#e4e8ec 100%);min-height:calc(100vh - 60px);padding:20px}

        /* Filter Bar */
        .ops-filter-bar{background:white;border-radius:12px;padding:15px 20px;margin-bottom:20px;box-shadow:var(--ops-shadow);display:flex;flex-wrap:wrap;gap:15px;align-items:center;animation:fadeIn .4s ease}
        .ops-filter-group{display:flex;flex-direction:column;gap:4px}
        .ops-filter-group label{font-size:10px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px}
        .ops-filter-group select,.ops-filter-group input{padding:8px 12px;border:1px solid var(--ops-border);border-radius:8px;font-size:13px;min-width:140px;background:white;transition:all .2s}
        .ops-filter-group select:focus,.ops-filter-group input:focus{outline:none;border-color:var(--ops-primary);box-shadow:0 0 0 3px rgba(99,102,241,0.1)}
        .ops-filter-group input[type="text"]{min-width:200px}
        .ops-filter-actions{margin-left:auto;display:flex;gap:10px;align-items:flex-end}
        .ops-filter-btn{padding:8px 16px;border-radius:8px;font-size:12px;font-weight:500;cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:6px;border:none}
        .ops-filter-btn.primary{background:var(--ops-primary);color:white}
        .ops-filter-btn.primary:hover{background:#4f46e5}
        .ops-filter-btn.secondary{background:#e2e8f0;color:#475569}
        .ops-filter-btn.secondary:hover{background:#cbd5e1}
        .ops-filter-btn.success{background:var(--ops-success);color:white}
        .ops-filter-btn.success:hover{background:#059669}
        .ops-quick-date-btns{display:flex;gap:5px;flex-wrap:wrap}
        .ops-quick-date-btn{padding:6px 12px;border-radius:6px;font-size:11px;font-weight:500;cursor:pointer;transition:all .2s;border:1px solid var(--ops-border);background:white;color:#475569}
        .ops-quick-date-btn:hover{border-color:var(--ops-primary);color:var(--ops-primary)}
        .ops-quick-date-btn.active{background:var(--ops-primary);color:white;border-color:var(--ops-primary)}

        .ops-dashboard-header{margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px;animation:fadeInDown .5s ease}
        .ops-greeting{font-size:26px;font-weight:700;color:var(--ops-dark)}
        .ops-subgreeting{color:#64748b;font-size:13px;display:flex;align-items:center;gap:15px;margin-top:5px}
        .ops-last-updated{font-size:11px;color:#94a3b8}
        .ops-header-stats{display:flex;gap:20px}
        .ops-header-stat{text-align:center;padding:10px 20px;background:white;border-radius:10px;box-shadow:var(--ops-shadow)}
        .ops-header-stat-value{font-size:24px;font-weight:700;color:var(--ops-primary)}
        .ops-header-stat-label{font-size:10px;color:#64748b;text-transform:uppercase}

        .ops-entity-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin-bottom:20px}
        .ops-entity-card{background:linear-gradient(135deg,var(--card-start) 0%,var(--card-end) 100%);color:white;padding:20px;border-radius:14px;cursor:pointer;position:relative;overflow:hidden;transition:all .3s cubic-bezier(.4,0,.2,1);animation:fadeInUp .6s ease backwards}
        .ops-entity-card:nth-child(1){animation-delay:.05s;--card-start:#6366f1;--card-end:#8b5cf6}
        .ops-entity-card:nth-child(2){animation-delay:.1s;--card-start:#8b5cf6;--card-end:#a855f7}
        .ops-entity-card:nth-child(3){animation-delay:.15s;--card-start:#f97316;--card-end:#fb923c}
        .ops-entity-card:nth-child(4){animation-delay:.2s;--card-start:#f59e0b;--card-end:#fbbf24}
        .ops-entity-card:nth-child(5){animation-delay:.25s;--card-start:#10b981;--card-end:#34d399}
        .ops-entity-card:nth-child(6){animation-delay:.3s;--card-start:#ef4444;--card-end:#f87171}
        .ops-entity-card:hover{transform:translateY(-5px) scale(1.02);box-shadow:var(--ops-shadow-xl)}
        .ops-card-icon{position:absolute;right:15px;top:15px;font-size:36px;opacity:.2;transition:all .3s ease}
        .ops-entity-card:hover .ops-card-icon{opacity:.4;transform:scale(1.1) rotate(-5deg)}
        .ops-card-label{font-size:10px;opacity:.85;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px}
        .ops-card-value{font-size:32px;font-weight:800;line-height:1;margin-bottom:6px}
        .ops-card-sub{font-size:11px;opacity:.75}
        .ops-card-trend{display:inline-flex;align-items:center;gap:4px;font-size:11px;padding:3px 8px;border-radius:10px;background:rgba(255,255,255,.2);margin-top:8px}
        .ops-card-trend.up{color:#86efac}
        .ops-card-trend.down{color:#fca5a5}

        .ops-stat-panels{display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-bottom:20px}
        @media(max-width:900px){.ops-stat-panels{grid-template-columns:1fr}}
        .ops-panel{background:white;border-radius:14px;padding:20px;box-shadow:var(--ops-shadow);transition:all .3s ease;animation:fadeIn .6s ease backwards}
        .ops-panel:hover{box-shadow:var(--ops-shadow-lg)}
        .ops-panel-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}
        .ops-panel-title{font-size:14px;font-weight:600;color:var(--ops-dark);display:flex;align-items:center;gap:8px}
        .ops-panel-title i{color:var(--ops-primary);font-size:16px}
        .ops-panel-action{font-size:11px;color:var(--ops-primary);cursor:pointer;transition:color .2s;display:flex;align-items:center;gap:4px}
        .ops-panel-action:hover{color:var(--ops-purple);text-decoration:underline}
        .ops-panel-badge{padding:4px 10px;border-radius:15px;font-size:10px;font-weight:600;background:var(--ops-light);color:var(--ops-primary)}

        .ops-quick-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
        .ops-quick-stat{text-align:center;padding:12px;background:var(--ops-light);border-radius:10px;transition:all .3s ease;cursor:pointer}
        .ops-quick-stat:hover{background:#e2e8f0;transform:translateY(-2px)}
        .ops-quick-stat-value{font-size:24px;font-weight:700;line-height:1;margin-bottom:4px}
        .ops-quick-stat-value.primary{color:var(--ops-primary)}
        .ops-quick-stat-value.success{color:var(--ops-success)}
        .ops-quick-stat-value.warning{color:var(--ops-warning)}
        .ops-quick-stat-value.danger{color:var(--ops-danger)}
        .ops-quick-stat-label{font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:.5px}

        .ops-pipeline{margin-bottom:10px}
        .ops-pipeline-bar{display:flex;gap:3px;height:10px;margin-bottom:12px;border-radius:5px;overflow:hidden}
        .ops-pipeline-segment{border-radius:5px;transition:all .3s ease;cursor:pointer;position:relative}
        .ops-pipeline-segment:hover{transform:scaleY(1.8);z-index:1}
        .ops-pipeline-legend{display:flex;flex-wrap:wrap;gap:8px}
        .ops-pipeline-item{display:flex;align-items:center;gap:5px;font-size:10px;color:#475569;cursor:pointer;padding:3px 6px;border-radius:5px;transition:background .2s}
        .ops-pipeline-item:hover{background:#f1f5f9}
        .ops-pipeline-dot{width:8px;height:8px;border-radius:2px}
        .ops-pipeline-item strong{color:var(--ops-dark)}

        .ops-charts-row{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px}
        @media(max-width:992px){.ops-charts-row{grid-template-columns:1fr}}
        .ops-chart-container{min-height:220px}

        .ops-attention-section{margin-bottom:20px}
        .ops-attention-tabs{display:flex;gap:8px;margin-bottom:15px;flex-wrap:wrap}
        .ops-attention-tab{padding:8px 15px;border-radius:20px;font-size:12px;font-weight:500;cursor:pointer;transition:all .3s ease;border:2px solid transparent;background:#e2e8f0;color:#475569;display:flex;align-items:center;gap:6px}
        .ops-attention-tab:hover{background:#cbd5e1}
        .ops-attention-tab.active{background:var(--ops-primary);color:white;border-color:var(--ops-primary)}
        .ops-attention-tab .badge{background:rgba(255,255,255,.3);padding:2px 7px;border-radius:8px;font-size:10px;min-width:20px;text-align:center}
        .ops-attention-tab.btn-default .badge{background:#94a3b8;color:white}
        .ops-attention-content{max-height:350px;overflow-y:auto;border-radius:10px}
        .ops-attention-pane{display:none}
        .ops-attention-pane.active{display:block;animation:fadeIn .3s ease}

        .ops-table{width:100%;border-collapse:separate;border-spacing:0}
        .ops-table th{background:var(--ops-light);padding:10px 12px;font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:#64748b;font-weight:600;text-align:left;border-bottom:2px solid var(--ops-border);position:sticky;top:0;z-index:1}
        .ops-table th:first-child{border-radius:8px 0 0 0}
        .ops-table th:last-child{border-radius:0 8px 0 0}
        .ops-table td{padding:10px 12px;font-size:12px;border-bottom:1px solid var(--ops-border);color:#334155}
        .ops-table tr:last-child td{border-bottom:none}
        .ops-table tr:hover td{background:#f8fafc}
        .ops-table th.sortable{cursor:pointer;user-select:none;transition:background .2s}
        .ops-table th.sortable:hover{background:#e2e8f0}
        .ops-table th.sortable i{margin-left:4px;opacity:.4;font-size:10px}
        .ops-table th.sortable.active i{opacity:1;color:var(--ops-primary)}
        .ops-table a{color:var(--ops-primary);font-weight:500;text-decoration:none}
        .ops-table a:hover{text-decoration:underline}
        .ops-table-actions{display:flex;gap:5px}
        .ops-table-action{width:26px;height:26px;border-radius:6px;border:1px solid var(--ops-border);background:white;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .2s;color:#64748b}
        .ops-table-action:hover{border-color:var(--ops-primary);color:var(--ops-primary);background:#f8faff}

        .ops-status-pill{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:15px;font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}
        .ops-status-pill.danger{background:#fef2f2;color:#dc2626}
        .ops-status-pill.warning{background:#fffbeb;color:#d97706}
        .ops-status-pill.success{background:#f0fdf4;color:#16a34a}
        .ops-status-pill.info{background:#eff6ff;color:#2563eb}
        .ops-status-pill.purple{background:#faf5ff;color:#9333ea}
        .ops-status-pill.default{background:#f1f5f9;color:#475569}
        .ops-overdue-date{color:var(--ops-danger);font-weight:600}

        .ops-quick-links{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;padding:8px 0}
        .ops-quick-link{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:white;border-radius:20px;font-size:12px;color:#475569;text-decoration:none;border:1px solid var(--ops-border);transition:all .3s ease}
        .ops-quick-link:hover{background:var(--ops-primary);color:white;border-color:var(--ops-primary);transform:translateY(-2px);box-shadow:var(--ops-shadow)}
        .ops-quick-link i{font-size:14px}

        .ops-loading{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:400px;gap:20px}
        .ops-loading-spinner{width:50px;height:50px;border:4px solid #e2e8f0;border-top-color:var(--ops-primary);border-radius:50%;animation:spin 1s linear infinite}
        .ops-loading-text{color:#64748b;font-size:14px}
        .ops-empty-state{text-align:center;padding:30px 20px;color:#94a3b8}
        .ops-empty-state i{font-size:40px;margin-bottom:10px;opacity:.5}
        .ops-empty-state p{margin:0;font-size:13px}
        .ops-refresh-indicator{display:inline-flex;align-items:center;gap:5px;font-size:10px;color:var(--ops-success);padding:3px 8px;background:#f0fdf4;border-radius:10px}
        .ops-refresh-indicator i{animation:spin 2s linear infinite}

        .ops-shipment-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
        .ops-shipment-card{text-align:center;padding:12px;background:var(--ops-light);border-radius:10px;border-left:3px solid var(--ship-color);cursor:pointer;transition:all .2s}
        .ops-shipment-card:hover{background:#e2e8f0}
        .ops-shipment-card.orange{--ship-color:#f97316}
        .ops-shipment-card.blue{--ship-color:#3b82f6}
        .ops-shipment-card.green{--ship-color:#10b981}
        .ops-shipment-card .ship-value{font-size:24px;font-weight:700;color:var(--ship-color)}
        .ops-shipment-card .ship-label{font-size:9px;color:#64748b;text-transform:uppercase}

        .ops-recent-orders-mini{max-height:280px;overflow-y:auto}
        .ops-recent-order-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;margin-bottom:6px;background:var(--ops-light);transition:all .2s;cursor:pointer}
        .ops-recent-order-item:hover{background:#e2e8f0;transform:translateX(3px)}
        .ops-recent-order-item:last-child{margin-bottom:0}
        .ops-recent-order-id{font-weight:600;color:var(--ops-primary);font-size:12px;min-width:70px}
        .ops-recent-order-customer{flex:1;font-size:11px;color:#475569;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .ops-recent-order-amount{font-weight:600;font-size:12px;color:var(--ops-dark)}
        .ops-recent-order-status{padding:2px 6px;border-radius:10px;font-size:9px;font-weight:600;text-transform:uppercase}
        .ops-recent-order-status.new{background:#fff7ed;color:#ea580c}
        .ops-recent-order-status.design{background:#faf5ff;color:#9333ea}
        .ops-recent-order-status.processing{background:#eff6ff;color:#2563eb}
        .ops-recent-order-status.production{background:#fefce8;color:#ca8a04}
        .ops-recent-order-status.ready{background:#f0fdf4;color:#16a34a}
        .ops-recent-order-status.completed{background:#ecfdf5;color:#059669}

        .ops-summary-row{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:20px}
        @media(max-width:900px){.ops-summary-row{grid-template-columns:repeat(2,1fr)}}
        .ops-summary-card{background:white;border-radius:12px;padding:15px;box-shadow:var(--ops-shadow);display:flex;align-items:center;gap:12px}
        .ops-summary-icon{width:45px;height:45px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px}
        .ops-summary-icon.purple{background:#f3e8ff;color:#9333ea}
        .ops-summary-icon.blue{background:#dbeafe;color:#2563eb}
        .ops-summary-icon.green{background:#dcfce7;color:#16a34a}
        .ops-summary-icon.orange{background:#ffedd5;color:#ea580c}
        .ops-summary-info{flex:1}
        .ops-summary-value{font-size:22px;font-weight:700;color:var(--ops-dark)}
        .ops-summary-label{font-size:11px;color:#64748b}

        @keyframes fadeIn{from{opacity:0}to{opacity:1}}
        @keyframes fadeInUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
        @keyframes fadeInDown{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
        @keyframes spin{to{transform:rotate(360deg)}}
        @media(max-width:576px){.ops-orders-dashboard{padding:12px}.ops-greeting{font-size:20px}.ops-entity-card{padding:15px}.ops-card-value{font-size:26px}.ops-quick-stats{grid-template-columns:1fr}.ops-attention-tabs{overflow-x:auto;flex-wrap:nowrap;padding-bottom:8px}.ops-attention-tab{white-space:nowrap}.ops-filter-bar{flex-direction:column;align-items:stretch}.ops-filter-actions{margin-left:0;margin-top:10px}}
    </style>`;
}

function get_greeting() {
    var hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
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

function get_date_range_label(range) {
    var labels = {
        'today': 'Today',
        'yesterday': 'Yesterday',
        'this_week': 'This Week',
        'last_week': 'Last Week',
        'this_month': 'This Month',
        'last_month': 'Last Month',
        'last_30': 'Last 30 Days',
        'last_90': 'Last 90 Days',
        'this_quarter': 'This Quarter',
        'this_year': 'This Year',
        'all': 'All Time'
    };
    return labels[range] || range;
}

function get_mini_status_class(status) {
    var map = {
        'New Order': 'new',
        'In Design': 'design',
        'Order Processing': 'processing',
        'Order Review': 'processing',
        'In Production': 'production',
        'Ready for Fulfillment': 'ready',
        'Fulfilled': 'completed',
        'Order Completed': 'completed'
    };
    return map[status] || '';
}

function render_recent_orders_mini(orders) {
    if (!orders || orders.length === 0) {
        return '<div class="ops-empty-state" style="padding: 20px;"><i class="fa fa-inbox"></i><p>No recent orders</p></div>';
    }

    var html = '';
    var display_orders = orders.slice(0, 8); // Show max 8 orders

    display_orders.forEach(function(o) {
        var status_class = get_mini_status_class(o.order_status);
        var short_status = (o.order_status || 'Unknown').replace('Order ', '').replace(' for ', ' ');
        if (short_status.length > 12) short_status = short_status.substring(0, 10) + '..';

        html += '<div class="ops-recent-order-item" onclick="frappe.set_route(\'Form\', \'OPS Order\', \'' + o.name + '\')">' +
            '<span class="ops-recent-order-id">#' + (o.ops_order_id || o.name).toString().slice(-6) + '</span>' +
            '<span class="ops-recent-order-customer">' + (o.customer_name || 'Unknown') + '</span>' +
            '<span class="ops-recent-order-status ' + status_class + '">' + short_status + '</span>' +
            '<span class="ops-recent-order-amount">$' + (o.order_amount || 0).toLocaleString() + '</span>' +
            '</div>';
    });

    return html;
}

function render_dashboard(page, stats, attention, timeline, pipeline, recent, shipments) {
    var current_range = page.dashboard_data.filters.date_range;
    var current_status = page.dashboard_data.filters.status;

    var html = get_styles() + `<div class="ops-orders-dashboard">
        <!-- Filter Bar -->
        <div class="ops-filter-bar">
            <div class="ops-filter-group">
                <label>Date Range</label>
                <select id="filter-date-range">
                    <option value="today" ${current_range === 'today' ? 'selected' : ''}>Today</option>
                    <option value="yesterday" ${current_range === 'yesterday' ? 'selected' : ''}>Yesterday</option>
                    <option value="this_week" ${current_range === 'this_week' ? 'selected' : ''}>This Week</option>
                    <option value="last_week" ${current_range === 'last_week' ? 'selected' : ''}>Last Week</option>
                    <option value="this_month" ${current_range === 'this_month' ? 'selected' : ''}>This Month</option>
                    <option value="last_month" ${current_range === 'last_month' ? 'selected' : ''}>Last Month</option>
                    <option value="last_30" ${current_range === 'last_30' ? 'selected' : ''}>Last 30 Days</option>
                    <option value="last_90" ${current_range === 'last_90' ? 'selected' : ''}>Last 90 Days</option>
                    <option value="this_quarter" ${current_range === 'this_quarter' ? 'selected' : ''}>This Quarter</option>
                    <option value="this_year" ${current_range === 'this_year' ? 'selected' : ''}>This Year</option>
                    <option value="all" ${current_range === 'all' ? 'selected' : ''}>All Time</option>
                </select>
            </div>
            <div class="ops-filter-group">
                <label>Status</label>
                <select id="filter-status">
                    <option value="all" ${current_status === 'all' ? 'selected' : ''}>All Statuses</option>
                    <option value="New Order" ${current_status === 'New Order' ? 'selected' : ''}>New Order</option>
                    <option value="In Design" ${current_status === 'In Design' ? 'selected' : ''}>In Design</option>
                    <option value="Order Processing" ${current_status === 'Order Processing' ? 'selected' : ''}>Order Processing</option>
                    <option value="Order Review" ${current_status === 'Order Review' ? 'selected' : ''}>Order Review</option>
                    <option value="In Production" ${current_status === 'In Production' ? 'selected' : ''}>In Production</option>
                    <option value="Ready for Fulfillment" ${current_status === 'Ready for Fulfillment' ? 'selected' : ''}>Ready for Fulfillment</option>
                    <option value="Fulfilled" ${current_status === 'Fulfilled' ? 'selected' : ''}>Fulfilled</option>
                    <option value="Order Completed" ${current_status === 'Order Completed' ? 'selected' : ''}>Order Completed</option>
                    <option value="Cancelled" ${current_status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                </select>
            </div>
            <div class="ops-filter-group">
                <label>Search Orders</label>
                <input type="text" id="filter-search" placeholder="Order ID, Customer..." value="${page.dashboard_data.filters.customer || ''}">
            </div>
            <div class="ops-filter-actions">
                <button class="ops-filter-btn primary" id="btn-apply-filters">
                    <i class="fa fa-filter"></i> Apply
                </button>
                <button class="ops-filter-btn secondary" id="btn-reset-filters">
                    <i class="fa fa-times"></i> Reset
                </button>
                <button class="ops-filter-btn success" id="btn-sync-now">
                    <i class="fa fa-cloud-download"></i> Sync
                </button>
            </div>
        </div>

        <!-- Header -->
        <div class="ops-dashboard-header">
            <div>
                <div class="ops-greeting">${get_greeting()}, Orders Overview</div>
                <div class="ops-subgreeting">
                    <span>Showing: <strong>${get_date_range_label(current_range)}</strong></span>
                    <span class="ops-last-updated">Updated ${format_time_ago(page.dashboard_data.last_updated)}</span>
                    ${page.dashboard_data.auto_refresh_interval ? '<span class="ops-refresh-indicator"><i class="fa fa-sync-alt"></i> Auto</span>' : ''}
                </div>
            </div>
            <div class="ops-header-stats">
                <div class="ops-header-stat">
                    <div class="ops-header-stat-value">${format_currency(stats.total_revenue)}</div>
                    <div class="ops-header-stat-label">Total Revenue</div>
                </div>
                <div class="ops-header-stat">
                    <div class="ops-header-stat-value" style="color: var(--ops-success);">${format_currency(stats.avg_order_value)}</div>
                    <div class="ops-header-stat-label">Avg Order</div>
                </div>
            </div>
        </div>

        <!-- Entity Cards -->
        <div class="ops-entity-cards">
            <div class="ops-entity-card" onclick="frappe.set_route('List', 'OPS Order')">
                <i class="fa fa-shopping-bag ops-card-icon"></i>
                <div class="ops-card-label">All Orders</div>
                <div class="ops-card-value">${stats.total_orders || 0}</div>
                <div class="ops-card-sub">${format_currency(stats.total_revenue)}</div>
            </div>
            <div class="ops-entity-card" onclick="frappe.set_route('List', 'OPS Order', {order_status: ['not in', ['Order Completed', 'Fulfilled', 'Cancelled', 'Refunded']]})">
                <i class="fa fa-spinner ops-card-icon"></i>
                <div class="ops-card-label">Active</div>
                <div class="ops-card-value">${stats.active_orders || 0}</div>
                <div class="ops-card-sub">In progress</div>
            </div>
            <div class="ops-entity-card" onclick="frappe.set_route('List', 'OPS Order', {order_status: 'New Order'})">
                <i class="fa fa-star ops-card-icon"></i>
                <div class="ops-card-label">New</div>
                <div class="ops-card-value">${stats.new_orders || 0}</div>
                <div class="ops-card-sub">Awaiting action</div>
            </div>
            <div class="ops-entity-card" onclick="frappe.set_route('List', 'OPS Order', {order_status: 'In Production'})">
                <i class="fa fa-cogs ops-card-icon"></i>
                <div class="ops-card-label">Production</div>
                <div class="ops-card-value">${stats.in_production || 0}</div>
                <div class="ops-card-sub">Being built</div>
            </div>
            <div class="ops-entity-card" onclick="frappe.set_route('List', 'OPS Order', {order_status: 'Ready for Fulfillment'})">
                <i class="fa fa-truck ops-card-icon"></i>
                <div class="ops-card-label">Ready</div>
                <div class="ops-card-value">${stats.ready_fulfillment || 0}</div>
                <div class="ops-card-sub">To ship</div>
            </div>
            <div class="ops-entity-card" onclick="frappe.set_route('List', 'OPS Order', {all_proofs_approved: 0, pending_proof_count: ['>', 0]})">
                <i class="fa fa-file-image-o ops-card-icon"></i>
                <div class="ops-card-label">Proofs</div>
                <div class="ops-card-value">${stats.pending_proofs || 0}</div>
                <div class="ops-card-sub">Pending</div>
            </div>
        </div>

        <!-- Recent Orders + Stats -->
        <div class="ops-stat-panels">
            <div class="ops-panel" style="animation-delay: 0.2s;">
                <div class="ops-panel-header">
                    <div class="ops-panel-title"><i class="fa fa-clock-o"></i> Recent Orders</div>
                    <span class="ops-panel-action" onclick="frappe.set_route('List', 'OPS Order')"><i class="fa fa-external-link"></i> View All</span>
                </div>
                <div class="ops-recent-orders-mini">
                    ${render_recent_orders_mini(recent)}
                </div>
            </div>
            <div class="ops-panel" style="animation-delay: 0.3s;">
                <div class="ops-panel-header">
                    <div class="ops-panel-title"><i class="fa fa-sun-o"></i> Today's Activity</div>
                    <span class="ops-panel-badge">${frappe.datetime.get_today()}</span>
                </div>
                <div class="ops-quick-stats">
                    <div class="ops-quick-stat" onclick="frappe.set_route('List', 'OPS Order', {date_purchased: ['>=', frappe.datetime.get_today()]})">
                        <div class="ops-quick-stat-value primary">${stats.orders_today || 0}</div>
                        <div class="ops-quick-stat-label">Orders</div>
                    </div>
                    <div class="ops-quick-stat">
                        <div class="ops-quick-stat-value success">${format_currency(stats.today_revenue || 0)}</div>
                        <div class="ops-quick-stat-label">Revenue</div>
                    </div>
                    <div class="ops-quick-stat" onclick="frappe.set_route('List', 'OPS ZiFlow Proof', {proof_status: ['not in', ['Approved', 'Cancelled']]})">
                        <div class="ops-quick-stat-value warning">${stats.pending_proofs || 0}</div>
                        <div class="ops-quick-stat-label">Proofs</div>
                    </div>
                </div>
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--ops-border);">
                    <div class="ops-quick-stats">
                        <div class="ops-quick-stat">
                            <div class="ops-quick-stat-value primary">${stats.orders_this_month || 0}</div>
                            <div class="ops-quick-stat-label">This Month</div>
                        </div>
                        <div class="ops-quick-stat">
                            <div class="ops-quick-stat-value success">${format_currency(stats.monthly_revenue)}</div>
                            <div class="ops-quick-stat-label">Monthly Rev</div>
                        </div>
                        <div class="ops-quick-stat">
                            <div class="ops-quick-stat-value primary">${format_currency(stats.avg_order_value)}</div>
                            <div class="ops-quick-stat-label">Avg Order</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Pipeline and Shipments -->
        <div class="ops-stat-panels">
            <div class="ops-panel" style="animation-delay: 0.4s;">
                <div class="ops-panel-header">
                    <div class="ops-panel-title"><i class="fa fa-tasks"></i> Order Pipeline</div>
                    <span class="ops-panel-action" onclick="frappe.set_route('List', 'OPS Order')"><i class="fa fa-external-link"></i> View All</span>
                </div>
                ${render_order_pipeline(pipeline)}
            </div>
            <div class="ops-panel" style="animation-delay: 0.5s;">
                <div class="ops-panel-header">
                    <div class="ops-panel-title"><i class="fa fa-truck"></i> Shipments</div>
                    <span class="ops-panel-action" onclick="frappe.set_route('List', 'OPS Order', {order_status: 'Ready for Fulfillment'})"><i class="fa fa-external-link"></i> Manage</span>
                </div>
                <div class="ops-shipment-cards">
                    <div class="ops-shipment-card orange" onclick="frappe.set_route('List', 'OPS Order', {order_status: 'Ready for Fulfillment'})">
                        <div class="ship-value">${shipments.awaiting_shipment || 0}</div>
                        <div class="ship-label">Awaiting</div>
                    </div>
                    <div class="ops-shipment-card blue">
                        <div class="ship-value">${shipments.in_transit || 0}</div>
                        <div class="ship-label">In Transit</div>
                    </div>
                    <div class="ops-shipment-card green">
                        <div class="ship-value">${shipments.delivered_today || 0}</div>
                        <div class="ship-label">Delivered</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="ops-charts-row">
            <div class="ops-panel" style="animation-delay: 0.6s;">
                <div class="ops-panel-header">
                    <div class="ops-panel-title"><i class="fa fa-line-chart"></i> Order Activity</div>
                    <span class="ops-panel-badge">Last 30 Days</span>
                </div>
                <div class="ops-chart-container" id="activity-chart"></div>
            </div>
            <div class="ops-panel" style="animation-delay: 0.7s;">
                <div class="ops-panel-header">
                    <div class="ops-panel-title"><i class="fa fa-pie-chart"></i> By Status</div>
                </div>
                <div class="ops-chart-container" id="status-chart"></div>
            </div>
        </div>

        <!-- Attention Section -->
        <div class="ops-panel ops-attention-section" style="animation-delay: 0.8s;">
            <div class="ops-panel-header">
                <div class="ops-panel-title"><i class="fa fa-exclamation-circle"></i> Items Needing Attention</div>
            </div>
            <div class="ops-attention-tabs">
                <div class="ops-attention-tab active" data-tab="pending-proofs-tab">
                    <i class="fa fa-file-image-o"></i> Pending Proofs
                    <span class="badge">${attention.pending_proofs ? attention.pending_proofs.length : 0}</span>
                </div>
                <div class="ops-attention-tab" data-tab="overdue-orders-tab">
                    <i class="fa fa-clock-o"></i> Overdue
                    <span class="badge">${attention.overdue ? attention.overdue.length : 0}</span>
                </div>
                <div class="ops-attention-tab" data-tab="recent-orders-tab">
                    <i class="fa fa-list"></i> Recent
                    <span class="badge">${recent.length}</span>
                </div>
            </div>
            <div class="ops-attention-content">
                <div class="ops-attention-pane active" id="pending-proofs-tab"></div>
                <div class="ops-attention-pane" id="overdue-orders-tab"></div>
                <div class="ops-attention-pane" id="recent-orders-tab"></div>
            </div>
        </div>

        <!-- Quick Links -->
        <div class="ops-panel" style="animation-delay: 0.9s;">
            <div class="ops-quick-links">
                <a href="/app/ops-order" class="ops-quick-link"><i class="fa fa-shopping-cart"></i> All Orders</a>
                <a href="/app/ops-ziflow-proof" class="ops-quick-link"><i class="fa fa-file-image-o"></i> Proofs</a>
                <a href="/app/ops-customer" class="ops-quick-link"><i class="fa fa-users"></i> Customers</a>
                <a href="/app/ops-product" class="ops-quick-link"><i class="fa fa-cube"></i> Products</a>
                <a href="/app/ops-quote" class="ops-quick-link"><i class="fa fa-file-text-o"></i> Quotes</a>
                <a href="/app/ops-cluster-dashboard" class="ops-quick-link"><i class="fa fa-dashboard"></i> Cluster</a>
                <a href="/app/ops-error-log" class="ops-quick-link"><i class="fa fa-bug"></i> Errors</a>
            </div>
        </div>
    </div>`;

    page.main.html(html);

    // Setup filter handlers
    setup_filter_handlers(page);

    // Render tables
    render_pending_proofs_table(page);
    render_overdue_orders_table(page);
    render_recent_orders_table(page);

    // Tab switching
    page.main.find('.ops-attention-tab').on('click', function() {
        var tab_id = $(this).data('tab');
        page.main.find('.ops-attention-tab').removeClass('active');
        $(this).addClass('active');
        page.main.find('.ops-attention-pane').removeClass('active');
        page.main.find('#' + tab_id).addClass('active');
    });

    // Render charts
    setTimeout(function() {
        render_activity_chart(timeline);
        render_status_chart(stats.by_status);
    }, 100);
}

function setup_filter_handlers(page) {
    // Apply filters
    page.main.find('#btn-apply-filters').on('click', function() {
        page.dashboard_data.filters.date_range = page.main.find('#filter-date-range').val();
        page.dashboard_data.filters.status = page.main.find('#filter-status').val();
        page.dashboard_data.filters.customer = page.main.find('#filter-search').val();
        load_dashboard(page, true);
    });

    // Reset filters
    page.main.find('#btn-reset-filters').on('click', function() {
        page.dashboard_data.filters = {
            date_range: 'this_month',
            status: 'all',
            customer: '',
            store: ''
        };
        page.main.find('#filter-date-range').val('this_month');
        page.main.find('#filter-status').val('all');
        page.main.find('#filter-search').val('');
        load_dashboard(page, true);
    });

    // Sync button
    page.main.find('#btn-sync-now').on('click', function() {
        sync_orders(page);
    });

    // Enter key on search
    page.main.find('#filter-search').on('keypress', function(e) {
        if (e.which === 13) {
            page.main.find('#btn-apply-filters').click();
        }
    });

    // Auto-apply on select change (optional - can be removed if you want explicit apply)
    page.main.find('#filter-date-range, #filter-status').on('change', function() {
        page.dashboard_data.filters.date_range = page.main.find('#filter-date-range').val();
        page.dashboard_data.filters.status = page.main.find('#filter-status').val();
        load_dashboard(page, true);
    });
}

function render_order_pipeline(pipeline) {
    if (!pipeline || Object.keys(pipeline).length === 0) {
        return '<div class="ops-empty-state"><p>No orders in pipeline</p></div>';
    }

    var statuses = ['New Order', 'In Design', 'Order Processing', 'Order Review', 'In Production', 'Ready for Fulfillment'];
    var colors = ['#f97316', '#8b5cf6', '#3b82f6', '#14b8a6', '#f59e0b', '#10b981'];
    var total = 0;

    statuses.forEach(function(s) {
        if (pipeline[s]) total += pipeline[s].count || 0;
    });

    if (total === 0) return '<div class="ops-empty-state"><p>No active orders</p></div>';

    var html = '<div class="ops-pipeline"><div class="ops-pipeline-bar">';
    statuses.forEach(function(status, i) {
        var data = pipeline[status] || { count: 0 };
        var pct = total > 0 ? (data.count / total * 100) : 0;
        if (data.count > 0) {
            html += '<div class="ops-pipeline-segment" style="flex: ' + Math.max(pct, 5) + '; background: ' + colors[i] + ';" title="' + status + ': ' + data.count + '" onclick="frappe.set_route(\'List\', \'OPS Order\', {order_status: \'' + status + '\'})"></div>';
        }
    });
    html += '</div><div class="ops-pipeline-legend">';
    statuses.forEach(function(status, i) {
        var data = pipeline[status] || { count: 0 };
        if (data.count > 0) {
            html += '<div class="ops-pipeline-item" onclick="frappe.set_route(\'List\', \'OPS Order\', {order_status: \'' + status + '\'})">' +
                '<span class="ops-pipeline-dot" style="background: ' + colors[i] + ';"></span>' +
                '<span>' + status.replace('Order ', '').replace(' for ', ' ') + ': <strong>' + data.count + '</strong></span></div>';
        }
    });
    html += '</div></div>';
    return html;
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

function render_pending_proofs_table(page) {
    var orders = page.dashboard_data.attention.pending_proofs || [];
    var sort = page.dashboard_data.sort_state['pending-proofs'];
    var sorted = sort_data(orders, sort.field, sort.order);

    if (!sorted || sorted.length === 0) {
        $('#pending-proofs-tab').html('<div class="ops-empty-state"><i class="fa fa-check-circle"></i><p>All proofs approved!</p></div>');
        return;
    }

    var html = '<table class="ops-table"><thead><tr>' +
        '<th class="sortable ' + (sort.field === 'ops_order_id' ? 'active' : '') + '" data-field="ops_order_id" data-list="pending-proofs">Order ' + get_sort_icon(sort.field, sort.order, 'ops_order_id') + '</th>' +
        '<th class="sortable ' + (sort.field === 'customer_name' ? 'active' : '') + '" data-field="customer_name" data-list="pending-proofs">Customer ' + get_sort_icon(sort.field, sort.order, 'customer_name') + '</th>' +
        '<th class="sortable ' + (sort.field === 'pending_proof_count' ? 'active' : '') + '" data-field="pending_proof_count" data-list="pending-proofs">Proofs ' + get_sort_icon(sort.field, sort.order, 'pending_proof_count') + '</th>' +
        '<th class="sortable ' + (sort.field === 'order_status' ? 'active' : '') + '" data-field="order_status" data-list="pending-proofs">Status ' + get_sort_icon(sort.field, sort.order, 'order_status') + '</th>' +
        '<th>Actions</th>' +
        '</tr></thead><tbody>';

    sorted.forEach(function(o) {
        html += '<tr>' +
            '<td><a href="/app/ops-order/' + o.name + '">' + (o.ops_order_id || o.name) + '</a></td>' +
            '<td>' + (o.customer_name || '-') + '</td>' +
            '<td><span class="ops-status-pill warning">' + o.pending_proof_count + '</span></td>' +
            '<td><span class="ops-status-pill ' + get_status_class(o.order_status) + '">' + (o.order_status || '-') + '</span></td>' +
            '<td class="ops-table-actions">' +
                '<a class="ops-table-action" href="/app/ops-order/' + o.name + '" title="View"><i class="fa fa-eye"></i></a>' +
                '<a class="ops-table-action" href="/app/ops-ziflow-proof?ops_order=' + o.name + '" title="Proofs"><i class="fa fa-file-image-o"></i></a>' +
            '</td>' +
            '</tr>';
    });
    html += '</tbody></table>';
    $('#pending-proofs-tab').html(html);
    setup_sort_handlers(page);
}

function render_overdue_orders_table(page) {
    var orders = page.dashboard_data.attention.overdue || [];
    var sort = page.dashboard_data.sort_state['overdue-orders'];
    var sorted = sort_data(orders, sort.field, sort.order);

    if (!sorted || sorted.length === 0) {
        $('#overdue-orders-tab').html('<div class="ops-empty-state"><i class="fa fa-check-circle"></i><p>No overdue orders!</p></div>');
        return;
    }

    var html = '<table class="ops-table"><thead><tr>' +
        '<th class="sortable ' + (sort.field === 'ops_order_id' ? 'active' : '') + '" data-field="ops_order_id" data-list="overdue-orders">Order ' + get_sort_icon(sort.field, sort.order, 'ops_order_id') + '</th>' +
        '<th class="sortable ' + (sort.field === 'customer_name' ? 'active' : '') + '" data-field="customer_name" data-list="overdue-orders">Customer ' + get_sort_icon(sort.field, sort.order, 'customer_name') + '</th>' +
        '<th class="sortable ' + (sort.field === 'order_status' ? 'active' : '') + '" data-field="order_status" data-list="overdue-orders">Status ' + get_sort_icon(sort.field, sort.order, 'order_status') + '</th>' +
        '<th class="sortable ' + (sort.field === 'production_due_date' ? 'active' : '') + '" data-field="production_due_date" data-list="overdue-orders">Due ' + get_sort_icon(sort.field, sort.order, 'production_due_date') + '</th>' +
        '<th class="sortable ' + (sort.field === 'order_amount' ? 'active' : '') + '" data-field="order_amount" data-list="overdue-orders">Amount ' + get_sort_icon(sort.field, sort.order, 'order_amount') + '</th>' +
        '</tr></thead><tbody>';

    sorted.forEach(function(o) {
        html += '<tr>' +
            '<td><a href="/app/ops-order/' + o.name + '">' + (o.ops_order_id || o.name) + '</a></td>' +
            '<td>' + (o.customer_name || '-') + '</td>' +
            '<td><span class="ops-status-pill danger">' + (o.order_status || '-') + '</span></td>' +
            '<td class="ops-overdue-date">' + (o.production_due_date || '-') + '</td>' +
            '<td>' + format_currency(o.order_amount) + '</td>' +
            '</tr>';
    });
    html += '</tbody></table>';
    $('#overdue-orders-tab').html(html);
    setup_sort_handlers(page);
}

function render_recent_orders_table(page) {
    var orders = page.dashboard_data.recent || [];
    var sort = page.dashboard_data.sort_state['recent-orders'];
    var sorted = sort_data(orders, sort.field, sort.order);

    if (!sorted || sorted.length === 0) {
        $('#recent-orders-tab').html('<div class="ops-empty-state"><i class="fa fa-inbox"></i><p>No orders found</p></div>');
        return;
    }

    var html = '<table class="ops-table"><thead><tr>' +
        '<th class="sortable ' + (sort.field === 'ops_order_id' ? 'active' : '') + '" data-field="ops_order_id" data-list="recent-orders">Order ' + get_sort_icon(sort.field, sort.order, 'ops_order_id') + '</th>' +
        '<th class="sortable ' + (sort.field === 'customer_name' ? 'active' : '') + '" data-field="customer_name" data-list="recent-orders">Customer ' + get_sort_icon(sort.field, sort.order, 'customer_name') + '</th>' +
        '<th class="sortable ' + (sort.field === 'order_status' ? 'active' : '') + '" data-field="order_status" data-list="recent-orders">Status ' + get_sort_icon(sort.field, sort.order, 'order_status') + '</th>' +
        '<th class="sortable ' + (sort.field === 'date_purchased' ? 'active' : '') + '" data-field="date_purchased" data-list="recent-orders">Date ' + get_sort_icon(sort.field, sort.order, 'date_purchased') + '</th>' +
        '<th class="sortable ' + (sort.field === 'order_amount' ? 'active' : '') + '" data-field="order_amount" data-list="recent-orders">Amount ' + get_sort_icon(sort.field, sort.order, 'order_amount') + '</th>' +
        '<th>Actions</th>' +
        '</tr></thead><tbody>';

    sorted.forEach(function(o) {
        var proof_indicator = '';
        if (o.pending_proof_count > 0 && !o.all_proofs_approved) {
            proof_indicator = ' <i class="fa fa-circle" style="color:#ef4444;font-size:8px;" title="Pending proofs"></i>';
        } else if (o.all_proofs_approved) {
            proof_indicator = ' <i class="fa fa-circle" style="color:#10b981;font-size:8px;" title="Proofs approved"></i>';
        }

        html += '<tr>' +
            '<td><a href="/app/ops-order/' + o.name + '">' + (o.ops_order_id || o.name) + '</a>' + proof_indicator + '</td>' +
            '<td>' + (o.customer_name || '-') + '</td>' +
            '<td><span class="ops-status-pill ' + get_status_class(o.order_status) + '">' + (o.order_status || '-') + '</span></td>' +
            '<td>' + (o.date_purchased || '-') + '</td>' +
            '<td>' + format_currency(o.order_amount) + '</td>' +
            '<td class="ops-table-actions">' +
                '<a class="ops-table-action" href="/app/ops-order/' + o.name + '" title="View"><i class="fa fa-eye"></i></a>' +
                '<a class="ops-table-action" onclick="window.open(\'/printview?doctype=OPS Order&name=' + o.name + '&format=Standard\', \'_blank\')" title="Print"><i class="fa fa-print"></i></a>' +
            '</td>' +
            '</tr>';
    });
    html += '</tbody></table>';
    $('#recent-orders-tab').html(html);
    setup_sort_handlers(page);
}

function get_status_class(status) {
    var map = {
        'New Order': 'warning',
        'In Design': 'purple',
        'Order Processing': 'info',
        'Order Review': 'info',
        'In Production': 'warning',
        'Ready for Fulfillment': 'success',
        'Fulfilled': 'success',
        'Order Completed': 'success',
        'Cancelled': 'danger',
        'Refunded': 'danger',
        'ERROR': 'danger'
    };
    return map[status] || 'default';
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

        if (list === 'pending-proofs') render_pending_proofs_table(page);
        else if (list === 'overdue-orders') render_overdue_orders_table(page);
        else if (list === 'recent-orders') render_recent_orders_table(page);
    });
}

function render_activity_chart(timeline) {
    var created = timeline.created || [];
    var completed = timeline.completed || [];

    var all_dates = {};
    created.forEach(function(d) { if(d.date) all_dates[d.date] = true; });
    completed.forEach(function(d) { if(d.date) all_dates[d.date] = true; });

    var labels = Object.keys(all_dates).sort();
    if (labels.length === 0) {
        $('#activity-chart').html('<div class="ops-empty-state"><i class="fa fa-chart-line"></i><p>No activity data</p></div>');
        return;
    }

    var created_map = {}, completed_map = {};
    created.forEach(function(d) { if(d.date) created_map[d.date] = d.count; });
    completed.forEach(function(d) { if(d.date) completed_map[d.date] = d.count; });

    var created_values = labels.map(function(d) { return created_map[d] || 0; });
    var completed_values = labels.map(function(d) { return completed_map[d] || 0; });
    var display_labels = labels.map(function(d) { return d.substring(5); });

    // Check if frappe.Chart is available
    if (typeof frappe.Chart === 'undefined') {
        console.error('frappe.Chart is not available');
        $('#activity-chart').html('<div class="ops-empty-state"><i class="fa fa-exclamation-triangle"></i><p>Chart library not loaded</p></div>');
        return;
    }

    try {
        // Clear any existing chart
        $('#activity-chart').empty();

        new frappe.Chart('#activity-chart', {
            data: {
                labels: display_labels,
                datasets: [
                    { name: 'Created', values: created_values },
                    { name: 'Completed', values: completed_values }
                ]
            },
            type: 'line',
            colors: ['#6366f1', '#10b981'],
            height: 200,
            lineOptions: { regionFill: 1, hideDots: 0, dotSize: 3 },
            axisOptions: { xIsSeries: true }
        });
    } catch (e) {
        console.error('Error rendering activity chart:', e);
        $('#activity-chart').html('<div class="ops-empty-state"><i class="fa fa-exclamation-triangle"></i><p>Error rendering chart</p></div>');
    }
}

function render_status_chart(by_status) {
    if (!by_status || Object.keys(by_status).length === 0) {
        $('#status-chart').html('<div class="ops-empty-state"><i class="fa fa-pie-chart"></i><p>No data</p></div>');
        return;
    }

    // Check if frappe.Chart is available
    if (typeof frappe.Chart === 'undefined') {
        console.error('frappe.Chart is not available');
        $('#status-chart').html('<div class="ops-empty-state"><i class="fa fa-exclamation-triangle"></i><p>Chart library not loaded</p></div>');
        return;
    }

    var labels = Object.keys(by_status);
    var values = labels.map(function(s) { return by_status[s]; });

    try {
        // Clear any existing chart
        $('#status-chart').empty();

        new frappe.Chart('#status-chart', {
            data: {
                labels: labels,
                datasets: [{ values: values }]
            },
            type: 'pie',
            colors: ['#f97316', '#8b5cf6', '#3b82f6', '#14b8a6', '#f59e0b', '#10b981', '#22c55e', '#16a34a', '#ef4444', '#94a3b8'],
            height: 200
        });
    } catch (e) {
        console.error('Error rendering status chart:', e);
        $('#status-chart').html('<div class="ops-empty-state"><i class="fa fa-exclamation-triangle"></i><p>Error rendering chart</p></div>');
    }
}
