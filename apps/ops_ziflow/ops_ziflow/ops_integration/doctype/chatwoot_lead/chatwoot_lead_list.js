frappe.listview_settings['Chatwoot Lead'] = {
	add_fields: ['status', 'priority', 'lead_type', 'modified', 'modified_by', 'info_collection_status', 'lead_name'],

	filters: [['status', '!=', 'Lost']],

	get_indicator: function(doc) {
		const status_colors = {
			'New': 'blue',
			'Contacted': 'orange',
			'Qualified': 'purple',
			'Proposal Sent': 'yellow',
			'Negotiation': 'cyan',
			'Won': 'green',
			'Lost': 'red',
			'Unqualified': 'gray'
		};
		return [__(doc.status), status_colors[doc.status] || 'gray', 'status,=,' + doc.status];
	},

	formatters: {
		lead_name: function(value, field, doc) {
			// Show lead name with priority indicator
			let priority_icon = '';
			if (doc.priority === 'Urgent') {
				priority_icon = '<span class="indicator-pill red" title="Urgent"></span> ';
			} else if (doc.priority === 'High') {
				priority_icon = '<span class="indicator-pill orange" title="High Priority"></span> ';
			}
			return priority_icon + value;
		},
		modified: function(value, field, doc) {
			// Show relative time
			return frappe.datetime.prettyDate(value);
		}
	},

	onload: function(listview) {
		// Add timeline sidebar button
		listview.page.add_inner_button(__('Activity Timeline'), function() {
			show_activity_timeline(listview);
		}, __('View'));

		// Add quick filters
		listview.page.add_inner_button(__('Today\'s Leads'), function() {
			listview.filter_area.clear();
			listview.filter_area.add([
				['Chatwoot Lead', 'creation', '>=', frappe.datetime.get_today()]
			]);
			listview.refresh();
		}, __('Quick Filters'));

		listview.page.add_inner_button(__('Needs Follow-up'), function() {
			listview.filter_area.clear();
			listview.filter_area.add([
				['Chatwoot Lead', 'status', 'in', ['New', 'Contacted']],
				['Chatwoot Lead', 'info_collection_status', '!=', 'Complete']
			]);
			listview.refresh();
		}, __('Quick Filters'));

		listview.page.add_inner_button(__('Hot Leads'), function() {
			listview.filter_area.clear();
			listview.filter_area.add([
				['Chatwoot Lead', 'priority', 'in', ['High', 'Urgent']],
				['Chatwoot Lead', 'status', 'not in', ['Won', 'Lost', 'Unqualified']]
			]);
			listview.refresh();
		}, __('Quick Filters'));
	},

	button: {
		show: function(doc) {
			return doc.status !== 'Won' && doc.status !== 'Lost';
		},
		get_label: function() {
			return __('View Timeline');
		},
		get_description: function(doc) {
			return __('View activity timeline for {0}', [doc.lead_name]);
		},
		action: function(doc) {
			show_lead_timeline(doc.name);
		}
	},

	primary_action: function() {
		// Quick create from chat
		frappe.new_doc('Chatwoot Lead');
	}
};

function show_activity_timeline(listview) {
	// Get recent activity across all visible leads
	const selected = listview.get_checked_items();
	const filters = selected.length > 0
		? { name: ['in', selected.map(d => d.name)] }
		: {};

	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Version',
			filters: {
				ref_doctype: 'Chatwoot Lead'
			},
			fields: ['name', 'owner', 'creation', 'data', 'docname'],
			order_by: 'creation desc',
			limit_page_length: 50
		},
		callback: function(r) {
			if (r.message) {
				show_timeline_dialog(r.message);
			}
		}
	});
}

function show_timeline_dialog(versions) {
	let timeline_html = build_timeline_html(versions);

	let d = new frappe.ui.Dialog({
		title: __('Activity Timeline'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'timeline_content'
			}
		]
	});

	d.fields_dict.timeline_content.$wrapper.html(timeline_html);
	d.show();
}

