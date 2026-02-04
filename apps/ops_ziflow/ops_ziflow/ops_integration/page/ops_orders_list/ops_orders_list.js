/**
 * OPS Orders List - Professional View
 * Features:
 * - Customer details panel
 * - Dropdown action buttons
 * - Ziflow proof preview
 * - Product options & attributes display
 * - Professional card-based UI
 */

frappe.pages['ops-orders-list'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'OPS Orders',
        single_column: true
    });

    // Store state
    page.state = {
        orders: [],
        expanded: {},
        filters: {
            status: 'active',
            date_range: 'this_month',
            search: '',
            customer: ''
        },
        pagination: {
            page: 1,
            limit: 20,
            total: 0
        },
        sort: {
            field: 'name',
            order: 'desc'
        },
        selected: new Set()
    };

    // Primary actions
    page.set_primary_action(__('Refresh'), function() {
        load_orders(page, true);
    }, 'refresh');

    page.set_secondary_action(__('New Order'), function() {
        frappe.new_doc('OPS Order');
    });

    // Menu items
    page.add_menu_item(__('Orders Dashboard'), function() {
        frappe.set_route('ops-orders-dashboard');
    });
    page.add_menu_item(__('Cluster Dashboard'), function() {
        frappe.set_route('ops-cluster-dashboard');
    });
    page.add_menu_item(__('Sync Orders'), function() {
        sync_orders(page);
    });
    page.add_menu_item(__('Export Selected'), function() {
        export_selected(page);
    });
    page.add_menu_item(__('Bulk Update Status'), function() {
        bulk_update_status(page);
    });

    load_orders(page, true);
};

function sync_orders(page) {
    frappe.show_alert({ message: 'Syncing orders...', indicator: 'blue' });
    frappe.call({
        method: 'ops_ziflow.services.order_sync_service.sync_recent_orders',
        args: { limit: 50 },
        callback: function(r) {
            frappe.show_alert({ message: 'Synced ' + (r.message?.synced || 0) + ' orders', indicator: 'green' });
            load_orders(page, true);
        }
    });
}

function export_selected(page) {
    if (page.state.selected.size === 0) {
        frappe.msgprint('Please select orders to export');
        return;
    }
    var orders = Array.from(page.state.selected);
    frappe.set_route('query-report', 'OPS Orders Summary', { order_ids: orders.join(',') });
}

function bulk_update_status(page) {
    if (page.state.selected.size === 0) {
        frappe.msgprint('Please select orders to update');
        return;
    }

    var d = new frappe.ui.Dialog({
        title: 'Update Status',
        fields: [
            {
                fieldname: 'new_status',
                fieldtype: 'Select',
                label: 'New Status',
                reqd: 1,
                options: 'New Order\nIn Design\nOrder Processing\nOrder Review\nIn Production\nReady for Fulfillment\nFulfilled\nOrder Completed'
            }
        ],
        primary_action_label: 'Update',
        primary_action: function(values) {
            frappe.call({
                method: 'ops_ziflow.api.orders_list.bulk_update_status',
                args: {
                    orders: Array.from(page.state.selected),
                    status: values.new_status
                },
                callback: function(r) {
                    frappe.show_alert({ message: 'Updated ' + (r.message?.updated || 0) + ' orders', indicator: 'green' });
                    page.state.selected.clear();
                    load_orders(page, true);
                }
            });
            d.hide();
        }
    });
    d.show();
}

function get_date_filters(range) {
    var today = frappe.datetime.get_today();
    switch(range) {
        case 'today': return { from: today, to: today };
        case 'yesterday': var y = frappe.datetime.add_days(today, -1); return { from: y, to: y };
        case 'this_week': return { from: frappe.datetime.week_start(), to: today };
        case 'this_month': return { from: frappe.datetime.month_start(), to: today };
        case 'last_30': return { from: frappe.datetime.add_days(today, -30), to: today };
        case 'last_90': return { from: frappe.datetime.add_days(today, -90), to: today };
        case 'this_year': return { from: new Date().getFullYear() + '-01-01', to: today };
        case 'all': return { from: null, to: null };
        default: return { from: frappe.datetime.month_start(), to: today };
    }
}

