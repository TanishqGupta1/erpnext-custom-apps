/**
 * OPS Quotes Dashboard - Dynamic Dashboard with Filters, Sorting, and Auto-Refresh
 */

frappe.pages['ops-quotes-dashboard'].on_page_load = function(wrapper) {
    // Ensure frappe-charts is loaded
    frappe.require('frappe-charts.bundle.js', function() {
        const page = frappe.ui.make_app_page({
            parent: wrapper,
            title: 'OPS Quotes Dashboard',
            single_column: true
        });
        new OPSQuotesDashboard(page);
    });
};

class OPSQuotesDashboard {
    constructor(page) {
        this.page = page;
        this.refresh_interval = null;
        this.auto_refresh_enabled = true;
        this.REFRESH_INTERVAL_MS = 5 * 60 * 1000;
        this.state = {
            filters: { status: '', date_from: '', date_to: '', customer: '', value_min: '', value_max: '', sync_status: '' },
            sort_field: 'quote_date', sort_order: 'desc', page: 0, limit: 25, active_tab: 'all'
        };
        this.data = { stats: null, timeline: null, attention: null, pipeline: null, quotes_list: null };
        this.setup_page();
        this.inject_styles();
        this.render_skeleton();
        this.load_dashboard();
        this.start_auto_refresh();
    }

    setup_page() {
        const me = this;
        this.page.set_primary_action(__('Refresh'), () => me.load_dashboard(), 'refresh');
        this.page.add_inner_button(__('Auto-Refresh: ON'), () => me.toggle_auto_refresh(), null, 'auto-refresh-btn');
        this.page.add_menu_item(__('View All Quotes'), () => frappe.set_route('List', 'OPS Quote'));
        this.page.add_menu_item(__('Export to CSV'), () => me.export_quotes());
    }

