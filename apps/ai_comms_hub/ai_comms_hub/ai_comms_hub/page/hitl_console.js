frappe.pages['hitl-console'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'HITL Console',
		single_column: false
	});

	// Initialize the console
	new HITLConsole(page);
};

class HITLConsole {
	constructor(page) {
		this.page = page;
		this.wrapper = $(page.body);
		this.selected_hub = null;
		this.conversations = [];

		this.setup_page();
		this.setup_realtime();
		this.load_conversations();
	}

	setup_page() {
		// Add page actions
		this.page.set_primary_action(__('Refresh'), () => {
			this.load_conversations();
		}, 'refresh');

		this.page.add_menu_item(__('Show All'), () => {
			this.filter = 'all';
			this.load_conversations();
		});

		this.page.add_menu_item(__('Pending Review Only'), () => {
			this.filter = 'pending';
			this.load_conversations();
		});

		this.page.add_menu_item(__('Escalated Only'), () => {
			this.filter = 'escalated';
			this.load_conversations();
		});

		// Build the layout
		this.wrapper.html(`
			<div class="hitl-console-container">
				<div class="row">
					<div class="col-md-4">
						<div class="hitl-sidebar">
							<div class="hitl-filters">
								<div class="btn-group btn-group-sm w-100 mb-3">
									<button class="btn btn-outline-secondary active" data-filter="all">All</button>
									<button class="btn btn-outline-warning" data-filter="pending">Pending</button>
									<button class="btn btn-outline-danger" data-filter="escalated">Escalated</button>
								</div>
							</div>
							<div class="hitl-conversation-list"></div>
						</div>
					</div>
					<div class="col-md-8">
						<div class="hitl-main-panel">
							<div class="hitl-empty-state">
								<div class="text-center text-muted py-5">
									<i class="fa fa-comments fa-3x mb-3"></i>
									<p>Select a conversation from the left to review</p>
								</div>
							</div>
							<div class="hitl-conversation-panel" style="display: none;">
								<div class="hitl-conversation-header"></div>
								<div class="hitl-messages-container"></div>
								<div class="hitl-draft-panel"></div>
								<div class="hitl-response-panel"></div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<style>
				.hitl-console-container {
					padding: 15px;
					height: calc(100vh - 120px);
				}
				.hitl-console-container .row {
					height: 100%;
				}
				.hitl-sidebar {
					height: 100%;
					border-right: 1px solid var(--border-color);
					padding-right: 15px;
				}
				.hitl-conversation-list {
					height: calc(100% - 50px);
					overflow-y: auto;
				}
				.hitl-conversation-item {
					padding: 12px;
					border: 1px solid var(--border-color);
					border-radius: 8px;
					margin-bottom: 10px;
					cursor: pointer;
					transition: all 0.2s;
				}
				.hitl-conversation-item:hover {
					background-color: var(--bg-light-gray);
				}
				.hitl-conversation-item.selected {
					border-color: var(--primary);
					background-color: var(--control-bg);
				}
				.hitl-conversation-item .customer-name {
					font-weight: 600;
					margin-bottom: 4px;
				}
				.hitl-conversation-item .channel-badge {
					font-size: 11px;
					padding: 2px 6px;
					border-radius: 4px;
				}
				.hitl-conversation-item .status-badge {
					font-size: 11px;
					padding: 2px 6px;
					border-radius: 4px;
				}
				.hitl-conversation-item .timestamp {
					font-size: 11px;
					color: var(--text-muted);
				}
				.hitl-conversation-item .preview {
					font-size: 13px;
					color: var(--text-muted);
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
					margin-top: 6px;
				}
				.hitl-main-panel {
					height: 100%;
					display: flex;
					flex-direction: column;
				}
				.hitl-conversation-header {
					padding: 15px;
					border-bottom: 1px solid var(--border-color);
					background: var(--bg-color);
				}
				.hitl-messages-container {
					flex: 1;
					overflow-y: auto;
					padding: 15px;
					background: var(--bg-light-gray);
				}
				.hitl-message {
					max-width: 80%;
					padding: 10px 15px;
					border-radius: 12px;
					margin-bottom: 10px;
				}
				.hitl-message.customer {
					background: white;
					border: 1px solid var(--border-color);
					margin-right: auto;
				}
				.hitl-message.ai {
					background: var(--bg-purple);
					color: var(--text-color);
					margin-left: auto;
				}
				.hitl-message.agent {
					background: var(--bg-green);
					color: var(--text-color);
					margin-left: auto;
				}
				.hitl-message.system {
					background: var(--bg-yellow);
					color: var(--text-color);
					margin: 0 auto;
					text-align: center;
					font-size: 12px;
				}
				.hitl-message .sender {
					font-size: 11px;
					font-weight: 600;
					margin-bottom: 4px;
				}
				.hitl-message .content {
					font-size: 14px;
					line-height: 1.5;
				}
				.hitl-message .time {
					font-size: 10px;
					color: var(--text-muted);
					margin-top: 4px;
				}
				.hitl-draft-panel {
					padding: 15px;
					background: var(--bg-orange);
					border-top: 2px solid var(--orange);
				}
				.hitl-draft-panel .draft-label {
					font-weight: 600;
					color: var(--orange);
					margin-bottom: 10px;
				}
				.hitl-draft-panel .draft-content {
					background: white;
					padding: 10px;
					border-radius: 8px;
					margin-bottom: 10px;
					min-height: 80px;
				}
				.hitl-draft-panel .draft-actions {
					display: flex;
					gap: 10px;
				}
				.hitl-response-panel {
					padding: 15px;
					border-top: 1px solid var(--border-color);
					background: var(--bg-color);
				}
				.hitl-response-panel textarea {
					width: 100%;
					min-height: 80px;
					border: 1px solid var(--border-color);
					border-radius: 8px;
					padding: 10px;
					margin-bottom: 10px;
					resize: vertical;
				}
				.hitl-response-panel .response-actions {
					display: flex;
					gap: 10px;
					justify-content: flex-end;
				}
				.status-pending { background-color: var(--bg-orange); color: var(--orange); }
				.status-escalated { background-color: var(--bg-red); color: var(--red); }
				.status-open { background-color: var(--bg-blue); color: var(--blue); }
				.channel-voice { background-color: var(--bg-purple); color: var(--purple); }
				.channel-sms { background-color: var(--bg-green); color: var(--green); }
				.channel-whatsapp { background-color: #25D366; color: white; }
				.channel-email { background-color: var(--bg-blue); color: var(--blue); }
				.channel-chat { background-color: var(--bg-cyan); color: var(--cyan); }
				.escalation-reason {
					background: var(--bg-red);
					color: var(--red);
					padding: 8px 12px;
					border-radius: 6px;
					font-size: 13px;
					margin-top: 10px;
				}
			</style>
		`);

		// Setup filter buttons
		this.wrapper.find('.hitl-filters .btn').on('click', (e) => {
			this.wrapper.find('.hitl-filters .btn').removeClass('active');
			$(e.target).addClass('active');
			this.filter = $(e.target).data('filter');
			this.load_conversations();
		});

		this.filter = 'all';
	}