function load_orders(page, show_loading) {
    if (show_loading) {
        page.main.html(get_loading_html());
    }

    var date_range = get_date_filters(page.state.filters.date_range);
    var status_filter = page.state.filters.status;

    // Build filters
    var filters = [];
    if (date_range.from) {
        filters.push(['date_purchased', '>=', date_range.from]);
    }
    if (date_range.to) {
        filters.push(['date_purchased', '<=', date_range.to + ' 23:59:59']);
    }
    if (status_filter === 'active') {
        filters.push(['order_status', 'not in', ['Order Completed', 'Fulfilled', 'Cancelled', 'Refunded']]);
    } else if (status_filter !== 'all') {
        filters.push(['order_status', '=', status_filter]);
    }
    if (page.state.filters.search) {
        filters.push(['ops_order_id', 'like', '%' + page.state.filters.search + '%']);
    }

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'OPS Order',
            filters: filters,
            fields: [
                'name', 'ops_order_id', 'customer_name', 'customer_email', 'customer_telephone',
                'customer_company', 'order_status', 'order_amount', 'date_purchased',
                'production_due_date', 'delivery_date', 'payment_status_title',
                'delivery_city', 'delivery_state', 'delivery_country',
                'pending_proof_count', 'all_proofs_approved', 'tracking_number', 'shipping_status'
            ],
            order_by: 'CAST(name AS UNSIGNED) ' + page.state.sort.order,
            limit_page_length: page.state.pagination.limit,
            limit_start: (page.state.pagination.page - 1) * page.state.pagination.limit
        },
        callback: function(r) {
            page.state.orders = r.message || [];

            // Get total count
            frappe.call({
                method: 'frappe.client.get_count',
                args: {
                    doctype: 'OPS Order',
                    filters: filters
                },
                async: false,
                callback: function(r2) {
                    page.state.pagination.total = r2.message || 0;
                }
            });

            render_page(page);
        }
    });
}

function get_loading_html() {
    return get_styles() + `
        <div class="ops-list-container">
            <div class="ops-loading">
                <div class="ops-loading-spinner"></div>
                <div class="ops-loading-text">Loading orders...</div>
            </div>
        </div>`;
}

