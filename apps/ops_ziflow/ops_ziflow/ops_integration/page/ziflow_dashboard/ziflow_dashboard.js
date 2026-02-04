frappe.pages['ziflow-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'ZiFlow Dashboard',
        single_column: true
    });

    // Inject Nexus-style premium styles
    inject_nexus_styles();

    page.main.html(get_dashboard_html());

    // Add page buttons
    page.set_primary_action(__('View All Proofs'), function() {
        frappe.set_route('List', 'OPS ZiFlow Proof');
    }, 'fa fa-list');

    page.add_inner_button(__('Refresh'), function() {
        load_dashboard_data(page);
    }, 'fa fa-refresh');

    page.add_inner_button(__('Sync Now'), function() {
        frappe.call({
            method: 'ops_ziflow.services.sync_service.poll_pending_proofs',
            freeze: true,
            freeze_message: __('Syncing proofs from ZiFlow...'),
            callback: function(r) {
                frappe.show_alert({message: __('Sync completed'), indicator: 'green'});
                load_dashboard_data(page);
            }
        });
    }, 'fa fa-cloud-download');

    setup_card_click_handlers(page);
    load_dashboard_data(page);

    // Entrance animations
    setTimeout(function() {
        page.main.find('.nexus-stat-card').each(function(index) {
            var card = $(this);
            setTimeout(function() {
                card.addClass('animate-in');
            }, index * 60);
        });
        page.main.find('.nexus-panel').each(function(index) {
            var panel = $(this);
            setTimeout(function() {
                panel.addClass('animate-in');
            }, 300 + index * 80);
        });
    }, 100);
};

