frappe.pages['ziflow-backfill'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'ZiFlow Proof Backfill',
        single_column: true
    });

    page.set_primary_action(__('Start Backfill'), function() {
        page.start_backfill();
    }, 'octicon octicon-sync');

    page.set_secondary_action(__('Refresh Stats'), function() {
        page.refresh_stats();
    });

    page.make_form = function() {
        page.form = new frappe.ui.FieldGroup({
            parent: page.body,
            fields: [
                {
                    fieldname: 'folder_id',
                    fieldtype: 'Data',
                    label: __('ZiFlow Folder ID (optional)'),
                    description: __('Leave empty to import all proofs')
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'include_comments',
                    fieldtype: 'Check',
                    label: __('Include Comments'),
                    description: __('Fetch comments for each proof (slower)')
                },
                {
                    fieldtype: 'Section Break',
                    label: __('Pagination Options')
                },
                {
                    fieldname: 'page_size',
                    fieldtype: 'Int',
                    label: __('Page Size'),
                    default: 50,
                    description: __('Number of proofs to fetch per page')
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'max_pages',
                    fieldtype: 'Int',
                    label: __('Max Pages'),
                    default: 20,
                    description: __('Maximum number of pages to fetch')
                },
                {
                    fieldtype: 'Section Break',
                    label: __('Current Statistics')
                },
                {
                    fieldname: 'stats_html',
                    fieldtype: 'HTML'
                }
            ]
        });
        page.form.make();
    };

    page.refresh_stats = function() {
        frappe.call({
            method: 'ops_ziflow.api.dashboard.get_dashboard_stats',
            callback: function(r) {
                if (r.message) {
                    var stats = r.message;
                    var html = `
                        <div class="row">
                            <div class="col-md-3">
                                <div class="stat-card" style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                                    <h3 style="color: #449CF0; margin: 0;">${stats.total_proofs}</h3>
                                    <p style="margin: 5px 0 0 0; color: #6c757d;">Total Proofs</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card" style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                                    <h3 style="color: #ECAD4B; margin: 0;">${stats.pending_count}</h3>
                                    <p style="margin: 5px 0 0 0; color: #6c757d;">Pending Review</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card" style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                                    <h3 style="color: #48BB74; margin: 0;">${stats.approved_count}</h3>
                                    <p style="margin: 5px 0 0 0; color: #6c757d;">Approved</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card" style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                                    <h3 style="color: #E53E3E; margin: 0;">${stats.overdue_count}</h3>
                                    <p style="margin: 5px 0 0 0; color: #6c757d;">Overdue</p>
                                </div>
                            </div>
                        </div>
                        <div class="row" style="margin-top: 15px;">
                            <div class="col-md-6">
                                <p><strong>Orders Pending Proofs:</strong> ${stats.orders_pending_proofs}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Approval Rate:</strong> ${stats.approval_rate}%</p>
                            </div>
                        </div>
                    `;
                    page.form.get_field('stats_html').html(html);
                }
            }
        });
    };

    page.start_backfill = function() {
        var values = page.form.get_values();

        frappe.confirm(
            __('This will import proofs from ZiFlow. Continue?'),
            function() {
                frappe.call({
                    method: 'ops_ziflow.api.backfill_ziflow_proofs',
                    args: {
                        folder_id: values.folder_id || null,
                        include_comments: values.include_comments ? 1 : 0,
                        page_size: values.page_size || 50,
                        max_pages: values.max_pages || 20
                    },
                    freeze: true,
                    freeze_message: __('Importing proofs from ZiFlow...'),
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __('Backfill Complete'),
                                message: __('Created: {0}, Updated: {1}, Skipped: {2}', [
                                    r.message.created || 0,
                                    r.message.updated || 0,
                                    r.message.skipped || 0
                                ]),
                                indicator: 'green'
                            });
                            page.refresh_stats();
                        }
                    }
                });
            }
        );
    };

    page.make_form();
    page.refresh_stats();
};