function get_styles() {
    return `<style>
        :root {
            --ops-primary: #6366f1;
            --ops-success: #10b981;
            --ops-warning: #f59e0b;
            --ops-danger: #ef4444;
            --ops-info: #3b82f6;
            --ops-purple: #8b5cf6;
            --ops-dark: #1e293b;
            --ops-light: #f8fafc;
            --ops-border: #e2e8f0;
            --ops-shadow: 0 1px 3px rgba(0,0,0,0.1);
            --ops-shadow-lg: 0 4px 15px rgba(0,0,0,0.1);
        }

        .ops-list-container {
            background: linear-gradient(135deg, #f5f7fa 0%, #eef2f7 100%);
            min-height: calc(100vh - 60px);
            padding: 20px;
        }

        /* Filter Bar */
        .ops-filter-bar {
            background: white;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 16px;
            box-shadow: var(--ops-shadow);
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: flex-end;
        }

        .ops-filter-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .ops-filter-group label {
            font-size: 10px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .ops-filter-group select,
        .ops-filter-group input {
            padding: 8px 12px;
            border: 1px solid var(--ops-border);
            border-radius: 8px;
            font-size: 13px;
            min-width: 150px;
            transition: all 0.2s;
        }

        .ops-filter-group select:focus,
        .ops-filter-group input:focus {
            outline: none;
            border-color: var(--ops-primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .ops-filter-actions {
            margin-left: auto;
            display: flex;
            gap: 8px;
        }

        .ops-btn {
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .ops-btn.primary { background: var(--ops-primary); color: white; }
        .ops-btn.primary:hover { background: #4f46e5; transform: translateY(-1px); }
        .ops-btn.success { background: var(--ops-success); color: white; }
        .ops-btn.success:hover { background: #059669; }
        .ops-btn.secondary { background: #e2e8f0; color: #475569; }
        .ops-btn.secondary:hover { background: #cbd5e1; }
        .ops-btn.danger { background: var(--ops-danger); color: white; }
        .ops-btn.sm { padding: 5px 10px; font-size: 11px; }

        /* Stats Bar */
        .ops-stats-bar {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }

        .ops-stat-card {
            background: white;
            border-radius: 10px;
            padding: 14px 20px;
            box-shadow: var(--ops-shadow);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 140px;
        }

        .ops-stat-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }

        .ops-stat-icon.purple { background: #f3e8ff; color: #9333ea; }
        .ops-stat-icon.blue { background: #dbeafe; color: #2563eb; }
        .ops-stat-icon.green { background: #dcfce7; color: #16a34a; }
        .ops-stat-icon.orange { background: #ffedd5; color: #ea580c; }

        .ops-stat-value { font-size: 20px; font-weight: 700; color: var(--ops-dark); }
        .ops-stat-label { font-size: 11px; color: #64748b; }

        /* Orders List */
        .ops-orders-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        /* Order Card */
        .ops-order-card {
            background: white;
            border-radius: 12px;
            box-shadow: var(--ops-shadow);
            overflow: hidden;
            transition: all 0.2s;
            border-left: 4px solid var(--status-color, #94a3b8);
        }

        .ops-order-card:hover {
            box-shadow: var(--ops-shadow-lg);
        }

        .ops-order-card.expanded {
            box-shadow: var(--ops-shadow-lg);
        }

        .ops-order-header {
            display: flex;
            align-items: center;
            padding: 16px 20px;
            gap: 16px;
            cursor: pointer;
        }

        .ops-order-checkbox {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }

        .ops-order-id {
            font-weight: 700;
            color: var(--ops-primary);
            font-size: 14px;
            min-width: 100px;
            padding: 4px 8px;
            background: #eff6ff;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .ops-order-id:hover {
            background: var(--ops-primary);
            color: white;
        }

        .ops-order-customer {
            flex: 1;
            min-width: 200px;
        }

        .ops-customer-name {
            font-weight: 600;
            color: var(--ops-dark);
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .ops-customer-email {
            font-size: 12px;
            color: #64748b;
        }

        .ops-order-status {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .ops-order-status.new { background: #fff7ed; color: #ea580c; }
        .ops-order-status.design { background: #faf5ff; color: #9333ea; }
        .ops-order-status.processing { background: #eff6ff; color: #2563eb; }
        .ops-order-status.production { background: #fefce8; color: #ca8a04; }
        .ops-order-status.ready { background: #f0fdf4; color: #16a34a; }
        .ops-order-status.completed { background: #ecfdf5; color: #059669; }
        .ops-order-status.cancelled { background: #fef2f2; color: #dc2626; }

        .ops-order-amount {
            font-weight: 700;
            font-size: 16px;
            color: var(--ops-dark);
            min-width: 90px;
            text-align: right;
        }

        .ops-order-date {
            font-size: 12px;
            color: #64748b;
            min-width: 100px;
            text-align: center;
        }

        .ops-order-proofs {
            display: flex;
            align-items: center;
            gap: 4px;
            min-width: 70px;
        }

        .ops-proof-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 600;
        }

        .ops-proof-badge.pending { background: #fef3c7; color: #b45309; }
        .ops-proof-badge.approved { background: #dcfce7; color: #16a34a; }
        .ops-proof-badge.none { background: #f1f5f9; color: #64748b; }

        /* Dropdown Button */
        .ops-dropdown {
            position: relative;
        }

        .ops-dropdown-btn {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            border: 1px solid var(--ops-border);
            background: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .ops-dropdown-btn:hover {
            background: var(--ops-light);
            border-color: var(--ops-primary);
            color: var(--ops-primary);
        }

        .ops-dropdown-menu {
            position: absolute;
            right: 0;
            top: 100%;
            margin-top: 4px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            min-width: 180px;
            z-index: 1000;
            display: none;
            overflow: hidden;
        }

        .ops-dropdown-menu.show {
            display: block;
            animation: fadeIn 0.15s ease;
        }

        .ops-dropdown-item {
            padding: 10px 14px;
            font-size: 13px;
            color: #334155;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.15s;
        }

        .ops-dropdown-item:hover {
            background: var(--ops-light);
        }

        .ops-dropdown-item i {
            width: 16px;
            color: #64748b;
        }

        .ops-dropdown-divider {
            height: 1px;
            background: var(--ops-border);
            margin: 4px 0;
        }

        /* Expanded Details */
        .ops-order-details {
            display: none;
            border-top: 1px solid var(--ops-border);
            background: var(--ops-light);
            padding: 20px;
        }

        .ops-order-card.expanded .ops-order-details {
            display: block;
            animation: slideDown 0.2s ease;
        }

        .ops-details-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }

        @media (max-width: 1200px) {
            .ops-details-grid { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 768px) {
            .ops-details-grid { grid-template-columns: 1fr; }
        }

        .ops-detail-section {
            background: white;
            border-radius: 10px;
            padding: 16px;
            box-shadow: var(--ops-shadow);
        }

        .ops-detail-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--ops-primary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .ops-detail-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 13px;
            border-bottom: 1px dashed var(--ops-border);
        }

        .ops-detail-row:last-child {
            border-bottom: none;
        }

        .ops-detail-label {
            color: #64748b;
        }

        .ops-detail-value {
            font-weight: 500;
            color: var(--ops-dark);
        }

        /* Products Section */
        .ops-products-section {
            grid-column: span 2;
        }

        .ops-product-item {
            background: var(--ops-light);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .ops-product-item:last-child {
            margin-bottom: 0;
        }

        .ops-product-qty {
            background: var(--ops-primary);
            color: white;
            font-weight: 700;
            font-size: 12px;
            min-width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .ops-product-info {
            flex: 1;
        }

        .ops-product-name {
            font-weight: 600;
            font-size: 13px;
            color: var(--ops-dark);
        }

        .ops-product-sku {
            font-size: 11px;
            color: #64748b;
        }

        .ops-product-options {
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
        }

        .ops-product-price {
            font-weight: 700;
            font-size: 14px;
            color: var(--ops-dark);
        }

        /* Ziflow Preview */
        .ops-ziflow-section {
            grid-column: span 2;
        }

        .ops-proof-card {
            background: var(--ops-light);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .ops-proof-preview {
            width: 60px;
            height: 60px;
            border-radius: 8px;
            background: #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .ops-proof-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .ops-proof-preview i {
            font-size: 24px;
            color: #94a3b8;
        }

        .ops-proof-info {
            flex: 1;
        }

        .ops-proof-name {
            font-weight: 600;
            font-size: 13px;
            color: var(--ops-dark);
        }

        .ops-proof-status-tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
            margin-top: 4px;
        }

        .ops-proof-status-tag.pending { background: #fef3c7; color: #b45309; }
        .ops-proof-status-tag.approved { background: #dcfce7; color: #16a34a; }
        .ops-proof-status-tag.rejected { background: #fef2f2; color: #dc2626; }

        .ops-proof-link {
            color: var(--ops-primary);
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
        }

        .ops-proof-link:hover {
            text-decoration: underline;
        }

        /* Pagination */
        .ops-pagination {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 20px;
            padding: 16px 20px;
            background: white;
            border-radius: 12px;
            box-shadow: var(--ops-shadow);
        }

        .ops-page-info {
            font-size: 13px;
            color: #64748b;
        }

        .ops-page-buttons {
            display: flex;
            gap: 8px;
        }

        .ops-page-btn {
            padding: 8px 14px;
            border: 1px solid var(--ops-border);
            background: white;
            border-radius: 8px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .ops-page-btn:hover:not(:disabled) {
            border-color: var(--ops-primary);
            color: var(--ops-primary);
        }

        .ops-page-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .ops-page-btn.active {
            background: var(--ops-primary);
            color: white;
            border-color: var(--ops-primary);
        }

        /* Loading & Empty States */
        .ops-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 400px;
            gap: 16px;
        }

        .ops-loading-spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #e2e8f0;
            border-top-color: var(--ops-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        .ops-loading-text {
            color: #64748b;
            font-size: 14px;
        }

        .ops-empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #94a3b8;
        }

        .ops-empty-state i {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideDown {
            from { opacity: 0; max-height: 0; }
            to { opacity: 1; max-height: 1000px; }
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 992px) {
            .ops-order-header {
                flex-wrap: wrap;
            }
            .ops-order-customer {
                order: 2;
                width: 100%;
            }
            .ops-filter-bar {
                flex-direction: column;
                align-items: stretch;
            }
            .ops-filter-actions {
                margin-left: 0;
                margin-top: 10px;
            }
        }
    </style>`;
}