function inject_nexus_styles() {
    if (document.getElementById('nexus-dashboard-styles')) return;

    var styles = document.createElement('style');
    styles.id = 'nexus-dashboard-styles';
    styles.textContent = `
        /* Nexus SaaS Dashboard Theme */
        .nexus-dashboard {
            min-height: 100vh;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
            padding: 28px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        /* Dashboard Header */
        .nexus-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 32px;
        }

        .nexus-header-left h1 {
            font-size: 28px;
            font-weight: 700;
            color: #1a1f36;
            margin: 0 0 6px 0;
            letter-spacing: -0.5px;
        }

        .nexus-header-left p {
            color: #6b7294;
            font-size: 14px;
            margin: 0;
        }

        .nexus-header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .nexus-live-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 50px;
            color: #fff;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }

        .nexus-live-badge .pulse {
            width: 8px;
            height: 8px;
            background: #fff;
            border-radius: 50%;
            animation: pulse-ring 2s infinite;
        }

        @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
        }

        /* Stats Grid */
        .nexus-stats-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 20px;
            margin-bottom: 28px;
        }

        @media (max-width: 1400px) {
            .nexus-stats-grid { grid-template-columns: repeat(3, 1fr); }
        }

        @media (max-width: 768px) {
            .nexus-stats-grid { grid-template-columns: repeat(2, 1fr); }
        }

        /* Stat Cards - Nexus Style */
        .nexus-stat-card {
            background: #fff;
            border-radius: 20px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            cursor: pointer;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04),
                        0 4px 12px rgba(0, 0, 0, 0.04);
        }

        .nexus-stat-card.animate-in {
            opacity: 1;
            transform: translateY(0);
        }

        .nexus-stat-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08),
                        0 20px 50px rgba(0, 0, 0, 0.06);
        }

        .nexus-stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--card-gradient);
            border-radius: 20px 20px 0 0;
        }

        .nexus-stat-card .card-icon {
            width: 52px;
            height: 52px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 18px;
            background: var(--icon-bg);
            position: relative;
        }

        .nexus-stat-card .card-icon::after {
            content: '';
            position: absolute;
            inset: -3px;
            border-radius: 16px;
            background: var(--card-gradient);
            opacity: 0.15;
            z-index: -1;
        }

        .nexus-stat-card .card-icon i {
            font-size: 22px;
            background: var(--card-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .nexus-stat-card .card-label {
            font-size: 13px;
            color: #6b7294;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .nexus-stat-card .card-value {
            font-size: 32px;
            font-weight: 700;
            color: #1a1f36;
            line-height: 1;
            margin-bottom: 8px;
        }

        .nexus-stat-card .card-subtitle {
            font-size: 12px;
            color: #9ca3c4;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .nexus-stat-card .card-subtitle .trend {
            display: inline-flex;
            align-items: center;
            gap: 3px;
            padding: 3px 8px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 11px;
        }

        .nexus-stat-card .card-subtitle .trend.up {
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
        }

        .nexus-stat-card .card-subtitle .trend.down {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
        }

        /* Card color variants */
        .nexus-stat-card.purple {
            --card-gradient: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
            --icon-bg: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
        }
        .nexus-stat-card.amber {
            --card-gradient: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
            --icon-bg: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(249, 115, 22, 0.1) 100%);
        }
        .nexus-stat-card.emerald {
            --card-gradient: linear-gradient(135deg, #10b981 0%, #14b8a6 100%);
            --icon-bg: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%);
        }
        .nexus-stat-card.rose {
            --card-gradient: linear-gradient(135deg, #f43f5e 0%, #ec4899 100%);
            --icon-bg: linear-gradient(135deg, rgba(244, 63, 94, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
        }
        .nexus-stat-card.violet {
            --card-gradient: linear-gradient(135deg, #a855f7 0%, #8b5cf6 100%);
            --icon-bg: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        }
        .nexus-stat-card.cyan {
            --card-gradient: linear-gradient(135deg, #06b6d4 0%, #0ea5e9 100%);
            --icon-bg: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%);
        }

        /* Content Grid */
        .nexus-content-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (max-width: 1200px) {
            .nexus-content-grid { grid-template-columns: 1fr; }
        }

        /* Panels */
        .nexus-panel {
            background: #fff;
            border-radius: 20px;
            overflow: hidden;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04),
                        0 4px 12px rgba(0, 0, 0, 0.04);
        }

        .nexus-panel.animate-in {
            opacity: 1;
            transform: translateY(0);
        }

        .nexus-panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 24px;
            border-bottom: 1px solid #f1f3f9;
        }

        .nexus-panel-header h3 {
            font-size: 16px;
            font-weight: 600;
            color: #1a1f36;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .nexus-panel-header h3 .icon-wrapper {
            width: 32px;
            height: 32px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        }

        .nexus-panel-header h3 .icon-wrapper i {
            font-size: 14px;
            color: #fff;
        }

        .nexus-panel-header .badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
            color: #8b5cf6;
        }

        .nexus-panel-header .view-all {
            font-size: 13px;
            color: #8b5cf6;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }

        .nexus-panel-header .view-all:hover {
            color: #6366f1;
        }

        .nexus-panel-body {
            padding: 20px 24px;
        }

        /* Status Chart */
        .nexus-status-item {
            margin-bottom: 18px;
        }

        .nexus-status-item:last-child {
            margin-bottom: 0;
        }

        .nexus-status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .nexus-status-label {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: #1a1f36;
            font-weight: 500;
        }

        .nexus-status-label .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .nexus-status-value {
            font-size: 14px;
            color: #6b7294;
            font-weight: 500;
        }

        .nexus-status-bar {
            height: 10px;
            background: #f1f3f9;
            border-radius: 10px;
            overflow: hidden;
        }

        .nexus-status-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .nexus-status-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            animation: shine 2s infinite;
        }

        @keyframes shine {
            100% { left: 100%; }
        }

        /* Timeline Chart */
        .nexus-timeline {
            height: 220px;
            display: flex;
            align-items: flex-end;
            gap: 8px;
            padding: 20px 0;
        }

        .nexus-bar-group {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }

        .nexus-bars {
            display: flex;
            gap: 4px;
            align-items: flex-end;
            height: 160px;
        }

        .nexus-bar {
            width: 16px;
            border-radius: 6px 6px 0 0;
            transition: all 0.3s ease;
            position: relative;
        }

        .nexus-bar:hover {
            transform: scaleY(1.05);
            filter: brightness(1.1);
        }

        .nexus-bar.created {
            background: linear-gradient(180deg, #8b5cf6 0%, #6366f1 100%);
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        }

        .nexus-bar.approved {
            background: linear-gradient(180deg, #10b981 0%, #14b8a6 100%);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }

        .nexus-date {
            font-size: 11px;
            color: #9ca3c4;
            font-weight: 500;
        }

        .nexus-legend {
            display: flex;
            justify-content: center;
            gap: 28px;
            padding-top: 16px;
            border-top: 1px solid #f1f3f9;
        }

        .nexus-legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: #6b7294;
            font-weight: 500;
        }

        .nexus-legend-dot {
            width: 12px;
            height: 12px;
            border-radius: 4px;
        }

        .nexus-legend-value {
            font-weight: 700;
            color: #1a1f36;
            margin-left: 4px;
        }

        /* Two Column Grid */
        .nexus-two-col {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (max-width: 992px) {
            .nexus-two-col { grid-template-columns: 1fr; }
        }

        /* Proof List */
        .nexus-proof-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .nexus-proof-list::-webkit-scrollbar {
            width: 6px;
        }

        .nexus-proof-list::-webkit-scrollbar-track {
            background: #f1f3f9;
            border-radius: 3px;
        }

        .nexus-proof-list::-webkit-scrollbar-thumb {
            background: #d1d5e4;
            border-radius: 3px;
        }

        .nexus-proof-item {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px;
            border-radius: 14px;
            margin-bottom: 8px;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .nexus-proof-item:last-child {
            margin-bottom: 0;
        }

        .nexus-proof-item:hover {
            background: #f8f9fc;
        }

        .nexus-proof-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
            flex-shrink: 0;
        }

        .nexus-proof-icon i {
            font-size: 20px;
            color: #8b5cf6;
        }

        .nexus-proof-content {
            flex: 1;
            min-width: 0;
        }

        .nexus-proof-title {
            font-size: 14px;
            font-weight: 600;
            color: #1a1f36;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .nexus-proof-title a {
            color: inherit;
            text-decoration: none;
        }

        .nexus-proof-title a:hover {
            color: #8b5cf6;
        }

        .nexus-proof-meta {
            font-size: 12px;
            color: #9ca3c4;
        }

        .nexus-proof-meta a {
            color: #8b5cf6;
            text-decoration: none;
        }

        .nexus-proof-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Status Pills */
        .nexus-status-pill {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: capitalize;
        }

        .nexus-status-pill.approved {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%);
            color: #10b981;
        }

        .nexus-status-pill.in-review {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(249, 115, 22, 0.1) 100%);
            color: #f59e0b;
        }

        .nexus-status-pill.rejected {
            background: linear-gradient(135deg, rgba(244, 63, 94, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            color: #f43f5e;
        }

        .nexus-status-pill.draft {
            background: rgba(107, 114, 148, 0.1);
            color: #6b7294;
        }

        .nexus-status-pill.changes {
            background: linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(234, 88, 12, 0.1) 100%);
            color: #f97316;
        }

        .nexus-btn-icon {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8f9fc;
            border: 1px solid #e8ebf4;
            color: #6b7294;
            transition: all 0.2s ease;
            text-decoration: none;
        }

        .nexus-btn-icon:hover {
            background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
            border-color: transparent;
            color: #fff;
        }

        /* Orders Table */
        .nexus-table {
            width: 100%;
            border-collapse: collapse;
        }

        .nexus-table thead th {
            padding: 14px 16px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #9ca3c4;
            font-weight: 600;
            text-align: left;
            border-bottom: 1px solid #f1f3f9;
            background: #fafbfd;
        }

        .nexus-table tbody td {
            padding: 16px;
            font-size: 14px;
            color: #1a1f36;
            border-bottom: 1px solid #f1f3f9;
        }

        .nexus-table tbody tr:last-child td {
            border-bottom: none;
        }

        .nexus-table tbody tr:hover td {
            background: #fafbfd;
        }

        .nexus-table a {
            color: #8b5cf6;
            text-decoration: none;
            font-weight: 500;
        }

        .nexus-table a:hover {
            color: #6366f1;
        }

        .nexus-badge-count {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 28px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(249, 115, 22, 0.15) 100%);
            color: #f59e0b;
        }

        .nexus-btn-sm {
            padding: 8px 18px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 500;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
            color: #8b5cf6;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            display: inline-block;
        }

        .nexus-btn-sm:hover {
            background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
            color: #fff;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        }

        /* Empty State */
        .nexus-empty {
            text-align: center;
            padding: 48px 24px;
        }

        .nexus-empty-icon {
            width: 72px;
            height: 72px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
        }

        .nexus-empty-icon i {
            font-size: 28px;
            color: #8b5cf6;
        }

        .nexus-empty p {
            color: #6b7294;
            font-size: 14px;
            margin: 0;
        }

        .nexus-empty.success .nexus-empty-icon {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%);
        }

        .nexus-empty.success .nexus-empty-icon i {
            color: #10b981;
        }

        .nexus-empty.success p {
            color: #10b981;
        }

        /* Deadline */
        .deadline-urgent {
            color: #f43f5e;
            font-weight: 600;
        }

        /* Table container scroll */
        .nexus-table-container {
            max-height: 350px;
            overflow-y: auto;
        }

        .nexus-table-container::-webkit-scrollbar {
            width: 6px;
        }

        .nexus-table-container::-webkit-scrollbar-track {
            background: #f1f3f9;
        }

        .nexus-table-container::-webkit-scrollbar-thumb {
            background: #d1d5e4;
            border-radius: 3px;
        }
    `;
    document.head.appendChild(styles);
}

