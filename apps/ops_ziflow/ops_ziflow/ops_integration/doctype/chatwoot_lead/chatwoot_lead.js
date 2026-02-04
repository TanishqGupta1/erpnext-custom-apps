frappe.ui.form.on('Chatwoot Lead', {
	refresh: function(frm) {
		// Add timeline button to toolbar
		if (!frm.is_new()) {
			frm.add_custom_button(__('View Timeline'), function() {
				show_form_timeline(frm);
			}, __('Actions'));

			// Add quick status buttons
			add_status_buttons(frm);

			// Show activity summary in sidebar
			render_activity_sidebar(frm);
		}

		// Show info collection status indicator
		if (frm.doc.info_collection_status && frm.doc.info_collection_status !== 'Complete') {
			frm.dashboard.add_indicator(
				__('Info Collection: {0}', [frm.doc.info_collection_status]),
				frm.doc.info_collection_status === 'In Progress' ? 'orange' : 'blue'
			);

			if (frm.doc.missing_fields) {
				try {
					let missing = JSON.parse(frm.doc.missing_fields);
					if (missing.length > 0) {
						frm.dashboard.add_comment(
							__('Missing fields: {0}', [missing.map(f => frappe.unscrub(f)).join(', ')]),
							'blue',
							true
						);
					}
				} catch(e) {}
			}
		}

		// Add link to Chatwoot conversation
		if (frm.doc.chatwoot_conversation_id) {
			frm.add_custom_button(__('Open in Chatwoot'), function() {
				// Assuming chatwoot is at app.chatwoot.com or configured URL
				let chatwoot_url = frappe.boot.chatwoot_url || 'https://app.chatwoot.com';
				let account_id = frm.doc.chatwoot_account_id || '1';
				let url = chatwoot_url + '/app/accounts/' + account_id + '/conversations/' + frm.doc.chatwoot_conversation_id;
				window.open(url, '_blank');
			}, __('Actions'));
		}

		// Auto-refresh timeline on form load
		if (!frm.is_new() && frm.fields_dict.section_history) {
			setTimeout(() => render_inline_timeline(frm), 500);
		}
	},

	onload: function(frm) {
		// Set default values for new leads
		if (frm.is_new()) {
			frm.set_value('status', 'New');
			frm.set_value('priority', 'Medium');
			frm.set_value('info_collection_status', 'Pending');
		}
	},

	status: function(frm) {
		// Track status changes
		if (frm.doc.status === 'Contacted' && !frm.doc.last_contacted) {
			frm.set_value('last_contacted', frappe.datetime.now_datetime());
			frm.set_value('contact_count', (frm.doc.contact_count || 0) + 1);
		}

		if (frm.doc.status === 'Won' && !frm.doc.converted) {
			frm.set_value('converted', 1);
			frm.set_value('converted_date', frappe.datetime.get_today());
		}
	},

	lead_type: function(frm) {
		// Update info collection when lead type changes
		frm.trigger('validate_info_collection');
	},

	validate_info_collection: function(frm) {
		// Check required fields based on lead type
		const required_fields = {
			'Schedule Call': ['lead_name', 'phone', 'preferred_call_time'],
			'Quote Request': ['lead_name', 'email', 'inquiry_type', 'quantity_needed'],
			'General Inquiry': ['lead_name']
		};

		let lead_type = frm.doc.lead_type || 'General Inquiry';
		let fields = required_fields[lead_type] || required_fields['General Inquiry'];
		let missing = [];

		fields.forEach(function(field) {
			if (!frm.doc[field]) {
				missing.push(field);
			}
		});

		if (missing.length > 0) {
			frm.set_value('info_collection_status', missing.length === fields.length ? 'Pending' : 'In Progress');
		} else {
			frm.set_value('info_collection_status', 'Complete');
		}
	}
});