function render_page(page) {
    var orders = page.state.orders;
    var pagination = page.state.pagination;
    var filters = page.state.filters;

    var total_pages = Math.ceil(pagination.total / pagination.limit);

    var html = get_styles() + `
        <div class="ops-list-container">
            <!-- Filter Bar -->
            <div class="ops-filter-bar">
                <div class="ops-filter-group">
                    <label>Status</label>
                    <select id="filter-status">
                        <option value="active" ${filters.status === 'active' ? 'selected' : ''}>Active Orders</option>
                        <option value="all" ${filters.status === 'all' ? 'selected' : ''}>All Orders</option>
                        <option value="New Order" ${filters.status === 'New Order' ? 'selected' : ''}>New Order</option>
                        <option value="In Design" ${filters.status === 'In Design' ? 'selected' : ''}>In Design</option>
                        <option value="Order Processing" ${filters.status === 'Order Processing' ? 'selected' : ''}>Order Processing</option>
                        <option value="In Production" ${filters.status === 'In Production' ? 'selected' : ''}>In Production</option>
                        <option value="Ready for Fulfillment" ${filters.status === 'Ready for Fulfillment' ? 'selected' : ''}>Ready for Fulfillment</option>
                        <option value="Order Completed" ${filters.status === 'Order Completed' ? 'selected' : ''}>Completed</option>
                    </select>
                </div>
                <div class="ops-filter-group">
                    <label>Date Range</label>
                    <select id="filter-date">
                        <option value="today" ${filters.date_range === 'today' ? 'selected' : ''}>Today</option>
                        <option value="this_week" ${filters.date_range === 'this_week' ? 'selected' : ''}>This Week</option>
                        <option value="this_month" ${filters.date_range === 'this_month' ? 'selected' : ''}>This Month</option>
                        <option value="last_30" ${filters.date_range === 'last_30' ? 'selected' : ''}>Last 30 Days</option>
                        <option value="last_90" ${filters.date_range === 'last_90' ? 'selected' : ''}>Last 90 Days</option>
                        <option value="this_year" ${filters.date_range === 'this_year' ? 'selected' : ''}>This Year</option>
                        <option value="all" ${filters.date_range === 'all' ? 'selected' : ''}>All Time</option>
                    </select>
                </div>
                <div class="ops-filter-group">
                    <label>Search</label>
                    <input type="text" id="filter-search" placeholder="Order ID, Customer..." value="${filters.search || ''}">
                </div>
                <div class="ops-filter-actions">
                    <button class="ops-btn primary" id="btn-apply"><i class="fa fa-filter"></i> Apply</button>
                    <button class="ops-btn secondary" id="btn-reset"><i class="fa fa-times"></i> Reset</button>
                    <button class="ops-btn success" id="btn-sync"><i class="fa fa-cloud-download"></i> Sync</button>
                </div>
            </div>

            <!-- Stats Bar -->
            <div class="ops-stats-bar">
                <div class="ops-stat-card">
                    <div class="ops-stat-icon purple"><i class="fa fa-list"></i></div>
                    <div>
                        <div class="ops-stat-value">${pagination.total}</div>
                        <div class="ops-stat-label">Total Orders</div>
                    </div>
                </div>
                <div class="ops-stat-card">
                    <div class="ops-stat-icon blue"><i class="fa fa-check-square-o"></i></div>
                    <div>
                        <div class="ops-stat-value">${page.state.selected.size}</div>
                        <div class="ops-stat-label">Selected</div>
                    </div>
                </div>
                <div class="ops-stat-card">
                    <div class="ops-stat-icon green"><i class="fa fa-file"></i></div>
                    <div>
                        <div class="ops-stat-value">${pagination.page} / ${total_pages || 1}</div>
                        <div class="ops-stat-label">Page</div>
                    </div>
                </div>
            </div>

            <!-- Orders List -->
            <div class="ops-orders-list">
                ${orders.length === 0 ? `
                    <div class="ops-empty-state">
                        <i class="fa fa-inbox"></i>
                        <h3>No orders found</h3>
                        <p>Try adjusting your filters or date range</p>
                    </div>
                ` : orders.map(order => render_order_card(page, order)).join('')}
            </div>

            <!-- Pagination -->
            ${pagination.total > pagination.limit ? `
                <div class="ops-pagination">
                    <div class="ops-page-info">
                        Showing ${(pagination.page - 1) * pagination.limit + 1} - ${Math.min(pagination.page * pagination.limit, pagination.total)} of ${pagination.total}
                    </div>
                    <div class="ops-page-buttons">
                        <button class="ops-page-btn" id="btn-prev" ${pagination.page <= 1 ? 'disabled' : ''}>
                            <i class="fa fa-chevron-left"></i> Previous
                        </button>
                        <button class="ops-page-btn" id="btn-next" ${pagination.page >= total_pages ? 'disabled' : ''}>
                            Next <i class="fa fa-chevron-right"></i>
                        </button>
                    </div>
                </div>
            ` : ''}
        </div>`;

    page.main.html(html);
    setup_handlers(page);
}