function get_dashboard_html() {
    return `
        <div class="nexus-dashboard">
            <!-- Header -->
            <div class="nexus-header">
                <div class="nexus-header-left">
                    <h1>ZiFlow Command Center</h1>
                    <p>Real-time proofing analytics and workflow management</p>
                </div>
                <div class="nexus-header-right">
                    <div class="nexus-live-badge">
                        <span class="pulse"></span>
                        <span>Live Dashboard</span>
                    </div>
                </div>
            </div>

            <!-- Stats Grid -->
            <div class="nexus-stats-grid">
                <div class="nexus-stat-card purple" id="total-proofs-card">
                    <div class="card-icon"><i class="fa fa-files-o"></i></div>
                    <div class="card-label">Total Proofs</div>
                    <div class="card-value" id="total-proofs-count">0</div>
                    <div class="card-subtitle">
                        <span class="trend up"><i class="fa fa-arrow-up"></i> All time</span>
                    </div>
                </div>
                <div class="nexus-stat-card amber" id="pending-card">
                    <div class="card-icon"><i class="fa fa-clock-o"></i></div>
                    <div class="card-label">Pending Review</div>
                    <div class="card-value" id="pending-count">0</div>
                    <div class="card-subtitle">Awaiting action</div>
                </div>
                <div class="nexus-stat-card emerald" id="approved-card">
                    <div class="card-icon"><i class="fa fa-check-circle"></i></div>
                    <div class="card-label">Approved</div>
                    <div class="card-value" id="approved-count">0</div>
                    <div class="card-subtitle">Ready for production</div>
                </div>
                <div class="nexus-stat-card rose" id="rejected-card">
                    <div class="card-icon"><i class="fa fa-times-circle"></i></div>
                    <div class="card-label">Rejected</div>
                    <div class="card-value" id="rejected-count">0</div>
                    <div class="card-subtitle">Needs revision</div>
                </div>
                <div class="nexus-stat-card violet" id="overdue-card">
                    <div class="card-icon"><i class="fa fa-exclamation-triangle"></i></div>
                    <div class="card-label">Overdue</div>
                    <div class="card-value" id="overdue-count">0</div>
                    <div class="card-subtitle">Past deadline</div>
                </div>
                <div class="nexus-stat-card cyan" id="approval-rate-card">
                    <div class="card-icon"><i class="fa fa-line-chart"></i></div>
                    <div class="card-label">Approval Rate</div>
                    <div class="card-value" id="approval-rate">0%</div>
                    <div class="card-subtitle">Success ratio</div>
                </div>
            </div>

            <!-- Charts Row -->
            <div class="nexus-content-grid">
                <div class="nexus-panel">
                    <div class="nexus-panel-header">
                        <h3>
                            <span class="icon-wrapper"><i class="fa fa-pie-chart"></i></span>
                            Status Distribution
                        </h3>
                    </div>
                    <div class="nexus-panel-body" id="status-chart"></div>
                </div>
                <div class="nexus-panel">
                    <div class="nexus-panel-header">
                        <h3>
                            <span class="icon-wrapper"><i class="fa fa-area-chart"></i></span>
                            Activity Timeline
                        </h3>
                        <span class="badge">Last 30 days</span>
                    </div>
                    <div class="nexus-panel-body" id="timeline-chart"></div>
                </div>
            </div>

            <!-- Two Column Section -->
            <div class="nexus-two-col">
                <div class="nexus-panel">
                    <div class="nexus-panel-header">
                        <h3>
                            <span class="icon-wrapper"><i class="fa fa-warning"></i></span>
                            Overdue Proofs
                        </h3>
                        <span class="badge" id="overdue-badge">0</span>
                    </div>
                    <div class="nexus-panel-body">
                        <div class="nexus-proof-list" id="overdue-proofs"></div>
                    </div>
                </div>
                <div class="nexus-panel">
                    <div class="nexus-panel-header">
                        <h3>
                            <span class="icon-wrapper"><i class="fa fa-history"></i></span>
                            Recent Activity
                        </h3>
                        <a href="/app/ops-ziflow-proof" class="view-all">View All →</a>
                    </div>
                    <div class="nexus-panel-body">
                        <div class="nexus-proof-list" id="recent-proofs"></div>
                    </div>
                </div>
            </div>

            <!-- Orders Table -->
            <div class="nexus-panel">
                <div class="nexus-panel-header">
                    <h3>
                        <span class="icon-wrapper"><i class="fa fa-shopping-cart"></i></span>
                        Orders Awaiting Approval
                    </h3>
                    <span class="badge" id="orders-pending-badge">0</span>
                </div>
                <div class="nexus-panel-body">
                    <div class="nexus-table-container" id="orders-pending"></div>
                </div>
            </div>
        </div>
    `;
}

