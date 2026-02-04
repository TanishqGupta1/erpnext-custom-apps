frappe.pages['ops-error-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'OPS Error Dashboard',
        single_column: true
    });

    page.main.html(`
        <div class="ops-error-dashboard" style="padding: 15px;">
            <div class="row">
                <div class="col-md-3">
                    <div class="stat-card" id="open-errors-card" style="background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 15px; border-left: 4px solid #e74c3c; cursor: pointer;">
                        <div style="font-size: 12px; color: #888; text-transform: uppercase;">Open Errors</div>
                        <div id="open-errors-count" style="font-size: 32px; font-weight: bold; color: #e74c3c;">-</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card" id="in-progress-card" style="background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 15px; border-left: 4px solid #e67e22; cursor: pointer;">
                        <div style="font-size: 12px; color: #888; text-transform: uppercase;">In Progress</div>
                        <div id="in-progress-count" style="font-size: 32px; font-weight: bold; color: #e67e22;">-</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card" id="critical-card" style="background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 15px; border-left: 4px solid #c0392b; cursor: pointer;">
                        <div style="font-size: 12px; color: #888; text-transform: uppercase;">Critical</div>
                        <div id="critical-count" style="font-size: 32px; font-weight: bold; color: #c0392b;">-</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card" id="resolved-today-card" style="background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 15px; border-left: 4px solid #27ae60; cursor: pointer;">
                        <div style="font-size: 12px; color: #888; text-transform: uppercase;">Resolved Today</div>
                        <div id="resolved-today-count" style="font-size: 32px; font-weight: bold; color: #27ae60;">-</div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div style="background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                        <h5 style="margin-bottom: 15px;">Errors by Type</h5>
                        <div id="errors-by-type"></div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div style="background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                        <h5 style="margin-bottom: 15px;">Errors by Severity</h5>
                        <div id="errors-by-severity"></div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-12">
                    <div style="background: #fff; border-radius: 8px; padding: 20px;">
                        <h5 style="margin-bottom: 15px;">Recent Critical/High Errors</h5>
                        <div id="recent-errors"></div>
                    </div>
                </div>
            </div>
        </div>
    `);

    // Add click handlers for stat cards
    page.main.find('#open-errors-card').on('click', function() {
        frappe.set_route('List', 'OPS Error Log', {'status': 'Open'});
    });

    page.main.find('#in-progress-card').on('click', function() {
        frappe.set_route('List', 'OPS Error Log', {'status': 'In Progress'});
    });

    page.main.find('#critical-card').on('click', function() {
        frappe.set_route('List', 'OPS Error Log', {'severity': 'Critical', 'status': 'Open'});
    });

    page.main.find('#resolved-today-card').on('click', function() {
        frappe.set_route('List', 'OPS Error Log', {'status': ['in', ['Resolved', 'Auto-Resolved']]});
    });

    // Add page buttons
    page.set_primary_action(__('View All Errors'), function() {
        frappe.set_route('List', 'OPS Error Log');
    });

    page.add_inner_button(__('Refresh'), function() {
        load_dashboard_data(page);
    });

    load_dashboard_data(page);
};