function add_status_buttons(frm) {
	// Quick status change buttons based on current status
	const next_statuses = {
		'New': ['Contacted', 'Qualified'],
		'Contacted': ['Qualified', 'Proposal Sent', 'Unqualified'],
		'Qualified': ['Proposal Sent', 'Won', 'Lost'],
		'Proposal Sent': ['Negotiation', 'Won', 'Lost'],
		'Negotiation': ['Won', 'Lost']
	};

	let current = frm.doc.status;
	let options = next_statuses[current];

	if (options) {
		options.forEach(function(status) {
			let color = status === 'Won' ? 'btn-success' : (status === 'Lost' || status === 'Unqualified') ? 'btn-danger' : 'btn-secondary';
			frm.add_custom_button(__(status), function() {
				frm.set_value('status', status);
				frm.save();
			}, __('Change Status'));
		});
	}
}

function render_activity_sidebar(frm) {
	// Add activity summary to the sidebar
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Version',
			filters: {
				ref_doctype: 'Chatwoot Lead',
				docname: frm.doc.name
			},
			fields: ['creation', 'owner'],
			order_by: 'creation desc',
			limit_page_length: 5
		},
		async: true,
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				let html = '<div class="sidebar-section">';
				html += '<h6 class="text-muted">' + __('Recent Activity') + '</h6>';
				html += '<ul class="list-unstyled small">';

				r.message.forEach(function(v) {
					html += '<li class="mb-2">';
					html += '<span class="text-muted">' + frappe.datetime.prettyDate(v.creation) + '</span>';
					html += '<br><span class="text-dark">' + v.owner.split('@')[0] + '</span>';
					html += '</li>';
				});

				html += '</ul>';
				html += '<a href="#" onclick="show_form_timeline(cur_frm); return false;" class="small">' + __('View Full Timeline') + '</a>';
				html += '</div>';

				// Add to form sidebar
				if (frm.sidebar) {
					$(frm.sidebar.sidebar).find('.sidebar-activity').remove();
					$(frm.sidebar.sidebar).append('<div class="sidebar-activity">' + html + '</div>');
				}
			}
		}
	});
}

function render_inline_timeline(frm) {
	// Render timeline in the History section
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Version',
			filters: {
				ref_doctype: 'Chatwoot Lead',
				docname: frm.doc.name
			},
			fields: ['name', 'owner', 'creation', 'data'],
			order_by: 'creation desc',
			limit_page_length: 10
		},
		callback: function(r) {
			if (r.message) {
				let html = build_inline_timeline(r.message);

				// Find or create timeline container
				let $section = $(frm.fields_dict.section_history.wrapper);
				$section.find('.inline-timeline').remove();
				$section.append('<div class="inline-timeline mt-3">' + html + '</div>');
			}
		}
	});
}

function build_inline_timeline(versions) {
	if (!versions || versions.length === 0) {
		return '<p class="text-muted">' + __('No activity recorded') + '</p>';
	}

	let html = '<div class="timeline-compact">';
	html += '<table class="table table-sm table-borderless">';
	html += '<thead><tr><th>' + __('When') + '</th><th>' + __('Who') + '</th><th>' + __('Changes') + '</th></tr></thead>';
	html += '<tbody>';

	versions.forEach(function(version) {
		let data = {};
		try {
			data = JSON.parse(version.data);
		} catch(e) {
			data = {};
		}

		let changes = [];

		if (data.changed && data.changed.length > 0) {
			data.changed.forEach(function(change) {
				let field_label = frappe.meta.get_label('Chatwoot Lead', change[0]) || change[0];
				changes.push(field_label + ': ' + (change[1] || '-') + ' → ' + (change[2] || '-'));
			});
		}

		if (data.added && data.added.length > 0) {
			changes.push('Created');
		}

		if (changes.length === 0) {
			changes.push('Saved');
		}

		html += '<tr>';
		html += '<td class="text-muted small">' + frappe.datetime.prettyDate(version.creation) + '</td>';
		html += '<td class="small">' + version.owner.split('@')[0] + '</td>';
		html += '<td class="small">' + changes.slice(0, 3).join(', ') + (changes.length > 3 ? ' +' + (changes.length - 3) + ' more' : '') + '</td>';
		html += '</tr>';
	});

	html += '</tbody></table></div>';

	return html;
}