function setup_card_click_handlers(page) {
    page.main.find('#total-proofs-card').on('click', function() {
        frappe.set_route('List', 'OPS ZiFlow Proof');
    });

    page.main.find('#pending-card').on('click', function() {
        frappe.set_route('List', 'OPS ZiFlow Proof', {'proof_status': ['in', ['Draft', 'In Review', 'Changes Requested']]});
    });

    page.main.find('#approved-card').on('click', function() {
        frappe.set_route('List', 'OPS ZiFlow Proof', {'proof_status': 'Approved'});
    });

    page.main.find('#rejected-card').on('click', function() {
        frappe.set_route('List', 'OPS ZiFlow Proof', {'proof_status': 'Rejected'});
    });

    page.main.find('#overdue-card').on('click', function() {
        frappe.set_route('List', 'OPS ZiFlow Proof', {
            'proof_status': ['in', ['Draft', 'In Review', 'Changes Requested']],
            'deadline': ['<', frappe.datetime.get_today()]
        });
    });
}

function load_dashboard_data(page) {
    frappe.call({
        method: 'ops_ziflow.api.dashboard.get_dashboard_stats',
        callback: function(r) {
            if (r.message) {
                var data = r.message;
                animateValue(page.main.find('#total-proofs-count'), data.total_proofs || 0);
                animateValue(page.main.find('#pending-count'), data.pending_count || 0);
                animateValue(page.main.find('#approved-count'), data.approved_count || 0);
                animateValue(page.main.find('#rejected-count'), data.rejected_count || 0);
                animateValue(page.main.find('#overdue-count'), data.overdue_count || 0);
                page.main.find('#approval-rate').text((data.approval_rate || 0) + '%');
                page.main.find('#overdue-badge').text(data.overdue_count || 0);
                page.main.find('#orders-pending-badge').text(data.orders_pending_proofs || 0);
                render_status_chart(page, data.by_status);
            }
        }
    });

    frappe.call({
        method: 'ops_ziflow.api.dashboard.get_proof_timeline',
        args: {days: 30},
        callback: function(r) {
            if (r.message) {
                render_timeline_chart(page, r.message);
            }
        }
    });

    frappe.call({
        method: 'ops_ziflow.api.dashboard.get_overdue_proofs',
        args: {limit: 10},
        callback: function(r) {
            if (r.message) {
                render_overdue_proofs(page, r.message.proofs);
            }
        }
    });

    frappe.call({
        method: 'ops_ziflow.api.dashboard.get_recent_proofs',
        args: {limit: 10},
        callback: function(r) {
            if (r.message) {
                render_recent_proofs(page, r.message.proofs);
            }
        }
    });

    load_orders_pending(page);
}

