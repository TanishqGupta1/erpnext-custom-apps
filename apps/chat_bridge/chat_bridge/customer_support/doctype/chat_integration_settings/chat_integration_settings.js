// Chat Integration Settings Form Script
frappe.ui.form.on('Chat Integration Settings', {
	refresh: function(frm) {
		// Add custom buttons
		frm.add_custom_button(__('Sync Now'), function() {
			frappe.call({
				method: 'chat_bridge.api.rest_api.sync_conversations',
				args: {
					background: 0
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __('Sync started successfully'),
							indicator: 'green'
						});
					} else {
						frappe.show_alert({
							message: __('Sync failed: ') + (r.message ? r.message.error : 'Unknown error'),
							indicator: 'red'
						});
					}
				}
			});
		}, __('Actions'));

		// Load embedded lists
		load_user_tokens(frm);
		load_contact_mappings(frm);
		load_conversation_mappings(frm);
	}
});

function load_user_tokens(frm) {
	frappe.call({
		method: 'chat_bridge.api.rest_api.get_all_users_with_token_status',
		callback: function(r) {
			if (r.message && r.message.success) {
				render_user_tokens_table(r.message.users, frm);
			}
		}
	});
}

function render_user_tokens_table(users, frm) {
	let html = `
		<div class="frappe-control">
			<div class="form-group">
				<div class="clearfix">
					<label class="control-label" style="padding-right: 0px;">
						<span style="margin-right: 10px;">All ERP Users with Chat Access Status</span>
					</label>
				</div>
				<div class="control-input-wrapper">
					<div class="control-value like-disabled-input" style="padding: 0;">
	`;

	if (users && users.length > 0) {
		html += `
						<table class="table table-bordered table-condensed" style="margin: 0;">
							<thead>
								<tr style="background-color: #f5f7fa;">
									<th style="color: #6c757d; font-weight: 600;">User</th>
									<th style="color: #6c757d; font-weight: 600;">Full Name</th>
									<th style="color: #6c757d; font-weight: 600;">Email</th>
									<th style="color: #6c757d; font-weight: 600;">Has Chat Access</th>
									<th style="color: #6c757d; font-weight: 600;">Chat User ID</th>
									<th style="color: #6c757d; font-weight: 600;">Last Modified</th>
									<th style="color: #6c757d; font-weight: 600;">Actions</th>
								</tr>
							</thead>
							<tbody>
		`;

		users.forEach(user => {
			html += '<tr>';
			html += `<td><a href="/app/user/${encodeURIComponent(user.name)}" target="_blank">${user.name}</a></td>`;
			html += `<td>${user.full_name || '-'}</td>`;
			html += `<td>${user.email || '-'}</td>`;

			if (user.has_token) {
				html += `<td><span class="indicator-pill green">Yes</span></td>`;
				html += `<td>${user.chat_user_id || '-'}</td>`;
				html += `<td>${user.modified ? moment(user.modified).format('YYYY-MM-DD HH:mm:ss') : '-'}</td>`;
				html += `<td>
					<a href="/app/chat-user-token/${user.token_name}" target="_blank" class="btn btn-xs btn-default">
						Edit Token
					</a>
				</td>`;
			} else {
				html += `<td><span class="indicator-pill red">No</span></td>`;
				html += `<td>-</td>`;
				html += `<td>-</td>`;
				html += `<td>
					<button class="btn btn-xs btn-primary" onclick="grant_chat_access('${user.name}', '${user.full_name}')">
						Grant Access
					</button>
				</td>`;
			}
			html += '</tr>';
		});

		html += '</tbody></table>';
	} else {
		html += `<div class="text-muted" style="padding: 15px;">No users found</div>`;
	}

	html += `
					</div>
				</div>
			</div>
		</div>
	`;

	$('#user-tokens-list').html(html);
}