function load_dashboard_data(page) {
    frappe.call({
        method: 'ops_ziflow.ops_integration.doctype.ops_error_log.ops_error_log.get_error_summary',
        callback: function(r) {
            if (r.message) {
                var data = r.message;

                // Update stat cards
                page.main.find('#open-errors-count').text(data.total_open || 0);
                page.main.find('#in-progress-count').text(data.total_in_progress || 0);
                page.main.find('#critical-count').text(data.by_severity.Critical || 0);

                // Errors by type
                var type_html = '';
                if (Object.keys(data.by_type).length > 0) {
                    for (var type in data.by_type) {
                        type_html += '<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">' +
                            '<span>' + type + '</span>' +
                            '<span class="badge" style="background: #3498db; color: #fff;">' + data.by_type[type] + '</span>' +
                            '</div>';
                    }
                } else {
                    type_html = '<div style="color: #888; text-align: center; padding: 20px;">No open errors</div>';
                }
                page.main.find('#errors-by-type').html(type_html);

                // Errors by severity
                var severity_html = '';
                var severity_colors = {
                    'Critical': '#e74c3c',
                    'High': '#e67e22',
                    'Medium': '#f1c40f',
                    'Low': '#3498db',
                    'Info': '#95a5a6'
                };
                if (Object.keys(data.by_severity).length > 0) {
                    for (var severity in data.by_severity) {
                        severity_html += '<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">' +
                            '<span><span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ' + (severity_colors[severity] || '#999') + '; margin-right: 8px;"></span>' + severity + '</span>' +
                            '<span class="badge" style="background: ' + (severity_colors[severity] || '#999') + '; color: #fff;">' + data.by_severity[severity] + '</span>' +
                            '</div>';
                    }
                } else {
                    severity_html = '<div style="color: #888; text-align: center; padding: 20px;">No open errors</div>';
                }
                page.main.find('#errors-by-severity').html(severity_html);

                // Recent critical errors
                var recent_html = '';
                if (data.recent_critical && data.recent_critical.length > 0) {
                    recent_html = '<table class="table table-bordered" style="margin-bottom: 0;">' +
                        '<thead><tr><th>Error</th><th>Type</th><th>Severity</th><th>Source</th><th>Occurred</th><th>Action</th></tr></thead>' +
                        '<tbody>';
                    data.recent_critical.forEach(function(err) {
                        var severity_badge = '<span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: ' +
                            (severity_colors[err.severity] || '#999') + '; color: #fff;">' + err.severity + '</span>';
                        var source = err.source_doctype ? (err.source_doctype + (err.source_document ? ': ' + err.source_document : '')) : '-';
                        var occurred = frappe.datetime.prettyDate(err.occurred_at);

                        recent_html += '<tr>' +
                            '<td><a href="/app/ops-error-log/' + err.name + '">' + (err.error_title || err.name) + '</a></td>' +
                            '<td>' + (err.error_type || '-') + '</td>' +
                            '<td>' + severity_badge + '</td>' +
                            '<td>' + source + '</td>' +
                            '<td>' + occurred + '</td>' +
                            '<td><button class="btn btn-xs btn-primary resolve-btn" data-name="' + err.name + '">Resolve</button></td>' +
                            '</tr>';
                    });
                    recent_html += '</tbody></table>';
                } else {
                    recent_html = '<div style="color: #888; text-align: center; padding: 40px;">No critical or high severity errors</div>';
                }
                page.main.find('#recent-errors').html(recent_html);

                // Add resolve button handlers
                page.main.find('.resolve-btn').on('click', function(e) {
                    e.preventDefault();
                    var error_name = $(this).data('name');
                    frappe.prompt([
                        {fieldname: 'resolution_action', label: 'Resolution Action', fieldtype: 'Select', options: '\nManual Fix\nData Corrected\nConfiguration Fixed', reqd: 1},
                        {fieldname: 'resolution_notes', label: 'Resolution Notes', fieldtype: 'Small Text'}
                    ], function(values) {
                        frappe.call({
                            method: 'ops_ziflow.ops_integration.doctype.ops_error_log.ops_error_log.resolve_error',
                            args: {
                                error_name: error_name,
                                resolution_notes: values.resolution_notes,
                                resolution_action: values.resolution_action
                            },
                            callback: function(r) {
                                if (r.message && r.message.status === 'success') {
                                    frappe.show_alert({message: __("Error resolved"), indicator: 'green'});
                                    load_dashboard_data(page);
                                }
                            }
                        });
                    }, __("Resolve Error"), __("Resolve"));
                });
            }
        }
    });

    // Get resolved today count
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'OPS Error Log',
            filters: {
                'status': ['in', ['Resolved', 'Auto-Resolved']],
                'resolved_at': ['>=', frappe.datetime.get_today()]
            }
        },
        callback: function(r) {
            page.main.find('#resolved-today-count').text(r.message || 0);
        }
    });
}