function get_status_color(status) {
    var colors = {
        'New Order': '#f97316',
        'In Design': '#9333ea',
        'Order Processing': '#2563eb',
        'Order Review': '#0891b2',
        'In Production': '#ca8a04',
        'Ready for Fulfillment': '#16a34a',
        'Fulfilled': '#059669',
        'Order Completed': '#22c55e',
        'Cancelled': '#dc2626',
        'Refunded': '#ef4444'
    };
    return colors[status] || '#94a3b8';
}

function get_status_class(status) {
    var classes = {
        'New Order': 'new',
        'In Design': 'design',
        'Order Processing': 'processing',
        'Order Review': 'processing',
        'In Production': 'production',
        'Ready for Fulfillment': 'ready',
        'Fulfilled': 'completed',
        'Order Completed': 'completed',
        'Cancelled': 'cancelled',
        'Refunded': 'cancelled'
    };
    return classes[status] || '';
}

function format_currency(value) {
    if (!value) return '$0.00';
    return '$' + parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function format_date(date) {
    if (!date) return '-';
    return frappe.datetime.str_to_user(date.split(' ')[0]);
}

function render_order_card(page, order) {
    var is_expanded = page.state.expanded[order.name];
    var is_selected = page.state.selected.has(order.name);
    var status_color = get_status_color(order.order_status);
    var status_class = get_status_class(order.order_status);

    var proof_badge = '';
    if (order.pending_proof_count > 0 && !order.all_proofs_approved) {
        proof_badge = `<span class="ops-proof-badge pending"><i class="fa fa-clock-o"></i> ${order.pending_proof_count}</span>`;
    } else if (order.all_proofs_approved) {
        proof_badge = `<span class="ops-proof-badge approved"><i class="fa fa-check"></i> Done</span>`;
    } else {
        proof_badge = `<span class="ops-proof-badge none">-</span>`;
    }

    return `
        <div class="ops-order-card ${is_expanded ? 'expanded' : ''}" data-order="${order.name}" style="--status-color: ${status_color}">
            <div class="ops-order-header">
                <input type="checkbox" class="ops-order-checkbox" data-order="${order.name}" ${is_selected ? 'checked' : ''}>

                <div class="ops-order-id" onclick="frappe.set_route('ops-order-view', '${order.name}')">
                    #${order.ops_order_id || order.name}
                </div>

                <div class="ops-order-customer">
                    <div class="ops-customer-name">
                        <i class="fa fa-user-circle-o"></i>
                        ${order.customer_name || 'Unknown'}
                    </div>
                    <div class="ops-customer-email">${order.customer_email || ''}</div>
                </div>

                <span class="ops-order-status ${status_class}">${order.order_status || 'Unknown'}</span>

                <div class="ops-order-proofs">${proof_badge}</div>

                <div class="ops-order-date">
                    <i class="fa fa-calendar-o"></i> ${format_date(order.date_purchased)}
                </div>

                <div class="ops-order-amount">${format_currency(order.order_amount)}</div>

                <!-- Dropdown Button -->
                <div class="ops-dropdown">
                    <button class="ops-dropdown-btn" onclick="toggleDropdown(event, '${order.name}')">
                        <i class="fa fa-ellipsis-v"></i>
                    </button>
                    <div class="ops-dropdown-menu" id="dropdown-${order.name}">
                        <div class="ops-dropdown-item" onclick="frappe.set_route('ops-order-view', '${order.name}')">
                            <i class="fa fa-eye"></i> View Order
                        </div>
                        <div class="ops-dropdown-item" onclick="window.open('/printview?doctype=OPS Order&name=${order.name}&format=Standard', '_blank')">
                            <i class="fa fa-print"></i> Print
                        </div>
                        <div class="ops-dropdown-divider"></div>
                        <div class="ops-dropdown-item" onclick="viewProofs('${order.name}')">
                            <i class="fa fa-file-image-o"></i> View Proofs
                        </div>
                        <div class="ops-dropdown-item" onclick="viewCustomer('${order.customer_company || ''}')">
                            <i class="fa fa-user"></i> Customer Details
                        </div>
                        <div class="ops-dropdown-divider"></div>
                        <div class="ops-dropdown-item" onclick="updateOrderStatus('${order.name}')">
                            <i class="fa fa-refresh"></i> Update Status
                        </div>
                        ${order.tracking_number ? `
                            <div class="ops-dropdown-item" onclick="window.open('${order.tracking_url || '#'}', '_blank')">
                                <i class="fa fa-truck"></i> Track Shipment
                            </div>
                        ` : ''}
                    </div>
                </div>

                <button class="ops-dropdown-btn" onclick="toggleOrderDetails('${order.name}')" title="Expand">
                    <i class="fa fa-chevron-${is_expanded ? 'up' : 'down'}"></i>
                </button>
            </div>

            <div class="ops-order-details" id="details-${order.name}">
                <!-- Details loaded on expand -->
            </div>
        </div>`;
}

function setup_handlers(page) {
    // Filter handlers
    page.main.find('#btn-apply').on('click', function() {
        page.state.filters.status = page.main.find('#filter-status').val();
        page.state.filters.date_range = page.main.find('#filter-date').val();
        page.state.filters.search = page.main.find('#filter-search').val();
        page.state.pagination.page = 1;
        load_orders(page, true);
    });

    page.main.find('#btn-reset').on('click', function() {
        page.state.filters = { status: 'active', date_range: 'this_month', search: '', customer: '' };
        page.state.pagination.page = 1;
        load_orders(page, true);
    });

    page.main.find('#btn-sync').on('click', function() {
        sync_orders(page);
    });

    // Auto-apply on filter change
    page.main.find('#filter-status, #filter-date').on('change', function() {
        page.main.find('#btn-apply').click();
    });

    // Search on enter
    page.main.find('#filter-search').on('keypress', function(e) {
        if (e.which === 13) page.main.find('#btn-apply').click();
    });

    // Checkbox handlers
    page.main.find('.ops-order-checkbox').on('change', function(e) {
        e.stopPropagation();
        var order = $(this).data('order');
        if (this.checked) {
            page.state.selected.add(order);
        } else {
            page.state.selected.delete(order);
        }
        // Update stats
        page.main.find('.ops-stat-card:eq(1) .ops-stat-value').text(page.state.selected.size);
    });

    // Pagination
    page.main.find('#btn-prev').on('click', function() {
        if (page.state.pagination.page > 1) {
            page.state.pagination.page--;
            load_orders(page, true);
        }
    });

    page.main.find('#btn-next').on('click', function() {
        var total_pages = Math.ceil(page.state.pagination.total / page.state.pagination.limit);
        if (page.state.pagination.page < total_pages) {
            page.state.pagination.page++;
            load_orders(page, true);
        }
    });
}

// Global functions for onclick handlers
window.toggleDropdown = function(e, order) {
    e.stopPropagation();
    var menu = document.getElementById('dropdown-' + order);

    // Close all other dropdowns
    document.querySelectorAll('.ops-dropdown-menu').forEach(function(m) {
        if (m.id !== 'dropdown-' + order) m.classList.remove('show');
    });

    menu.classList.toggle('show');

    // Close on click outside
    setTimeout(function() {
        document.addEventListener('click', function closeDropdown() {
            menu.classList.remove('show');
            document.removeEventListener('click', closeDropdown);
        });
    }, 0);
};

window.toggleOrderDetails = function(order) {
    var card = document.querySelector('.ops-order-card[data-order="' + order + '"]');
    var details = document.getElementById('details-' + order);
    var isExpanded = card.classList.contains('expanded');

    if (isExpanded) {
        card.classList.remove('expanded');
    } else {
        card.classList.add('expanded');
        // Load details if not loaded
        if (!details.innerHTML.trim()) {
            loadOrderDetails(order, details);
        }
    }
};

window.loadOrderDetails = function(order, container) {
    container.innerHTML = '<div style="padding: 20px; text-align: center;"><i class="fa fa-spinner fa-spin"></i> Loading...</div>';

    // Get order with products
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'OPS Order',
            name: order
        },
        callback: function(r) {
            var doc = r.message;
            if (!doc) {
                container.innerHTML = '<div style="padding: 20px; text-align: center; color: #ef4444;">Error loading details</div>';
                return;
            }

            // Also get proofs for this order
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'OPS ZiFlow Proof',
                    filters: { ops_order: order },
                    fields: ['name', 'proof_name', 'proof_status', 'ziflow_url', 'preview_url']
                },
                callback: function(r2) {
                    var proofs = r2.message || [];
                    container.innerHTML = render_order_details(doc, proofs);
                }
            });
        }
    });
};