function show_form_timeline(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Version',
			filters: {
				ref_doctype: 'Chatwoot Lead',
				docname: frm.doc.name
			},
			fields: ['name', 'owner', 'creation', 'data'],
			order_by: 'creation desc',
			limit_page_length: 50
		},
		callback: function(r) {
			if (r.message) {
				let html = build_full_timeline(r.message);

				let d = new frappe.ui.Dialog({
					title: __('Activity Timeline: {0}', [frm.doc.lead_name || frm.doc.name]),
					size: 'large',
					fields: [
						{
							fieldtype: 'HTML',
							fieldname: 'timeline_content'
						}
					]
				});

				d.fields_dict.timeline_content.$wrapper.html(html);
				d.show();
			}
		}
	});
}

function build_full_timeline(versions) {
	if (!versions || versions.length === 0) {
		return '<div class="text-muted text-center p-4">' + __('No activity recorded yet') + '</div>';
	}

	let html = '<div class="timeline-full" style="max-height: 500px; overflow-y: auto; padding: 16px;">';

	versions.forEach(function(version, index) {
		let data = {};
		try {
			data = JSON.parse(version.data);
		} catch(e) {
			data = {};
		}

		let changes = [];
		let badge_class = 'badge-secondary';
		let action_type = 'Updated';

		if (data.changed && data.changed.length > 0) {
			data.changed.forEach(function(change) {
				let field_label = frappe.meta.get_label('Chatwoot Lead', change[0]) || frappe.unscrub(change[0]);
				let old_val = change[1] || '<em class="text-muted">empty</em>';
				let new_val = change[2] || '<em class="text-muted">empty</em>';

				if (change[0] === 'status') {
					badge_class = 'badge-' + get_status_badge_class(change[2]);
					action_type = 'Status Changed';
				}

				changes.push({
					field: field_label,
					old: String(old_val).substring(0, 100),
					new: String(new_val).substring(0, 100)
				});
			});
		}

		if (data.added && data.added.length > 0) {
			action_type = 'Created';
			badge_class = 'badge-success';
			changes.push({ field: 'Lead', old: '', new: 'Created' });
		}

		if (changes.length === 0) {
			changes.push({ field: 'Document', old: '', new: 'Saved' });
		}

		html += '<div class="timeline-entry mb-3 p-3" style="background: var(--card-bg); border-radius: 8px; border-left: 4px solid var(--primary);">';
		html += '<div class="d-flex justify-content-between align-items-center mb-2">';
		html += '<div>';
		html += '<span class="badge ' + badge_class + '">' + action_type + '</span> ';
		html += '<strong>' + version.owner + '</strong>';
		html += '</div>';
		html += '<small class="text-muted">' + frappe.datetime.str_to_user(version.creation) + ' (' + frappe.datetime.prettyDate(version.creation) + ')</small>';
		html += '</div>';

		html += '<div class="changes-list small">';
		changes.forEach(function(c) {
			if (c.old) {
				html += '<div class="change-item py-1">';
				html += '<strong>' + c.field + ':</strong> ';
				html += '<span class="text-danger text-decoration-line-through">' + c.old + '</span>';
				html += ' → ';
				html += '<span class="text-success">' + c.new + '</span>';
				html += '</div>';
			} else {
				html += '<div class="change-item py-1">';
				html += '<strong>' + c.field + ':</strong> ' + c.new;
				html += '</div>';
			}
		});
		html += '</div>';

		html += '</div>';
	});

	html += '</div>';

	return html;
}

function get_status_badge_class(status) {
	const classes = {
		'New': 'primary',
		'Contacted': 'info',
		'Qualified': 'info',
		'Proposal Sent': 'warning',
		'Negotiation': 'warning',
		'Won': 'success',
		'Lost': 'danger',
		'Unqualified': 'secondary'
	};
	return classes[status] || 'secondary';
}