function animateValue(element, target) {
    var current = 0;
    var duration = 1200;
    var start = performance.now();

    function update(timestamp) {
        var elapsed = timestamp - start;
        var progress = Math.min(elapsed / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 4);
        current = Math.floor(eased * target);
        element.text(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.text(target);
        }
    }

    requestAnimationFrame(update);
}

function render_status_chart(page, by_status) {
    var container = page.main.find('#status-chart');

    if (!by_status || Object.keys(by_status).length === 0) {
        container.html(`
            <div class="nexus-empty">
                <div class="nexus-empty-icon"><i class="fa fa-pie-chart"></i></div>
                <p>No data available</p>
            </div>
        `);
        return;
    }

    var status_config = {
        'Approved': { color: '#10b981', gradient: 'linear-gradient(90deg, #10b981 0%, #14b8a6 100%)' },
        'In Review': { color: '#f59e0b', gradient: 'linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%)' },
        'Pending': { color: '#eab308', gradient: 'linear-gradient(90deg, #eab308 0%, #fde047 100%)' },
        'Draft': { color: '#6b7294', gradient: 'linear-gradient(90deg, #6b7294 0%, #9ca3c4 100%)' },
        'Rejected': { color: '#f43f5e', gradient: 'linear-gradient(90deg, #f43f5e 0%, #ec4899 100%)' },
        'Changes Requested': { color: '#f97316', gradient: 'linear-gradient(90deg, #f97316 0%, #fb923c 100%)' },
        'Archived': { color: '#9ca3c4', gradient: 'linear-gradient(90deg, #9ca3c4 0%, #d1d5e4 100%)' }
    };

    var total = Object.values(by_status).reduce((a, b) => a + b, 0);
    var html = '';

    for (var status in by_status) {
        var count = by_status[status];
        var percent = Math.round((count / total) * 100);
        var config = status_config[status] || { color: '#6b7294', gradient: 'linear-gradient(90deg, #6b7294 0%, #9ca3c4 100%)' };

        html += `
            <div class="nexus-status-item">
                <div class="nexus-status-header">
                    <span class="nexus-status-label">
                        <span class="dot" style="background: ${config.color};"></span>
                        ${status}
                    </span>
                    <span class="nexus-status-value">${count} (${percent}%)</span>
                </div>
                <div class="nexus-status-bar">
                    <div class="nexus-status-fill" style="width: 0%; background: ${config.gradient};" data-width="${percent}"></div>
                </div>
            </div>
        `;
    }

    container.html(html);

    setTimeout(function() {
        container.find('.nexus-status-fill').each(function() {
            $(this).css('width', $(this).data('width') + '%');
        });
    }, 100);
}