function render_order_details(doc, proofs) {
    var products = doc.ops_order_products || [];

    return `
        <div class="ops-details-grid">
            <!-- Customer Details -->
            <div class="ops-detail-section">
                <div class="ops-detail-title"><i class="fa fa-user"></i> Customer</div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Name</span>
                    <span class="ops-detail-value">${doc.customer_name || '-'}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Company</span>
                    <span class="ops-detail-value">${doc.delivery_company || '-'}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Email</span>
                    <span class="ops-detail-value">${doc.customer_email || '-'}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Phone</span>
                    <span class="ops-detail-value">${doc.customer_telephone || '-'}</span>
                </div>
            </div>

            <!-- Shipping -->
            <div class="ops-detail-section">
                <div class="ops-detail-title"><i class="fa fa-truck"></i> Shipping</div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Address</span>
                    <span class="ops-detail-value">${doc.delivery_street_address || '-'}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">City</span>
                    <span class="ops-detail-value">${doc.delivery_city || ''}, ${doc.delivery_state || ''} ${doc.delivery_postcode || ''}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Tracking</span>
                    <span class="ops-detail-value">${doc.tracking_number ? '<a href="' + (doc.tracking_url || '#') + '" target="_blank">' + doc.tracking_number + '</a>' : '-'}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Status</span>
                    <span class="ops-detail-value">${doc.shipping_status || 'Pending'}</span>
                </div>
            </div>

            <!-- Payment -->
            <div class="ops-detail-section">
                <div class="ops-detail-title"><i class="fa fa-credit-card"></i> Payment</div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Subtotal</span>
                    <span class="ops-detail-value">$${(doc.order_amount || 0).toFixed(2)}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Shipping</span>
                    <span class="ops-detail-value">$${(doc.shipping_amount || 0).toFixed(2)}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Tax</span>
                    <span class="ops-detail-value">$${(doc.tax_amount || 0).toFixed(2)}</span>
                </div>
                <div class="ops-detail-row" style="font-weight: 700;">
                    <span class="ops-detail-label">Total</span>
                    <span class="ops-detail-value">$${(doc.total_amount || 0).toFixed(2)}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Status</span>
                    <span class="ops-detail-value" style="color: ${doc.payment_status_title === 'Paid' ? '#16a34a' : '#ea580c'}">${doc.payment_status_title || '-'}</span>
                </div>
            </div>

            <!-- Dates -->
            <div class="ops-detail-section">
                <div class="ops-detail-title"><i class="fa fa-calendar"></i> Dates</div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Ordered</span>
                    <span class="ops-detail-value">${doc.date_purchased ? frappe.datetime.str_to_user(doc.date_purchased.split(' ')[0]) : '-'}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Production Due</span>
                    <span class="ops-detail-value">${doc.production_due_date ? frappe.datetime.str_to_user(doc.production_due_date) : '-'}</span>
                </div>
                <div class="ops-detail-row">
                    <span class="ops-detail-label">Delivery</span>
                    <span class="ops-detail-value">${doc.delivery_date ? frappe.datetime.str_to_user(doc.delivery_date) : '-'}</span>
                </div>
            </div>

            <!-- Products -->
            <div class="ops-detail-section ops-products-section">
                <div class="ops-detail-title"><i class="fa fa-cube"></i> Products (${products.length})</div>
                ${products.length === 0 ? '<div style="color: #94a3b8; font-size: 13px;">No products</div>' : products.map(function(p) {
                    return `
                        <div class="ops-product-item">
                            <div class="ops-product-qty">${p.products_quantity || 1}</div>
                            <div class="ops-product-info">
                                <div class="ops-product-name">${p.products_name || p.products_title || 'Unknown Product'}</div>
                                <div class="ops-product-sku">SKU: ${p.products_sku || '-'}</div>
                                ${p.product_width && p.product_height ? '<div class="ops-product-options">Size: ' + p.product_width + ' x ' + p.product_height + ' ' + (p.product_size_unit || '') + '</div>' : ''}
                            </div>
                            <div class="ops-product-price">$${(p.final_price || 0).toFixed(2)}</div>
                        </div>
                    `;
                }).join('')}
            </div>

            <!-- Ziflow Proofs -->
            <div class="ops-detail-section ops-ziflow-section">
                <div class="ops-detail-title"><i class="fa fa-file-image-o"></i> Ziflow Proofs (${proofs.length})</div>
                ${proofs.length === 0 ? '<div style="color: #94a3b8; font-size: 13px;">No proofs attached</div>' : proofs.map(function(p) {
                    var statusClass = p.proof_status === 'Approved' ? 'approved' : (p.proof_status === 'Rejected' ? 'rejected' : 'pending');
                    return `
                        <div class="ops-proof-card">
                            <div class="ops-proof-preview">
                                ${p.preview_url ? '<img src="' + p.preview_url + '" alt="Preview">' : '<i class="fa fa-file-image-o"></i>'}
                            </div>
                            <div class="ops-proof-info">
                                <div class="ops-proof-name">${p.proof_name || p.name}</div>
                                <span class="ops-proof-status-tag ${statusClass}">${p.proof_status || 'Pending'}</span>
                            </div>
                            ${p.ziflow_url ? '<a class="ops-proof-link" href="' + p.ziflow_url + '" target="_blank"><i class="fa fa-external-link"></i> Open in Ziflow</a>' : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

window.viewProofs = function(order) {
    frappe.set_route('List', 'OPS ZiFlow Proof', { ops_order: order });
};

window.viewCustomer = function(customer) {
    if (customer) {
        frappe.set_route('Form', 'OPS Customer', customer);
    } else {
        frappe.msgprint('No customer linked to this order');
    }
};

window.updateOrderStatus = function(order) {
    var d = new frappe.ui.Dialog({
        title: 'Update Order Status',
        fields: [
            {
                fieldname: 'status',
                fieldtype: 'Select',
                label: 'New Status',
                reqd: 1,
                options: 'New Order\nIn Design\nOrder Processing\nOrder Review\nIn Production\nReady for Fulfillment\nFulfilled\nOrder Completed\nCancelled'
            }
        ],
        primary_action_label: 'Update',
        primary_action: function(values) {
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'OPS Order',
                    name: order,
                    fieldname: 'order_status',
                    value: values.status
                },
                callback: function() {
                    frappe.show_alert({ message: 'Status updated', indicator: 'green' });
                    location.reload();
                }
            });
            d.hide();
        }
    });
    d.show();
};