window.grant_chat_access = function(user, full_name) {
	// Ask if user already exists in Chatwoot
	let d = new frappe.ui.Dialog({
		title: __('Grant Chat Access'),
		fields: [
			{
				fieldtype: 'HTML',
				options: `<p><strong>User:</strong> ${full_name}</p>`
			},
			{
				fieldtype: 'Section Break'
			},
			{
				fieldname: 'account_exists',
				fieldtype: 'Select',
				label: __('Does this user already have a Chatwoot account?'),
				options: ['No - Create new account', 'Yes - Link existing account'],
				default: 'No - Create new account',
				reqd: 1,
				change: function() {
					let exists = d.get_value('account_exists') === 'Yes - Link existing account';
					d.set_df_property('chatwoot_user_id', 'hidden', !exists);
					d.set_df_property('api_access_token', 'hidden', !exists);
					d.set_df_property('info_html', 'hidden', exists);
				}
			},
			{
				fieldtype: 'Section Break'
			},
			{
				fieldname: 'chatwoot_user_id',
				fieldtype: 'Int',
				label: __('Chatwoot User ID'),
				description: __('The numeric ID from Chatwoot (e.g., 3)'),
				hidden: 1,
				mandatory_depends_on: 'eval:doc.account_exists=="Yes - Link existing account"'
			},
			{
				fieldname: 'api_access_token',
				fieldtype: 'Password',
				label: __('User\'s API Access Token'),
				description: __('REQUIRED: Get from Chatwoot → Profile Settings → Access Token'),
				hidden: 1,
				mandatory_depends_on: 'eval:doc.account_exists=="Yes - Link existing account"'
			},
			{
				fieldname: 'info_html',
				fieldtype: 'HTML',
				options: `
					<div style="padding: 10px; background: #f8f9fa; border-radius: 4px; margin-top: 10px;">
						<p style="margin: 0;"><strong>This will:</strong></p>
						<ul style="margin: 5px 0;">
							<li>Create a Chatwoot agent account</li>
							<li>Generate an API access token</li>
							<li>Store it in the user profile</li>
						</ul>
					</div>
				`
			}
		],
		primary_action_label: __('Grant Access'),
		primary_action: function(values) {
			d.hide();

			let args = { user: user };
			let create_new = values.account_exists === 'No - Create new account';

			if (!create_new) {
				// Validate inputs for existing account
				if (!values.chatwoot_user_id) {
					frappe.throw(__('Please provide Chatwoot User ID'));
					return;
				}
				if (!values.api_access_token) {
					frappe.throw(__('Please provide the user\'s API Access Token from Chatwoot'));
					return;
				}
				args.chatwoot_user_id = values.chatwoot_user_id;
				args.api_access_token = values.api_access_token;
			}

			frappe.show_alert({
				message: __(create_new ? 'Creating Chatwoot account...' : 'Linking existing account...'),
				indicator: 'blue'
			});

			frappe.call({
				method: 'chat_bridge.api.rest_api.create_chatwoot_user',
				args: args,
				callback: function(resp) {
					if (resp.message && resp.message.success) {
						frappe.show_alert({
							message: __('Chat access granted successfully'),
							indicator: 'green'
						});
						load_user_tokens(cur_frm);
					} else {
						frappe.show_alert({
							message: __('Failed to grant access: ') + (resp.message ? resp.message.error : 'Unknown error'),
							indicator: 'red'
						});
					}
				}
			});
		}
	});

	d.show();
};

function load_contact_mappings(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Chat Contact Mapping',
			fields: ['name', 'erpnext_contact', 'chat_contact_id', 'chat_account_id', 'sync_direction', 'last_synced'],
			order_by: 'modified desc',
			limit_page_length: 100
		},
		callback: function(r) {
			if (r.message) {
				render_list('#contact-mappings-list', r.message, 'Chat Contact Mapping', [
					{label: 'ERPNext Contact', field: 'erpnext_contact', type: 'Link'},
					{label: 'Chat Contact ID', field: 'chat_contact_id', type: 'Data'},
					{label: 'Sync Direction', field: 'sync_direction', type: 'Data'},
					{label: 'Last Synced', field: 'last_synced', type: 'Datetime'}
				]);
			}
		}
	});
}

function load_conversation_mappings(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Chat Conversation Mapping',
			fields: ['name', 'chat_conversation_id', 'erpnext_contact', 'erpnext_lead', 'erpnext_communication', 'status', 'last_message_at'],
			order_by: 'modified desc',
			limit_page_length: 100
		},
		callback: function(r) {
			if (r.message) {
				render_list('#conversation-mappings-list', r.message, 'Chat Conversation Mapping', [
					{label: 'Chat Conversation ID', field: 'chat_conversation_id', type: 'Data'},
					{label: 'Contact', field: 'erpnext_contact', type: 'Link'},
					{label: 'Lead', field: 'erpnext_lead', type: 'Link'},
					{label: 'Status', field: 'status', type: 'Data'},
					{label: 'Last Message', field: 'last_message_at', type: 'Datetime'}
				]);
			}
		}
	});
}

function render_list(selector, data, doctype, columns) {
	let html = `
		<div class="frappe-control">
			<div class="form-group">
				<div class="clearfix">
					<label class="control-label" style="padding-right: 0px;">
						<a class="btn btn-xs btn-default" href="/app/${doctype.toLowerCase().replace(/ /g, '-')}" target="_blank">
							View All ${doctype}
						</a>
					</label>
				</div>
				<div class="control-input-wrapper">
					<div class="control-value like-disabled-input" style="padding: 0;">
	`;

	if (data && data.length > 0) {
		html += `
						<table class="table table-bordered table-condensed" style="margin: 0;">
							<thead>
								<tr style="background-color: #f5f7fa;">
		`;

		columns.forEach(col => {
			html += `<th style="color: #6c757d; font-weight: 600;">${col.label}</th>`;
		});
		html += `<th style="color: #6c757d; font-weight: 600;">Actions</th></tr></thead><tbody>`;

		data.forEach(row => {
			html += '<tr>';
			columns.forEach(col => {
				let value = row[col.field];
				if (value) {
					if (col.type === 'Datetime') {
						value = moment(value).format('YYYY-MM-DD HH:mm:ss');
					} else if (col.type === 'Link') {
						value = `<a href="/app/${col.field.toLowerCase()}/${encodeURIComponent(value)}" target="_blank">${value}</a>`;
					}
					html += `<td>${value}</td>`;
				} else {
					html += '<td>-</td>';
				}
			});
			html += `<td>
				<a href="/app/${doctype.toLowerCase().replace(/ /g, '-')}/${row.name}" target="_blank" class="btn btn-xs btn-default">
					Edit
				</a>
			</td>`;
			html += '</tr>';
		});

		html += '</tbody></table>';
	} else {
		html += `<div class="text-muted" style="padding: 15px;">No ${doctype} records found</div>`;
	}

	html += `
					</div>
				</div>
			</div>
		</div>
	`;

	$(selector).html(html);
}