	setup_realtime() {
		// Listen for HITL requests
		frappe.realtime.on('hitl_request', (data) => {
			frappe.show_alert({
				message: __('New HITL request: {0}', [data.customer || data.hub_id]),
				indicator: 'orange'
			}, 10);
			this.load_conversations();
		});

		// Listen for conversation updates
		frappe.realtime.on('communication_hub_update', (data) => {
			if (this.selected_hub && data.hub_id === this.selected_hub) {
				this.load_conversation_detail(this.selected_hub);
			}
			this.load_conversations();
		});

		// Listen for new messages
		frappe.realtime.on('new_message', (data) => {
			if (this.selected_hub && data.hub_id === this.selected_hub) {
				this.load_conversation_detail(this.selected_hub);
			}
		});
	}

	load_conversations() {
		let filters = {
			ai_mode: ['in', ['HITL', 'Takeover']]
		};

		if (this.filter === 'pending') {
			filters.status = 'Pending Review';
		} else if (this.filter === 'escalated') {
			filters.status = 'Escalated';
		} else {
			filters.status = ['in', ['Open', 'In Progress', 'Pending Review', 'Escalated']];
		}

		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Communication Hub',
				filters: filters,
				fields: [
					'name', 'customer_name', 'channel', 'status', 'ai_mode',
					'subject', 'sentiment', 'escalation_reason', 'modified',
					'ai_draft_response'
				],
				order_by: 'modified desc',
				limit_page_length: 50
			},
			callback: (r) => {
				this.conversations = r.message || [];
				this.render_conversation_list();
			}
		});
	}

	render_conversation_list() {
		const list_container = this.wrapper.find('.hitl-conversation-list');
		list_container.empty();

		if (this.conversations.length === 0) {
			list_container.html(`
				<div class="text-center text-muted py-4">
					<i class="fa fa-check-circle fa-2x mb-2"></i>
					<p>No conversations requiring attention</p>
				</div>
			`);
			return;
		}

		this.conversations.forEach(conv => {
			const status_class = conv.status === 'Pending Review' ? 'status-pending' :
			                     conv.status === 'Escalated' ? 'status-escalated' : 'status-open';
			const channel_class = `channel-${conv.channel.toLowerCase()}`;
			const has_draft = conv.ai_draft_response ? '<i class="fa fa-file-text-o text-warning ml-2" title="Has AI Draft"></i>' : '';

			const item = $(`
				<div class="hitl-conversation-item ${this.selected_hub === conv.name ? 'selected' : ''}"
				     data-hub="${conv.name}">
					<div class="d-flex justify-content-between align-items-start">
						<div class="customer-name">${conv.customer_name || 'Unknown'} ${has_draft}</div>
						<span class="timestamp">${frappe.datetime.prettyDate(conv.modified)}</span>
					</div>
					<div class="d-flex gap-2 mt-1">
						<span class="channel-badge ${channel_class}">${conv.channel}</span>
						<span class="status-badge ${status_class}">${conv.status}</span>
						${conv.sentiment === 'Negative' ? '<span class="badge bg-danger">Negative</span>' : ''}
					</div>
					<div class="preview">${conv.subject || conv.escalation_reason || 'No subject'}</div>
				</div>
			`);

			item.on('click', () => {
				this.select_conversation(conv.name);
			});

			list_container.append(item);
		});
	}

	select_conversation(hub_id) {
		this.selected_hub = hub_id;

		// Update selection UI
		this.wrapper.find('.hitl-conversation-item').removeClass('selected');
		this.wrapper.find(`.hitl-conversation-item[data-hub="${hub_id}"]`).addClass('selected');

		// Show conversation panel
		this.wrapper.find('.hitl-empty-state').hide();
		this.wrapper.find('.hitl-conversation-panel').show();

		this.load_conversation_detail(hub_id);
	}

	load_conversation_detail(hub_id) {
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Communication Hub',
				name: hub_id
			},
			callback: (r) => {
				if (r.message) {
					this.current_hub = r.message;
					this.render_conversation_header(r.message);
					this.load_messages(hub_id);
					this.render_draft_panel(r.message);
					this.render_response_panel(r.message);
				}
			}
		});
	}

	render_conversation_header(hub) {
		const header = this.wrapper.find('.hitl-conversation-header');

		header.html(`
			<div class="d-flex justify-content-between align-items-start">
				<div>
					<h4 class="mb-1">${hub.customer_name || 'Unknown Customer'}</h4>
					<div class="d-flex gap-2 align-items-center">
						<span class="channel-badge channel-${hub.channel.toLowerCase()}">${hub.channel}</span>
						<span class="text-muted">${hub.customer_email || hub.customer_phone || ''}</span>
					</div>
					${hub.subject ? `<div class="mt-2"><strong>Subject:</strong> ${hub.subject}</div>` : ''}
					${hub.escalation_reason ? `<div class="escalation-reason"><strong>Escalation Reason:</strong> ${hub.escalation_reason}</div>` : ''}
				</div>
				<div class="text-right">
					<div class="btn-group btn-group-sm">
						<button class="btn btn-outline-primary btn-takeover" title="Take Over Conversation">
							<i class="fa fa-hand-paper-o"></i> Take Over
						</button>
						<button class="btn btn-outline-secondary btn-view-doc" title="View Full Document">
							<i class="fa fa-external-link"></i>
						</button>
					</div>
					<div class="mt-2">
						<span class="badge ${hub.ai_mode === 'HITL' ? 'bg-warning' : 'bg-danger'}">${hub.ai_mode} Mode</span>
						<span class="badge ${hub.status === 'Escalated' ? 'bg-danger' : hub.status === 'Pending Review' ? 'bg-warning' : 'bg-info'}">${hub.status}</span>
					</div>
				</div>
			</div>
		`);

		// Takeover button
		header.find('.btn-takeover').on('click', () => {
			this.takeover_conversation(hub.name);
		});

		// View document button
		header.find('.btn-view-doc').on('click', () => {
			frappe.set_route('Form', 'Communication Hub', hub.name);
		});
	}

	load_messages(hub_id) {
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Communication Message',
				filters: { communication_hub: hub_id },
				fields: ['name', 'sender_type', 'sender_name', 'content', 'timestamp', 'is_function_call', 'function_name'],
				order_by: 'timestamp asc',
				limit_page_length: 100
			},
			callback: (r) => {
				this.render_messages(r.message || []);
			}
		});
	}

	render_messages(messages) {
		const container = this.wrapper.find('.hitl-messages-container');
		container.empty();

		messages.forEach(msg => {
			const type_class = msg.sender_type === 'Customer' ? 'customer' :
			                   msg.sender_type === 'AI' ? 'ai' :
			                   msg.sender_type === 'Agent' ? 'agent' : 'system';

			let content = msg.content;
			if (msg.is_function_call) {
				content = `<em><i class="fa fa-cog"></i> ${msg.function_name || 'Function Call'}</em><br>${content}`;
			}

			container.append(`
				<div class="hitl-message ${type_class}">
					<div class="sender">${msg.sender_name || msg.sender_type}</div>
					<div class="content">${frappe.utils.escape_html(content).replace(/\n/g, '<br>')}</div>
					<div class="time">${frappe.datetime.str_to_user(msg.timestamp)}</div>
				</div>
			`);
		});

		// Scroll to bottom
		container.scrollTop(container[0].scrollHeight);
	}

	render_draft_panel(hub) {
		const panel = this.wrapper.find('.hitl-draft-panel');

		if (!hub.ai_draft_response) {
			panel.hide();
			return;
		}

		panel.show();
		panel.html(`
			<div class="draft-label">
				<i class="fa fa-robot"></i> AI Draft Response (Pending Approval)
			</div>
			<div class="draft-content" contenteditable="true">${frappe.utils.escape_html(hub.ai_draft_response).replace(/\n/g, '<br>')}</div>
			<div class="draft-actions">
				<button class="btn btn-success btn-sm btn-approve-draft">
					<i class="fa fa-check"></i> Approve & Send
				</button>
				<button class="btn btn-warning btn-sm btn-approve-edited">
					<i class="fa fa-edit"></i> Approve with Edits
				</button>
				<button class="btn btn-danger btn-sm btn-reject-draft">
					<i class="fa fa-times"></i> Reject Draft
				</button>
			</div>
		`);

		// Approve draft as-is
		panel.find('.btn-approve-draft').on('click', () => {
			this.approve_draft(hub.name);
		});

		// Approve with edits
		panel.find('.btn-approve-edited').on('click', () => {
			const edited = panel.find('.draft-content').text();
			this.approve_draft(hub.name, edited);
		});

		// Reject draft
		panel.find('.btn-reject-draft').on('click', () => {
			panel.hide();
			this.wrapper.find('.hitl-response-panel textarea').focus();
		});
	}

	render_response_panel(hub) {
		const panel = this.wrapper.find('.hitl-response-panel');

		panel.html(`
			<textarea placeholder="Type your response here..." class="form-control"></textarea>
			<div class="response-actions">
				<button class="btn btn-outline-secondary btn-sm btn-generate-ai" title="Generate AI suggestion">
					<i class="fa fa-magic"></i> AI Suggest
				</button>
				<button class="btn btn-primary btn-sm btn-send-response">
					<i class="fa fa-paper-plane"></i> Send Response
				</button>
			</div>
		`);

		// Generate AI suggestion
		panel.find('.btn-generate-ai').on('click', () => {
			this.generate_ai_suggestion(hub.name);
		});

		// Send response
		panel.find('.btn-send-response').on('click', () => {
			const content = panel.find('textarea').val().trim();
			if (content) {
				this.send_agent_response(hub.name, content);
			} else {
				frappe.msgprint(__('Please enter a response'));
			}
		});
	}

	approve_draft(hub_id, edited_response = null) {
		frappe.call({
			method: 'ai_comms_hub.api.ai_engine.approve_hitl_draft',
			args: {
				hub_id: hub_id,
				edited_response: edited_response
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					frappe.show_alert({
						message: __('Draft approved and sent'),
						indicator: 'green'
					});
					this.load_conversation_detail(hub_id);
					this.load_conversations();
				} else {
					frappe.msgprint(__('Error: {0}', [r.message?.error || 'Unknown error']));
				}
			}
		});
	}

	send_agent_response(hub_id, content) {
		frappe.call({
			method: 'ai_comms_hub.api.ai_engine.reject_hitl_draft',
			args: {
				hub_id: hub_id,
				agent_response: content
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					frappe.show_alert({
						message: __('Response sent'),
						indicator: 'green'
					});
					this.wrapper.find('.hitl-response-panel textarea').val('');
					this.load_conversation_detail(hub_id);
					this.load_conversations();
				} else {
					frappe.msgprint(__('Error: {0}', [r.message?.error || 'Unknown error']));
				}
			}
		});
	}

	takeover_conversation(hub_id) {
		frappe.confirm(
			__('Take over this conversation? AI will be paused and you will handle all responses.'),
			() => {
				frappe.call({
					method: 'ai_comms_hub.api.ai_engine.takeover_conversation',
					args: {
						hub_id: hub_id,
						agent_user: frappe.session.user
					},
					callback: (r) => {
						if (r.message && r.message.success) {
							frappe.show_alert({
								message: __('Conversation taken over'),
								indicator: 'green'
							});
							this.load_conversation_detail(hub_id);
							this.load_conversations();
						}
					}
				});
			}
		);
	}

	generate_ai_suggestion(hub_id) {
		const btn = this.wrapper.find('.btn-generate-ai');
		btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Generating...');

		frappe.call({
			method: 'ai_comms_hub.api.ai_engine.generate_suggestion',
			args: {
				hub_id: hub_id
			},
			callback: (r) => {
				btn.prop('disabled', false).html('<i class="fa fa-magic"></i> AI Suggest');
				if (r.message && r.message.suggestion) {
					this.wrapper.find('.hitl-response-panel textarea').val(r.message.suggestion);
				} else {
					frappe.msgprint(__('Could not generate suggestion'));
				}
			}
		});
	}
}