function render_timeline_chart(page, data) {
    var container = page.main.find('#timeline-chart');

    // Generate last 15 days for continuous timeline
    var dates = [];
    for (var i = 14; i >= 0; i--) {
        var d = new Date();
        d.setDate(d.getDate() - i);
        dates.push(d.toISOString().split('T')[0]);
    }

    // Build data maps - handle various date formats from server
    var created_map = {};
    var approved_map = {};

    if (data.created && data.created.length > 0) {
        data.created.forEach(function(d) {
            var dateStr = d.date;
            if (typeof dateStr === 'object' && dateStr !== null) {
                dateStr = new Date(dateStr).toISOString().split('T')[0];
            } else if (typeof dateStr === 'string' && dateStr.includes('T')) {
                dateStr = dateStr.split('T')[0];
            }
            created_map[dateStr] = d.count;
        });
    }

    if (data.approved && data.approved.length > 0) {
        data.approved.forEach(function(d) {
            var dateStr = d.date;
            if (typeof dateStr === 'object' && dateStr !== null) {
                dateStr = new Date(dateStr).toISOString().split('T')[0];
            } else if (typeof dateStr === 'string' && dateStr.includes('T')) {
                dateStr = dateStr.split('T')[0];
            }
            approved_map[dateStr] = d.count;
        });
    }

    // Calculate max value for scaling
    var all_values = [...Object.values(created_map), ...Object.values(approved_map)];
    var max_val = all_values.length > 0 ? Math.max(...all_values, 1) : 5;

    // Check if there's any data
    var hasData = Object.keys(created_map).length > 0 || Object.keys(approved_map).length > 0;

    var html = '<div class="nexus-timeline">';

    dates.forEach(function(date, index) {
        var created = created_map[date] || 0;
        var approved = approved_map[date] || 0;
        var created_height = hasData ? Math.max((created / max_val) * 140, 4) : (Math.random() * 60 + 20);
        var approved_height = hasData ? Math.max((approved / max_val) * 140, 4) : (Math.random() * 40 + 10);
        var dateObj = new Date(date);
        var day = dateObj.getDate();
        var month = dateObj.toLocaleString('default', { month: 'short' });

        html += `
            <div class="nexus-bar-group" style="animation-delay: ${index * 50}ms;">
                <div class="nexus-bars">
                    <div class="nexus-bar created" data-height="${created_height}" data-value="${created}" style="height: 0px;"></div>
                    <div class="nexus-bar approved" data-height="${approved_height}" data-value="${approved}" style="height: 0px;"></div>
                </div>
                <div class="nexus-date">${month} ${day}</div>
            </div>
        `;
    });

    html += '</div>';

    // Add totals summary
    var totalCreated = Object.values(created_map).reduce((a, b) => a + b, 0);
    var totalApproved = Object.values(approved_map).reduce((a, b) => a + b, 0);

    html += `
        <div class="nexus-legend">
            <div class="nexus-legend-item">
                <div class="nexus-legend-dot" style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);"></div>
                <span>Created</span>
                <span class="nexus-legend-value">${totalCreated}</span>
            </div>
            <div class="nexus-legend-item">
                <div class="nexus-legend-dot" style="background: linear-gradient(135deg, #10b981 0%, #14b8a6 100%);"></div>
                <span>Approved</span>
                <span class="nexus-legend-value">${totalApproved}</span>
            </div>
        </div>
    `;

    container.html(html);

    // Animate bars with staggered effect
    setTimeout(function() {
        container.find('.nexus-bar').each(function(index) {
            var bar = $(this);
            var height = bar.data('height');
            setTimeout(function() {
                bar.css({
                    'height': height + 'px',
                    'transition': 'height 0.6s cubic-bezier(0.4, 0, 0.2, 1)'
                });
            }, Math.floor(index / 2) * 40);
        });
    }, 200);

    // Add hover tooltips
    container.find('.nexus-bar').hover(
        function() {
            var bar = $(this);
            var value = bar.data('value');
            var type = bar.hasClass('created') ? 'Created' : 'Approved';
            var tooltip = $('<div class="nexus-tooltip">' + type + ': ' + value + '</div>');
            tooltip.css({
                'position': 'absolute',
                'background': '#1a1f36',
                'color': '#fff',
                'padding': '6px 12px',
                'border-radius': '8px',
                'font-size': '12px',
                'font-weight': '600',
                'top': '-35px',
                'left': '50%',
                'transform': 'translateX(-50%)',
                'white-space': 'nowrap',
                'z-index': '100',
                'box-shadow': '0 4px 12px rgba(0,0,0,0.15)'
            });
            bar.css('position', 'relative').append(tooltip);
        },
        function() {
            $(this).find('.nexus-tooltip').remove();
        }
    );
}

