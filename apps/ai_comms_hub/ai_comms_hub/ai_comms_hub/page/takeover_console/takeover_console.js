frappe.pages['takeover-console'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Takeover Console',
		single_column: false
	});

	// Initialize the console
	new TakeoverConsole(page);
};

class TakeoverConsole {
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

		// Build the layout
		this.wrapper.html(`
			<div class="takeover-console-container">
				<div class="row">
					<div class="col-md-4">
						<div class="takeover-sidebar">
							<div class="takeover-header mb-3">
								<h5><i class="fa fa-user"></i> My Active Conversations</h5>
								<small class="text-muted">Conversations you are actively handling</small>
							</div>
							<div class="takeover-conversation-list"></div>
						</div>
					</div>
					<div class="col-md-8">
						<div class="takeover-main-panel">
							<div class="takeover-empty-state">
								<div class="text-center text-muted py-5">
									<i class="fa fa-comments fa-3x mb-3"></i>
									<p>Select a conversation from the left to respond</p>
								</div>
							</div>
							<div class="takeover-conversation-panel" style="display: none;">
								<div class="takeover-conversation-header"></div>
								<div class="takeover-messages-container"></div>
								<div class="takeover-response-panel"></div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<style>
				.takeover-console-container {
					padding: 15px;
					height: calc(100vh - 120px);
				}
				.takeover-console-container .row {
					height: 100%;
				}
				.takeover-sidebar {
					height: 100%;
					border-right: 1px solid var(--border-color);
					padding-right: 15px;
				}
				.takeover-conversation-list {
					height: calc(100% - 70px);
					overflow-y: auto;
				}
				.takeover-conversation-item {
					padding: 12px;
					border: 1px solid var(--border-color);
					border-radius: 8px;
					margin-bottom: 10px;
					cursor: pointer;
					transition: all 0.2s;
					border-left: 4px solid var(--purple);
				}
				.takeover-conversation-item:hover {
					background-color: var(--bg-light-gray);
				}
				.takeover-conversation-item.selected {
					border-color: var(--primary);
					background-color: var(--control-bg);
				}
				.takeover-conversation-item.has-new {
					border-left-color: var(--red);
					animation: pulse 2s infinite;
				}
				@keyframes pulse {
					0%, 100% { opacity: 1; }
					50% { opacity: 0.7; }
				}
				.takeover-conversation-item .customer-name {
					font-weight: 600;
					margin-bottom: 4px;
				}
				.takeover-conversation-item .channel-badge {
					font-size: 11px;
					padding: 2px 6px;
					border-radius: 4px;
				}
				.takeover-conversation-item .timestamp {
					font-size: 11px;
					color: var(--text-muted);
				}
				.takeover-conversation-item .preview {
					font-size: 13px;
					color: var(--text-muted);
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
					margin-top: 6px;
				}
				.takeover-conversation-item .new-badge {
					background: var(--red);
					color: white;
					font-size: 10px;
					padding: 2px 6px;
					border-radius: 10px;
				}
				.takeover-main-panel {
					height: 100%;
					display: flex;
					flex-direction: column;
				}
				.takeover-conversation-header {
					padding: 15px;
					border-bottom: 1px solid var(--border-color);
					background: var(--bg-color);
				}
				.takeover-messages-container {
					flex: 1;
					overflow-y: auto;
					padding: 15px;
					background: var(--bg-light-gray);
				}
				.takeover-message {
					max-width: 80%;
					padding: 10px 15px;
					border-radius: 12px;
					margin-bottom: 10px;
				}
				.takeover-message.customer {
					background: white;
					border: 1px solid var(--border-color);
					margin-right: auto;
				}
				.takeover-message.ai {
					background: var(--bg-purple);
					color: var(--text-color);
					margin-left: auto;
				}
				.takeover-message.agent {
					background: var(--bg-green);
					color: var(--text-color);
					margin-left: auto;
				}
				.takeover-message.system {
					background: var(--bg-yellow);
					color: var(--text-color);
					margin: 0 auto;
					text-align: center;
					font-size: 12px;
				}
				.takeover-message .sender {
					font-size: 11px;
					font-weight: 600;
					margin-bottom: 4px;
				}
				.takeover-message .content {
					font-size: 14px;
					line-height: 1.5;
				}
				.takeover-message .time {
					font-size: 10px;
					color: var(--text-muted);
					margin-top: 4px;
				}
				.takeover-response-panel {
					padding: 15px;
					border-top: 1px solid var(--border-color);
					background: var(--bg-color);
				}
				.takeover-response-panel textarea {
					width: 100%;
					min-height: 100px;
					border: 1px solid var(--border-color);
					border-radius: 8px;
					padding: 10px;
					margin-bottom: 10px;
					resize: vertical;
				}
				.takeover-response-panel .response-actions {
					display: flex;
					gap: 10px;
					justify-content: space-between;
					align-items: center;
				}
				.takeover-response-panel .left-actions {
					display: flex;
					gap: 10px;
				}
				.channel-voice { background-color: var(--bg-purple); color: var(--purple); }
				.channel-sms { background-color: var(--bg-green); color: var(--green); }
				.channel-whatsapp { background-color: #25D366; color: white; }
				.channel-email { background-color: var(--bg-blue); color: var(--blue); }
				.channel-chat { background-color: var(--bg-cyan); color: var(--cyan); }
				.customer-info {
					background: var(--bg-light-gray);
					padding: 10px;
					border-radius: 6px;
					margin-top: 10px;
					font-size: 13px;
				}
			</style>
		`);
	}

	setup_realtime() {
		// Listen for new messages
		frappe.realtime.on('new_message', (data) => {
			if (this.selected_hub && data.hub_id === this.selected_hub) {
				this.load_messages(this.selected_hub);
			}
			// Mark conversation as having new message
			this.wrapper.find(`.takeover-conversation-item[data-hub="${data.hub_id}"]`).addClass('has-new');
			this.load_conversations();
		});

		// Listen for AI mode changes
		frappe.realtime.on('ai_mode_changed', (data) => {
			this.load_conversations();
			if (this.selected_hub && data.hub_id === this.selected_hub) {
				this.load_conversation_detail(this.selected_hub);
			}
		});
	}

	load_conversations() {
		// Load conversations assigned to current user in Takeover mode
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Communication Hub',
				filters: {
					ai_mode: 'Takeover',
					assigned_to: frappe.session.user,
					status: ['in', ['Open', 'In Progress']]
				},
				fields: [
					'name', 'customer_name', 'channel', 'status', 'ai_mode',
					'subject', 'sentiment', 'modified', 'customer_email', 'customer_phone'
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
		const list_container = this.wrapper.find('.takeover-conversation-list');
		list_container.empty();

		if (this.conversations.length === 0) {
			list_container.html(`
				<div class="text-center text-muted py-4">
					<i class="fa fa-inbox fa-2x mb-2"></i>
					<p>No conversations in takeover mode</p>
					<small>Use the HITL Console to take over conversations</small>
				</div>
			`);
			return;
		}

		this.conversations.forEach(conv => {
			const channel_class = `channel-${conv.channel.toLowerCase()}`;

			const item = $(`
				<div class="takeover-conversation-item ${this.selected_hub === conv.name ? 'selected' : ''}"
				     data-hub="${conv.name}">
					<div class="d-flex justify-content-between align-items-start">
						<div class="customer-name">${conv.customer_name || 'Unknown'}</div>
						<span class="timestamp">${frappe.datetime.prettyDate(conv.modified)}</span>
					</div>
					<div class="d-flex gap-2 mt-1">
						<span class="channel-badge ${channel_class}">${conv.channel}</span>
						${conv.sentiment === 'Negative' ? '<span class="badge bg-danger">Negative</span>' : ''}
					</div>
					<div class="preview">${conv.subject || conv.customer_email || conv.customer_phone || 'No subject'}</div>
				</div>
			`);

			item.on('click', () => {
				item.removeClass('has-new');
				this.select_conversation(conv.name);
			});

			list_container.append(item);
		});
	}

	select_conversation(hub_id) {
		this.selected_hub = hub_id;

		// Update selection UI
		this.wrapper.find('.takeover-conversation-item').removeClass('selected');
		this.wrapper.find(`.takeover-conversation-item[data-hub="${hub_id}"]`).addClass('selected');

		// Show conversation panel
		this.wrapper.find('.takeover-empty-state').hide();
		this.wrapper.find('.takeover-conversation-panel').show();

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
					this.render_response_panel(r.message);
				}
			}
		});
	}

	render_conversation_header(hub) {
		const header = this.wrapper.find('.takeover-conversation-header');

		header.html(`
			<div class="d-flex justify-content-between align-items-start">
				<div>
					<h4 class="mb-1">${hub.customer_name || 'Unknown Customer'}</h4>
					<div class="d-flex gap-2 align-items-center">
						<span class="channel-badge channel-${hub.channel.toLowerCase()}">${hub.channel}</span>
						<span class="badge bg-purple">Takeover Mode</span>
					</div>
					${hub.subject ? `<div class="mt-2"><strong>Subject:</strong> ${hub.subject}</div>` : ''}
					<div class="customer-info">
						${hub.customer_email ? `<div><i class="fa fa-envelope"></i> ${hub.customer_email}</div>` : ''}
						${hub.customer_phone ? `<div><i class="fa fa-phone"></i> ${hub.customer_phone}</div>` : ''}
					</div>
				</div>
				<div class="text-right">
					<div class="btn-group btn-group-sm">
						<button class="btn btn-outline-success btn-handback" title="Hand Back to AI">
							<i class="fa fa-robot"></i> Hand Back to AI
						</button>
						<button class="btn btn-outline-secondary btn-resolve" title="Mark Resolved">
							<i class="fa fa-check"></i> Resolve
						</button>
						<button class="btn btn-outline-secondary btn-view-doc" title="View Full Document">
							<i class="fa fa-external-link"></i>
						</button>
					</div>
				</div>
			</div>
		`);

		// Handback button
		header.find('.btn-handback').on('click', () => {
			this.handback_to_ai(hub.name);
		});

		// Resolve button
		header.find('.btn-resolve').on('click', () => {
			this.resolve_conversation(hub.name);
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
		const container = this.wrapper.find('.takeover-messages-container');
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
				<div class="takeover-message ${type_class}">
					<div class="sender">${msg.sender_name || msg.sender_type}</div>
					<div class="content">${frappe.utils.escape_html(content).replace(/\n/g, '<br>')}</div>
					<div class="time">${frappe.datetime.str_to_user(msg.timestamp)}</div>
				</div>
			`);
		});

		// Scroll to bottom
		container.scrollTop(container[0].scrollHeight);
	}

	render_response_panel(hub) {
		const panel = this.wrapper.find('.takeover-response-panel');

		// Character limit info based on channel
		const limits = {
			'Twitter': 280,
			'SMS': 320,
			'WhatsApp': 4096,
			'Facebook': 2000,
			'Instagram': 1000
		};
		const limit = limits[hub.channel] || null;
		const limit_info = limit ? `<small class="text-muted">Character limit: <span class="char-count">0</span>/${limit}</small>` : '';

		panel.html(`
			<textarea placeholder="Type your response here..." class="form-control" ${limit ? `maxlength="${limit}"` : ''}></textarea>
			<div class="response-actions">
				<div class="left-actions">
					<button class="btn btn-outline-secondary btn-sm btn-generate-ai" title="Get AI suggestion">
						<i class="fa fa-magic"></i> AI Suggest
					</button>
					<button class="btn btn-outline-secondary btn-sm btn-templates" title="Quick responses">
						<i class="fa fa-list"></i> Templates
					</button>
					${limit_info}
				</div>
				<button class="btn btn-primary btn-send-response">
					<i class="fa fa-paper-plane"></i> Send Response
				</button>
			</div>
		`);

		// Character counter
		if (limit) {
			panel.find('textarea').on('input', function() {
				panel.find('.char-count').text($(this).val().length);
			});
		}

		// Generate AI suggestion
		panel.find('.btn-generate-ai').on('click', () => {
			this.generate_ai_suggestion(hub.name);
		});

		// Templates button
		panel.find('.btn-templates').on('click', () => {
			this.show_templates_dialog(hub);
		});

		// Send response
		panel.find('.btn-send-response').on('click', () => {
			const content = panel.find('textarea').val().trim();
			if (content) {
				this.send_response(hub.name, content);
			} else {
				frappe.msgprint(__('Please enter a response'));
			}
		});

		// Enter to send (Ctrl+Enter)
		panel.find('textarea').on('keydown', (e) => {
			if (e.ctrlKey && e.key === 'Enter') {
				panel.find('.btn-send-response').click();
			}
		});
	}

	send_response(hub_id, content) {
		const btn = this.wrapper.find('.btn-send-response');
		btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Sending...');

		frappe.call({
			method: 'ai_comms_hub.api.message.send_agent_message',
			args: {
				hub_id: hub_id,
				content: content,
				sender_name: frappe.session.user_fullname
			},
			callback: (r) => {
				btn.prop('disabled', false).html('<i class="fa fa-paper-plane"></i> Send Response');
				if (r.message && r.message.success) {
					frappe.show_alert({
						message: __('Response sent'),
						indicator: 'green'
					});
					this.wrapper.find('.takeover-response-panel textarea').val('');
					this.load_messages(hub_id);
				} else {
					frappe.msgprint(__('Error: {0}', [r.message?.error || 'Unknown error']));
				}
			}
		});
	}

	handback_to_ai(hub_id) {
		frappe.confirm(
			__('Hand this conversation back to AI? The AI will resume autonomous responses.'),
			() => {
				frappe.call({
					method: 'ai_comms_hub.api.ai_engine.handback_conversation',
					args: { hub_id: hub_id },
					callback: (r) => {
						if (r.message && r.message.success) {
							frappe.show_alert({
								message: __('Conversation handed back to AI'),
								indicator: 'green'
							});
							this.selected_hub = null;
							this.wrapper.find('.takeover-conversation-panel').hide();
							this.wrapper.find('.takeover-empty-state').show();
							this.load_conversations();
						}
					}
				});
			}
		);
	}

	resolve_conversation(hub_id) {
		frappe.confirm(
			__('Mark this conversation as resolved?'),
			() => {
				frappe.call({
					method: 'frappe.client.set_value',
					args: {
						doctype: 'Communication Hub',
						name: hub_id,
						fieldname: {
							status: 'Resolved',
							ai_mode: 'Manual'
						}
					},
					callback: (r) => {
						if (r.message) {
							frappe.show_alert({
								message: __('Conversation resolved'),
								indicator: 'green'
							});
							this.selected_hub = null;
							this.wrapper.find('.takeover-conversation-panel').hide();
							this.wrapper.find('.takeover-empty-state').show();
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
			args: { hub_id: hub_id },
			callback: (r) => {
				btn.prop('disabled', false).html('<i class="fa fa-magic"></i> AI Suggest');
				if (r.message && r.message.suggestion) {
					this.wrapper.find('.takeover-response-panel textarea').val(r.message.suggestion);
					// Trigger character count update
					this.wrapper.find('.takeover-response-panel textarea').trigger('input');
				} else {
					frappe.msgprint(__('Could not generate suggestion'));
				}
			}
		});
	}

	show_templates_dialog(hub) {
		// Quick response templates
		const templates = [
			{ label: 'Greeting', text: 'Hello! Thank you for contacting us. How can I help you today?' },
			{ label: 'Please Wait', text: 'Let me check on that for you. Please hold on a moment.' },
			{ label: 'Need More Info', text: 'Could you please provide more details so I can better assist you?' },
			{ label: 'Apology', text: 'I apologize for any inconvenience this has caused. Let me help resolve this for you.' },
			{ label: 'Transfer', text: 'I\'ll connect you with a specialist who can better assist with this matter.' },
			{ label: 'Closing', text: 'Is there anything else I can help you with today?' },
			{ label: 'Thank You', text: 'Thank you for your patience. We appreciate your business!' }
		];

		let d = new frappe.ui.Dialog({
			title: __('Quick Response Templates'),
			fields: templates.map((t, i) => ({
				fieldname: `template_${i}`,
				fieldtype: 'Button',
				label: t.label,
				click: () => {
					this.wrapper.find('.takeover-response-panel textarea').val(t.text);
					this.wrapper.find('.takeover-response-panel textarea').trigger('input');
					d.hide();
				}
			}))
		});

		d.show();
	}
}