    inject_styles() {
        if (document.getElementById('ops-quotes-dashboard-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'ops-quotes-dashboard-styles';
        styles.textContent = `
            :root { --ops-primary: #667eea; --ops-success: #43e97b; --ops-warning: #ff9800; --ops-danger: #f44336; --ops-info: #2196f3; }
            .ops-quotes-dashboard { padding: 15px; background: #f5f7fa; min-height: calc(100vh - 120px); }
            .ops-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
            .ops-last-updated { font-size: 12px; color: #666; }
            .ops-filter-bar { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; }
            .ops-filter-group { display: flex; flex-direction: column; gap: 4px; }
            .ops-filter-group label { font-size: 11px; color: #666; font-weight: 500; }
            .ops-filter-group select, .ops-filter-group input { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; min-width: 120px; }
            .ops-filter-group input[type=date] { min-width: 130px; }
            .ops-filter-group input[type=number] { min-width: 90px; }
            .ops-filter-btn { padding: 6px 16px; border-radius: 4px; font-size: 13px; cursor: pointer; border: none; }
            .ops-filter-btn.primary { background: var(--ops-primary); color: white; }
            .ops-filter-btn.secondary { background: #e0e0e0; color: #333; }
            .ops-stat-card { padding: 20px; border-radius: 8px; text-align: center; color: white; transition: transform 0.2s, box-shadow 0.2s; cursor: pointer; }
            .ops-stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
            .ops-stat-value { font-size: 28px; font-weight: bold; }
            .ops-stat-label { font-size: 12px; opacity: 0.9; margin-top: 4px; }
            .ops-value-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
            .ops-value-amount { font-size: 24px; font-weight: bold; }
            .ops-value-label { font-size: 12px; color: #666; }
            .ops-panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-bottom: 20px; }
            .ops-panel-title { font-size: 16px; font-weight: 600; margin-bottom: 15px; color: #333; }
            .ops-pipeline-stage { padding: 15px; border-radius: 4px; border-left: 4px solid; cursor: pointer; transition: background 0.2s; }
            .ops-pipeline-stage:hover { background: rgba(0,0,0,0.03); }
            .ops-pipeline-status { font-weight: 600; margin-bottom: 5px; }
            .ops-pipeline-count { font-size: 24px; font-weight: bold; }
            .ops-pipeline-value { font-size: 12px; color: #666; }
            .ops-tabs { display: flex; gap: 5px; margin-bottom: 15px; border-bottom: 1px solid #e0e0e0; padding-bottom: 10px; }
            .ops-tab { padding: 8px 16px; border: none; background: transparent; cursor: pointer; font-size: 13px; color: #666; border-radius: 4px 4px 0 0; transition: all 0.2s; }
            .ops-tab:hover { background: #f0f0f0; }
            .ops-tab.active { background: var(--ops-primary); color: white; }
            .ops-tab .badge { margin-left: 5px; padding: 2px 6px; border-radius: 10px; font-size: 11px; background: rgba(255,255,255,0.2); }
            .ops-tab.active .badge { background: rgba(255,255,255,0.3); }
            .ops-table { width: 100%; border-collapse: collapse; }
            .ops-table th { text-align: left; padding: 10px 12px; background: #f8f9fa; font-size: 12px; font-weight: 600; color: #666; border-bottom: 2px solid #e0e0e0; cursor: pointer; user-select: none; white-space: nowrap; }
            .ops-table th:hover { background: #eee; }
            .ops-table th .sort-icon { margin-left: 5px; opacity: 0.5; }
            .ops-table th.sorted .sort-icon { opacity: 1; }
            .ops-table td { padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 13px; }
            .ops-table tr:hover { background: #f8f9fa; }
            .ops-status-badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 500; }
            .ops-pagination { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-top: 1px solid #eee; margin-top: 10px; }
            .ops-pagination-info { font-size: 13px; color: #666; }
            .ops-pagination-btns { display: flex; gap: 5px; }
            .ops-pagination-btn { padding: 6px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 13px; }
            .ops-pagination-btn:hover:not(:disabled) { background: #f0f0f0; }
            .ops-pagination-btn:disabled { opacity: 0.5; cursor: not-allowed; }
            .ops-empty-state { text-align: center; padding: 40px; color: #999; }
            .ops-empty-state i { font-size: 48px; margin-bottom: 15px; opacity: 0.5; }
            .ops-loading { text-align: center; padding: 50px; }
            .ops-loading i { font-size: 32px; color: var(--ops-primary); }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .ops-refreshing { animation: pulse 1s infinite; }
        `;
        document.head.appendChild(styles);
    }

    render_skeleton() {
        this.page.main.html('<div class="ops-quotes-dashboard"><div class="ops-loading"><i class="fa fa-spinner fa-spin"></i><p>Loading dashboard...</p></div></div>');
    }

    async load_dashboard() {
        const me = this;
        me.page.main.find('.ops-quotes-dashboard').addClass('ops-refreshing');
        try {
            const [stats_res, timeline_res, attention_res, pipeline_res, list_res] = await Promise.all([
                frappe.call({ method: 'ops_ziflow.api.quotes_dashboard.get_quotes_dashboard_stats' }),
                frappe.call({ method: 'ops_ziflow.api.quotes_dashboard.get_quotes_timeline', args: { days: 30 } }),
                frappe.call({ method: 'ops_ziflow.api.quotes_dashboard.get_quotes_needing_attention' }),
                frappe.call({ method: 'ops_ziflow.api.quotes_dashboard.get_quotes_pipeline' }),
                me.fetch_quotes_list()
            ]);
            me.data.stats = stats_res.message;
            me.data.timeline = timeline_res.message;
            me.data.attention = attention_res.message;
            me.data.pipeline = pipeline_res.message;
            me.data.quotes_list = list_res.message;
            me.render_dashboard();
        } catch (err) {
            console.error('Dashboard load error:', err);
            me.page.main.html('<div class="ops-quotes-dashboard"><div class="ops-empty-state"><i class="fa fa-exclamation-triangle"></i><p>Error loading dashboard</p></div></div>');
        }
    }

    async fetch_quotes_list() {
        return frappe.call({
            method: 'ops_ziflow.api.quotes_dashboard.get_quotes_list',
            args: {
                status: this.state.filters.status, date_from: this.state.filters.date_from, date_to: this.state.filters.date_to,
                customer: this.state.filters.customer, value_min: this.state.filters.value_min || null, value_max: this.state.filters.value_max || null,
                sync_status: this.state.filters.sync_status, sort_field: this.state.sort_field, sort_order: this.state.sort_order,
                limit: this.state.limit, offset: this.state.page * this.state.limit
            }
        });
    }

    render_dashboard() {
        const me = this;
        const stats = this.data.stats;
        const attention = this.data.attention;
        const pipeline = this.data.pipeline;

        const html = `
            <div class="ops-quotes-dashboard">
                <div class="ops-header">
                    <h3 style="margin: 0;">Quotes Overview</h3>
                    <div class="ops-last-updated">Last updated: ${frappe.datetime.now_datetime()}</div>
                </div>

                <!-- Filter Bar -->
                <div class="ops-filter-bar">
                    <div class="ops-filter-group">
                        <label>Status</label>
                        <select id="filter-status">
                            <option value="">All Statuses</option>
                            <option value="Draft">Draft</option>
                            <option value="Pending">Pending</option>
                            <option value="Sent">Sent</option>
                            <option value="Accepted">Accepted</option>
                            <option value="Rejected">Rejected</option>
                            <option value="Expired">Expired</option>
                            <option value="Converted">Converted</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </div>
                    <div class="ops-filter-group">
                        <label>Date From</label>
                        <input type="date" id="filter-date-from" value="${this.state.filters.date_from}">
                    </div>
                    <div class="ops-filter-group">
                        <label>Date To</label>
                        <input type="date" id="filter-date-to" value="${this.state.filters.date_to}">
                    </div>
                    <div class="ops-filter-group">
                        <label>Customer</label>
                        <input type="text" id="filter-customer" placeholder="Search..." value="${this.state.filters.customer}">
                    </div>
                    <div class="ops-filter-group">
                        <label>Min Value</label>
                        <input type="number" id="filter-value-min" placeholder="0" value="${this.state.filters.value_min}">
                    </div>
                    <div class="ops-filter-group">
                        <label>Max Value</label>
                        <input type="number" id="filter-value-max" placeholder="No max" value="${this.state.filters.value_max}">
                    </div>
                    <div class="ops-filter-group">
                        <label>Sync Status</label>
                        <select id="filter-sync-status">
                            <option value="">All</option>
                            <option value="Synced">Synced</option>
                            <option value="Pending">Pending</option>
                            <option value="Error">Error</option>
                        </select>
                    </div>
                    <button class="ops-filter-btn primary" id="apply-filters"><i class="fa fa-search"></i> Apply</button>
                    <button class="ops-filter-btn secondary" id="clear-filters"><i class="fa fa-times"></i> Clear</button>
                </div>

                <!-- Stat Cards -->
                <div class="row" style="margin-bottom: 20px;">
                    <div class="col-md-2 col-sm-4 col-xs-6" style="margin-bottom: 10px;">
                        <div class="ops-stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);" data-filter-status="">
                            <div class="ops-stat-value">${stats.total_quotes}</div>
                            <div class="ops-stat-label">Total Quotes</div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-xs-6" style="margin-bottom: 10px;">
                        <div class="ops-stat-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);" data-filter-status="Draft,Pending,Sent,Accepted">
                            <div class="ops-stat-value">${stats.active_quotes}</div>
                            <div class="ops-stat-label">Active Quotes</div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-xs-6" style="margin-bottom: 10px;">
                        <div class="ops-stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);" data-filter-status="Sent">
                            <div class="ops-stat-value">${stats.sent}</div>
                            <div class="ops-stat-label">Sent / Awaiting</div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-xs-6" style="margin-bottom: 10px;">
                        <div class="ops-stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);" data-filter-status="Accepted">
                            <div class="ops-stat-value">${stats.accepted}</div>
                            <div class="ops-stat-label">Accepted</div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-xs-6" style="margin-bottom: 10px;">
                        <div class="ops-stat-card" style="background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);" data-filter-status="Converted">
                            <div class="ops-stat-value">${stats.converted}</div>
                            <div class="ops-stat-label">Converted</div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-xs-6" style="margin-bottom: 10px;">
                        <div class="ops-stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                            <div class="ops-stat-value">${stats.conversion_rate}%</div>
                            <div class="ops-stat-label">Conversion Rate</div>
                        </div>
                    </div>
                </div>

                <!-- Value Metrics -->
                <div class="row" style="margin-bottom: 20px;">
                    <div class="col-md-3 col-sm-6" style="margin-bottom: 10px;">
                        <div class="ops-value-card">
                            <div class="ops-value-amount" style="color: #2e7d32;">${this.format_currency(stats.total_value)}</div>
                            <div class="ops-value-label">Total Quote Value</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6" style="margin-bottom: 10px;">
                        <div class="ops-value-card">
                            <div class="ops-value-amount" style="color: #1565c0;">${this.format_currency(stats.converted_value)}</div>
                            <div class="ops-value-label">Converted Value</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6" style="margin-bottom: 10px;">
                        <div class="ops-value-card">
                            <div class="ops-value-amount" style="color: #6a1b9a;">${this.format_currency(stats.avg_quote_value)}</div>
                            <div class="ops-value-label">Avg Quote Value</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6" style="margin-bottom: 10px;">
                        <div class="ops-value-card">
                            <div class="ops-value-amount" style="color: #00796b;">${stats.avg_profit_pct}%</div>
                            <div class="ops-value-label">Avg Profit Margin</div>
                        </div>
                    </div>
                </div>

                <!-- Charts Row -->
                <div class="row" style="margin-bottom: 20px;">
                    <div class="col-md-6" style="margin-bottom: 10px;">
                        <div class="ops-panel">
                            <div class="ops-panel-title">Quotes by Status</div>
                            <div id="status-chart" style="height: 250px;"></div>
                        </div>
                    </div>
                    <div class="col-md-6" style="margin-bottom: 10px;">
                        <div class="ops-panel">
                            <div class="ops-panel-title">Quotes Timeline (30 Days)</div>
                            <div id="timeline-chart" style="height: 250px;"></div>
                        </div>
                    </div>
                </div>

                <!-- Pipeline -->
                <div class="ops-panel">
                    <div class="ops-panel-title">Sales Pipeline</div>
                    <div class="row">${this.render_pipeline(pipeline)}</div>
                </div>

                <!-- Quotes Table -->
                <div class="ops-panel">
                    <div class="ops-tabs">
                        <button class="ops-tab ${this.state.active_tab === 'all' ? 'active' : ''}" data-tab="all">All Quotes <span class="badge">${this.data.quotes_list?.total || 0}</span></button>
                        <button class="ops-tab ${this.state.active_tab === 'attention' ? 'active' : ''}" data-tab="attention">Needs Attention <span class="badge">${(attention.pending?.length || 0) + (attention.sent?.length || 0)}</span></button>
                        <button class="ops-tab ${this.state.active_tab === 'errors' ? 'active' : ''}" data-tab="errors">Sync Errors <span class="badge">${attention.sync_errors?.length || 0}</span></button>
                    </div>
                    <div id="tab-content-all" class="tab-content" style="display: ${this.state.active_tab === 'all' ? 'block' : 'none'};">${this.render_quotes_table()}</div>
                    <div id="tab-content-attention" class="tab-content" style="display: ${this.state.active_tab === 'attention' ? 'block' : 'none'};">${this.render_attention_table(attention)}</div>
                    <div id="tab-content-errors" class="tab-content" style="display: ${this.state.active_tab === 'errors' ? 'block' : 'none'};">${this.render_errors_table(attention.sync_errors)}</div>
                </div>

                <!-- Footer Stats -->
                <div class="ops-panel" style="margin-bottom: 0;">
                    <div class="row">
                        <div class="col-md-2 col-sm-4 col-xs-6"><span style="color: #666;">Today:</span> <strong>${stats.quotes_today}</strong></div>
                        <div class="col-md-2 col-sm-4 col-xs-6"><span style="color: #666;">This Month:</span> <strong>${stats.quotes_this_month}</strong></div>
                        <div class="col-md-2 col-sm-4 col-xs-6"><span style="color: #666;">Monthly Value:</span> <strong style="color: #2e7d32;">${this.format_currency(stats.monthly_value)}</strong></div>
                        <div class="col-md-2 col-sm-4 col-xs-6"><span style="color: #666;">Win Rate:</span> <strong style="color: #1565c0;">${stats.acceptance_rate}%</strong></div>
                        <div class="col-md-2 col-sm-4 col-xs-6"><span style="color: #666;">Sync Pending:</span> <strong style="color: #f57c00;">${stats.sync_pending}</strong></div>
                        <div class="col-md-2 col-sm-4 col-xs-6"><span style="color: #666;">Sync Errors:</span> <strong style="color: #d32f2f;">${stats.sync_error}</strong></div>
                    </div>
                </div>
            </div>
        `;
        this.page.main.html(html);
        this.bind_events();
        this.render_charts();
        this.restore_filter_values();
    }

    render_pipeline(pipeline) {
        const statuses = ['Draft', 'Pending', 'Sent', 'Accepted'];
        const colors = { 'Draft': '#9e9e9e', 'Pending': '#ff9800', 'Sent': '#2196f3', 'Accepted': '#4caf50' };
        return statuses.map(status => {
            const data = pipeline[status] || { count: 0, value: 0 };
            return `<div class="col-md-3 col-sm-6" style="margin-bottom: 10px;">
                <div class="ops-pipeline-stage" style="background: ${colors[status]}15; border-color: ${colors[status]};" data-filter-status="${status}">
                    <div class="ops-pipeline-status" style="color: ${colors[status]};">${status}</div>
                    <div class="ops-pipeline-count">${data.count}</div>
                    <div class="ops-pipeline-value">${this.format_currency(data.value)}</div>
                </div>
            </div>`;
        }).join('');
    }

    render_quotes_table() {
        const list_data = this.data.quotes_list;
        if (!list_data || !list_data.quotes || list_data.quotes.length === 0) {
            return '<div class="ops-empty-state"><i class="fa fa-file-text-o"></i><p>No quotes found</p></div>';
        }
        const quotes = list_data.quotes;
        const sort_icon = (field) => this.state.sort_field === field ? `<i class="fa fa-sort-${this.state.sort_order === 'asc' ? 'up' : 'down'} sort-icon"></i>` : '<i class="fa fa-sort sort-icon"></i>';
        const sorted_class = (field) => this.state.sort_field === field ? 'sorted' : '';

        let html = `<table class="ops-table"><thead><tr>
            <th class="${sorted_class('quote_id')}" data-sort="quote_id">Quote ID ${sort_icon('quote_id')}</th>
            <th class="${sorted_class('customer_name')}" data-sort="customer_name">Customer ${sort_icon('customer_name')}</th>
            <th class="${sorted_class('quote_status')}" data-sort="quote_status">Status ${sort_icon('quote_status')}</th>
            <th class="${sorted_class('quote_price')}" data-sort="quote_price">Value ${sort_icon('quote_price')}</th>
            <th class="${sorted_class('profit_percentage')}" data-sort="profit_percentage">Profit % ${sort_icon('profit_percentage')}</th>
            <th class="${sorted_class('quote_date')}" data-sort="quote_date">Date ${sort_icon('quote_date')}</th>
            <th>Sync</th>
        </tr></thead><tbody>`;

        quotes.forEach(q => {
            html += `<tr>
                <td><a href="/app/ops-quote/${q.name}" style="font-weight: 600; color: var(--ops-primary);">${q.quote_id || q.name}</a>${q.quote_title ? `<div style="font-size: 11px; color: #666;">${this.truncate(q.quote_title, 30)}</div>` : ''}</td>
                <td><div>${q.customer_name || '-'}</div>${q.customer_company ? `<div style="font-size: 11px; color: #666;">${q.customer_company}</div>` : ''}</td>
                <td>${this.render_status_badge(q.quote_status)}</td>
                <td style="font-weight: 600;">${this.format_currency(q.quote_price)}</td>
                <td>${q.profit_percentage ? q.profit_percentage.toFixed(1) + '%' : '-'}</td>
                <td>${q.quote_date || '-'}</td>
                <td>${this.render_sync_badge(q.sync_status)}</td>
            </tr>`;
        });
        html += `</tbody></table>${this.render_pagination(list_data)}`;
        return html;
    }

    render_attention_table(attention) {
        const pending = attention.pending || [];
        const sent = attention.sent || [];
        const all = [...pending.map(q => ({...q, _type: 'Pending'})), ...sent.map(q => ({...q, _type: 'Sent'}))];
        if (all.length === 0) return '<div class="ops-empty-state"><i class="fa fa-check-circle"></i><p>No quotes need attention</p></div>';
        let html = '<table class="ops-table"><thead><tr><th>Quote ID</th><th>Customer</th><th>Status</th><th>Value</th><th>Date</th></tr></thead><tbody>';
        all.forEach(q => {
            html += `<tr><td><a href="/app/ops-quote/${q.name}" style="font-weight: 600; color: var(--ops-primary);">${q.quote_id || q.name}</a></td><td>${q.customer_name || '-'}</td><td>${this.render_status_badge(q._type)}</td><td style="font-weight: 600;">${this.format_currency(q.quote_price)}</td><td>${q.quote_date || '-'}</td></tr>`;
        });
        html += '</tbody></table>';
        return html;
    }

    render_errors_table(errors) {
        if (!errors || errors.length === 0) return '<div class="ops-empty-state"><i class="fa fa-check-circle"></i><p>No sync errors</p></div>';
        let html = '<table class="ops-table"><thead><tr><th>Quote ID</th><th>Customer</th><th>Error</th><th>Date</th></tr></thead><tbody>';
        errors.forEach(q => {
            html += `<tr><td><a href="/app/ops-quote/${q.name}" style="font-weight: 600; color: var(--ops-primary);">${q.quote_id || q.name}</a></td><td>${q.customer_name || '-'}</td><td style="color: #d32f2f; font-size: 12px;">${this.truncate(q.sync_error || 'Unknown', 50)}</td><td>${q.quote_date || '-'}</td></tr>`;
        });
        html += '</tbody></table>';
        return html;
    }

    render_pagination(list_data) {
        const total = list_data.total || 0;
        const offset = list_data.offset || 0;
        const limit = list_data.limit || 25;
        const current_page = Math.floor(offset / limit) + 1;
        const total_pages = Math.ceil(total / limit);
        const showing_from = total > 0 ? offset + 1 : 0;
        const showing_to = Math.min(offset + limit, total);
        return `<div class="ops-pagination">
            <div class="ops-pagination-info">Showing ${showing_from} - ${showing_to} of ${total} quotes</div>
            <div class="ops-pagination-btns">
                <button class="ops-pagination-btn" id="prev-page" ${current_page <= 1 ? 'disabled' : ''}><i class="fa fa-chevron-left"></i> Previous</button>
                <span style="padding: 6px 12px; color: #666;">Page ${current_page} of ${total_pages}</span>
                <button class="ops-pagination-btn" id="next-page" ${!list_data.has_more ? 'disabled' : ''}>Next <i class="fa fa-chevron-right"></i></button>
            </div>
        </div>`;
    }

    render_status_badge(status) {
        const colors = { 'Draft': '#9e9e9e', 'Pending': '#ff9800', 'Sent': '#2196f3', 'Accepted': '#4caf50', 'Rejected': '#f44336', 'Expired': '#607d8b', 'Converted': '#8bc34a', 'Cancelled': '#795548' };
        const color = colors[status] || '#999';
        return `<span class="ops-status-badge" style="background: ${color}20; color: ${color};">${status || 'Unknown'}</span>`;
    }

    render_sync_badge(sync_status) {
        const colors = { 'Synced': '#4caf50', 'Pending': '#ff9800', 'Error': '#f44336' };
        const color = colors[sync_status] || '#999';
        return `<span class="ops-status-badge" style="background: ${color}20; color: ${color};">${sync_status || '-'}</span>`;
    }

    render_charts() {
        // Check if frappe.Chart is available
        if (typeof frappe.Chart === 'undefined') {
            console.error('frappe.Chart is not available');
            return;
        }

        try {
            const by_status = this.data.stats.by_status || {};
            const status_colors = { 'Draft': '#9e9e9e', 'Pending': '#ff9800', 'Sent': '#2196f3', 'Accepted': '#4caf50', 'Rejected': '#f44336', 'Expired': '#607d8b', 'Converted': '#8bc34a', 'Cancelled': '#795548', 'Unknown': '#bdbdbd' };
            const labels = Object.keys(by_status);
            const values = Object.values(by_status);
            const colors = labels.map(s => status_colors[s] || '#999');
            if (labels.length > 0) {
                $('#status-chart').empty();
                new frappe.Chart('#status-chart', { data: { labels, datasets: [{ values }] }, type: 'pie', colors, height: 250 });
            }
            const timeline = this.data.timeline || {};
            const created = timeline.created || [];
            const converted = timeline.converted || [];
            if (created.length > 0) {
                const timeline_labels = created.map(d => d.date ? d.date.substring(5) : '');
                const created_values = created.map(d => d.count);
                const converted_map = {};
                converted.forEach(d => { if (d.date) converted_map[d.date] = d.count; });
                const converted_values = created.map(d => converted_map[d.date] || 0);
                $('#timeline-chart').empty();
                new frappe.Chart('#timeline-chart', { data: { labels: timeline_labels, datasets: [{ name: 'Created', values: created_values }, { name: 'Converted', values: converted_values }] }, type: 'line', colors: ['#667eea', '#43e97b'], height: 250, lineOptions: { regionFill: 1 } });
            }
        } catch (e) {
            console.error('Error rendering charts:', e);
        }
    }

    bind_events() {
        const me = this;
        const $main = this.page.main;
        $main.find('#apply-filters').on('click', () => me.apply_filters());
        $main.find('#clear-filters').on('click', () => me.clear_filters());
        $main.find('.ops-filter-group input').on('keypress', (e) => { if (e.which === 13) me.apply_filters(); });
        $main.find('.ops-tab').on('click', function() {
            const tab = $(this).data('tab');
            me.state.active_tab = tab;
            $main.find('.ops-tab').removeClass('active');
            $(this).addClass('active');
            $main.find('.tab-content').hide();
            $main.find(`#tab-content-${tab}`).show();
        });
        $main.find('.ops-table th[data-sort]').on('click', function() {
            const field = $(this).data('sort');
            if (me.state.sort_field === field) { me.state.sort_order = me.state.sort_order === 'asc' ? 'desc' : 'asc'; }
            else { me.state.sort_field = field; me.state.sort_order = 'desc'; }
            me.state.page = 0;
            me.refresh_quotes_list();
        });
        $main.find('#prev-page').on('click', () => { if (me.state.page > 0) { me.state.page--; me.refresh_quotes_list(); } });
        $main.find('#next-page').on('click', () => { if (me.data.quotes_list?.has_more) { me.state.page++; me.refresh_quotes_list(); } });
        $main.find('.ops-stat-card[data-filter-status]').on('click', function() { me.state.filters.status = $(this).data('filter-status'); me.state.page = 0; me.apply_filters(); });
        $main.find('.ops-pipeline-stage[data-filter-status]').on('click', function() { me.state.filters.status = $(this).data('filter-status'); me.state.page = 0; me.apply_filters(); });
    }

    restore_filter_values() {
        const $main = this.page.main;
        $main.find('#filter-status').val(this.state.filters.status);
        $main.find('#filter-date-from').val(this.state.filters.date_from);
        $main.find('#filter-date-to').val(this.state.filters.date_to);
        $main.find('#filter-customer').val(this.state.filters.customer);
        $main.find('#filter-value-min').val(this.state.filters.value_min);
        $main.find('#filter-value-max').val(this.state.filters.value_max);
        $main.find('#filter-sync-status').val(this.state.filters.sync_status);
    }

    apply_filters() {
        const $main = this.page.main;
        this.state.filters = {
            status: $main.find('#filter-status').val(), date_from: $main.find('#filter-date-from').val(), date_to: $main.find('#filter-date-to').val(),
            customer: $main.find('#filter-customer').val(), value_min: $main.find('#filter-value-min').val(), value_max: $main.find('#filter-value-max').val(),
            sync_status: $main.find('#filter-sync-status').val()
        };
        this.state.page = 0;
        this.refresh_quotes_list();
    }

    clear_filters() {
        this.state.filters = { status: '', date_from: '', date_to: '', customer: '', value_min: '', value_max: '', sync_status: '' };
        this.state.page = 0;
        this.restore_filter_values();
        this.refresh_quotes_list();
    }

    async refresh_quotes_list() {
        const me = this;
        const $table_container = this.page.main.find('#tab-content-all');
        $table_container.html('<div class="ops-loading"><i class="fa fa-spinner fa-spin"></i></div>');
        try {
            const res = await me.fetch_quotes_list();
            me.data.quotes_list = res.message;
            $table_container.html(me.render_quotes_table());
            me.bind_table_events();
        } catch (err) {
            console.error('Error refreshing quotes list:', err);
            $table_container.html('<div class="ops-empty-state"><p>Error loading quotes</p></div>');
        }
    }

    bind_table_events() {
        const me = this;
        const $main = this.page.main;
        $main.find('.ops-table th[data-sort]').off('click').on('click', function() {
            const field = $(this).data('sort');
            if (me.state.sort_field === field) { me.state.sort_order = me.state.sort_order === 'asc' ? 'desc' : 'asc'; }
            else { me.state.sort_field = field; me.state.sort_order = 'desc'; }
            me.state.page = 0;
            me.refresh_quotes_list();
        });
        $main.find('#prev-page').off('click').on('click', () => { if (me.state.page > 0) { me.state.page--; me.refresh_quotes_list(); } });
        $main.find('#next-page').off('click').on('click', () => { if (me.data.quotes_list?.has_more) { me.state.page++; me.refresh_quotes_list(); } });
    }

    toggle_auto_refresh() {
        this.auto_refresh_enabled = !this.auto_refresh_enabled;
        const $btn = this.page.inner_toolbar.find('.auto-refresh-btn');
        if (this.auto_refresh_enabled) { $btn.text(__('Auto-Refresh: ON')); this.start_auto_refresh(); }
        else { $btn.text(__('Auto-Refresh: OFF')); this.stop_auto_refresh(); }
    }

    start_auto_refresh() {
        if (this.refresh_interval) clearInterval(this.refresh_interval);
        this.refresh_interval = setInterval(() => { if (this.auto_refresh_enabled) this.load_dashboard(); }, this.REFRESH_INTERVAL_MS);
    }

    stop_auto_refresh() {
        if (this.refresh_interval) { clearInterval(this.refresh_interval); this.refresh_interval = null; }
    }

    export_quotes() {
        const quotes = this.data.quotes_list?.quotes || [];
        if (quotes.length === 0) { frappe.msgprint(__('No quotes to export')); return; }
        const headers = ['Quote ID', 'Title', 'Customer', 'Company', 'Status', 'Value', 'Profit %', 'Date', 'Sync Status'];
        const rows = quotes.map(q => [q.quote_id || q.name, q.quote_title || '', q.customer_name || '', q.customer_company || '', q.quote_status || '', q.quote_price || 0, q.profit_percentage || 0, q.quote_date || '', q.sync_status || '']);
        let csv = headers.join(',') + '\n';
        rows.forEach(row => { csv += row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',') + '\n'; });
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `quotes_export_${frappe.datetime.now_date()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    format_currency(value) {
        if (!value) return '$0.00';
        return '$' + parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    truncate(str, len) {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + '...' : str;
    }
}