function render_overdue_proofs(page, proofs) {
    var container = page.main.find('#overdue-proofs');

    if (!proofs || proofs.length === 0) {
        container.html(`
            <div class="nexus-empty success">
                <div class="nexus-empty-icon"><i class="fa fa-check-circle"></i></div>
                <p>No overdue proofs!</p>
            </div>
        `);
        return;
    }

    var html = '';
    proofs.forEach(function(proof) {
        var deadline = proof.deadline ? frappe.datetime.prettyDate(proof.deadline) : 'No deadline';
        var statusClass = get_status_class(proof.proof_status);

        html += `
            <div class="nexus-proof-item">
                <div class="nexus-proof-icon">
                    <i class="fa fa-file-image-o"></i>
                </div>
                <div class="nexus-proof-content">
                    <div class="nexus-proof-title">
                        <a href="/app/ops-ziflow-proof/${proof.name}">${proof.proof_name || proof.name}</a>
                    </div>
                    <div class="nexus-proof-meta">
                        ${proof.ops_order ? '<a href="/app/ops-order/' + proof.ops_order + '">' + proof.ops_order + '</a> • ' : ''}
                        <span class="deadline-urgent">Due: ${deadline}</span>
                    </div>
                </div>
                <div class="nexus-proof-actions">
                    <span class="nexus-status-pill ${statusClass}">${proof.proof_status}</span>
                    ${proof.ziflow_url ? '<a href="' + proof.ziflow_url + '" target="_blank" class="nexus-btn-icon" title="Open in ZiFlow"><i class="fa fa-external-link"></i></a>' : ''}
                </div>
            </div>
        `;
    });

    container.html(html);
}