function show_lead_timeline(lead_name) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Version',
			filters: {
				ref_doctype: 'Chatwoot Lead',
				docname: lead_name
			},
			fields: ['name', 'owner', 'creation', 'data'],
			order_by: 'creation desc',
			limit_page_length: 20
		},
		callback: function(r) {
			if (r.message) {
				let timeline_html = build_timeline_html(r.message, lead_name);

				let d = new frappe.ui.Dialog({
					title: __('Timeline: {0}', [lead_name]),
					size: 'large',
					fields: [
						{
							fieldtype: 'HTML',
							fieldname: 'timeline_content'
						}
					]
				});

				d.fields_dict.timeline_content.$wrapper.html(timeline_html);
				d.show();
			}
		}
	});
}

function build_timeline_html(versions, lead_name = null) {
	if (!versions || versions.length === 0) {
		return '<div class="text-muted text-center p-4">' + __('No activity recorded yet') + '</div>';
	}

	let html = '<div class="timeline-wrapper" style="max-height: 500px; overflow-y: auto;">';
	html += '<ul class="timeline" style="list-style: none; padding-left: 0;">';

	versions.forEach(function(version, index) {
		let data = {};
		try {
			data = JSON.parse(version.data);
		} catch(e) {
			data = {};
		}

		let changes = [];
		let icon = 'fa-edit';
		let color = 'blue';

		// Parse changed fields
		if (data.changed && data.changed.length > 0) {
			data.changed.forEach(function(change) {
				let field_label = frappe.meta.get_label('Chatwoot Lead', change[0]) || change[0];
				let old_val = change[1] || '(empty)';
				let new_val = change[2] || '(empty)';

				// Detect status changes for special styling
				if (change[0] === 'status') {
					icon = 'fa-flag';
					color = get_status_color(new_val);
					changes.push('<strong>' + field_label + '</strong>: ' + old_val + ' → <span class="text-' + color + '">' + new_val + '</span>');
				} else if (change[0] === 'info_collection_status') {
					icon = 'fa-tasks';
					color = new_val === 'Complete' ? 'green' : 'orange';
					changes.push('<strong>' + field_label + '</strong>: ' + old_val + ' → ' + new_val);
				} else {
					changes.push('<strong>' + field_label + '</strong>: ' + truncate(old_val, 30) + ' → ' + truncate(new_val, 30));
				}
			});
		}

		// If document was created
		if (data.added && data.added.length > 0) {
			icon = 'fa-plus-circle';
			color = 'green';
			changes.push('<em>Lead created</em>');
		}

		if (changes.length === 0) {
			changes.push('<em>Document saved</em>');
		}

		let doc_link = lead_name ? '' : '<a href="/app/chatwoot-lead/' + version.docname + '" class="text-muted small">' + version.docname + '</a><br>';

		html += '<li class="timeline-item" style="position: relative; padding-left: 30px; padding-bottom: 20px; border-left: 2px solid #e0e0e0; margin-left: 10px;">';
		html += '<div class="timeline-icon" style="position: absolute; left: -12px; top: 0; width: 22px; height: 22px; border-radius: 50%; background: var(--bg-color); border: 2px solid var(--' + color + '-500, #5e64ff); display: flex; align-items: center; justify-content: center;">';
		html += '<i class="fa ' + icon + '" style="font-size: 10px; color: var(--' + color + '-500, #5e64ff);"></i>';
		html += '</div>';
		html += '<div class="timeline-content" style="background: var(--card-bg); border-radius: 8px; padding: 12px; box-shadow: var(--card-shadow);">';
		html += '<div class="timeline-header" style="display: flex; justify-content: space-between; margin-bottom: 8px;">';
		html += '<span class="text-muted small">' + frappe.datetime.prettyDate(version.creation) + '</span>';
		html += '<span class="text-muted small"><i class="fa fa-user"></i> ' + version.owner + '</span>';
		html += '</div>';
		html += doc_link;
		html += '<div class="timeline-changes">' + changes.join('<br>') + '</div>';
		html += '</div>';
		html += '</li>';
	});

	html += '</ul></div>';

	return html;
}

function get_status_color(status) {
	const colors = {
		'New': 'blue',
		'Contacted': 'orange',
		'Qualified': 'purple',
		'Proposal Sent': 'yellow',
		'Negotiation': 'cyan',
		'Won': 'green',
		'Lost': 'red',
		'Unqualified': 'gray'
	};
	return colors[status] || 'gray';
}

function truncate(str, length) {
	if (!str) return '';
	str = String(str);
	if (str.length <= length) return str;
	return str.substring(0, length) + '...';
}