function render_recent_proofs(page, proofs) {
    var container = page.main.find('#recent-proofs');

    if (!proofs || proofs.length === 0) {
        container.html(`
            <div class="nexus-empty">
                <div class="nexus-empty-icon"><i class="fa fa-history"></i></div>
                <p>No recent proofs</p>
            </div>
        `);
        return;
    }

    var html = '';
    proofs.forEach(function(proof) {
        var modified = frappe.datetime.prettyDate(proof.modified);
        var statusClass = get_status_class(proof.proof_status);

        html += `
            <div class="nexus-proof-item">
                <div class="nexus-proof-icon">
                    <i class="fa fa-file-image-o"></i>
                </div>
                <div class="nexus-proof-content">
                    <div class="nexus-proof-title">
                        <a href="/app/ops-ziflow-proof/${proof.name}">${proof.proof_name || proof.name}</a>
                    </div>
                    <div class="nexus-proof-meta">
                        ${proof.ops_order ? '<a href="/app/ops-order/' + proof.ops_order + '">' + proof.ops_order + '</a> • ' : ''}
                        v${proof.current_version || 1} • ${modified}
                    </div>
                </div>
                <div class="nexus-proof-actions">
                    <span class="nexus-status-pill ${statusClass}">${proof.proof_status}</span>
                </div>
            </div>
        `;
    });

    container.html(html);
}

function load_orders_pending(page) {
    var container = page.main.find('#orders-pending');

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'OPS Order',
            filters: {
                'all_proofs_approved': 0,
                'pending_proof_count': ['>', 0]
            },
            fields: ['name', 'ops_order_id', 'customer_name', 'pending_proof_count', 'order_status'],
            order_by: 'pending_proof_count desc',
            limit_page_length: 15
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                var html = `
                    <table class="nexus-table">
                        <thead>
                            <tr>
                                <th>Order ID</th>
                                <th>Customer</th>
                                <th>Status</th>
                                <th>Pending</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                r.message.forEach(function(order) {
                    html += `
                        <tr>
                            <td><a href="/app/ops-order/${order.name}">${order.ops_order_id || order.name}</a></td>
                            <td>${order.customer_name || '-'}</td>
                            <td>${order.order_status || '-'}</td>
                            <td><span class="nexus-badge-count">${order.pending_proof_count}</span></td>
                            <td><a href="/app/ops-ziflow-proof?ops_order=${order.name}" class="nexus-btn-sm">View Proofs</a></td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
                container.html(html);
            } else {
                container.html(`
                    <div class="nexus-empty success">
                        <div class="nexus-empty-icon"><i class="fa fa-trophy"></i></div>
                        <p>All orders have approved proofs!</p>
                    </div>
                `);
            }
        }
    });
}

function get_status_class(status) {
    var classes = {
        'Approved': 'approved',
        'In Review': 'in-review',
        'Pending': 'in-review',
        'Draft': 'draft',
        'Rejected': 'rejected',
        'Changes Requested': 'changes'
    };
    return classes[status] || 'draft';
}
