frappe.pages['conversations'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Conversations',
		single_column: true
	});

	// Initialize the Chatwoot-style workspace
	new ConversationsWorkspace(page);
};

class ConversationsWorkspace {
	constructor(page) {
		this.page = page;
		this.wrapper = $(this.page.body);
		this.current_conversation = null;
		this.conversations = [];
		this.filters = {
			status: null,
			priority: null,
			assigned_to: null,
			search: null
		};

		this.init();
	}

	init() {
		this.inject_styles();
		this.setup_layout();
		this.setup_filters();
		this.load_conversations();
		this.setup_realtime();
	}

	inject_styles() {
		if (!document.getElementById('chatwoot-conversations-styles')) {
			const style = document.createElement('style');
			style.id = 'chatwoot-conversations-styles';
			style.innerHTML = `
				.conversations-workspace {
					display: flex;
					height: calc(100vh - 130px);
					gap: 0;
					background: var(--bg-color);
				}

				/* Left Panel - Conversation List */
				.conversations-list-panel {
					width: 350px;
					min-width: 300px;
					max-width: 400px;
					border-right: 1px solid var(--border-color);
					display: flex;
					flex-direction: column;
					background: var(--card-bg);
				}

				.conversations-search {
					padding: 1rem;
					border-bottom: 1px solid var(--border-color);
				}

				.conversations-search input {
					width: 100%;
					padding: 0.5rem;
					border: 1px solid var(--border-color);
					border-radius: 6px;
					font-size: 14px;
				}

				.conversations-filters {
					padding: 0.75rem 1rem;
					border-bottom: 1px solid var(--border-color);
					display: flex;
					gap: 0.5rem;
					flex-wrap: wrap;
				}

				.filter-badge {
					display: inline-flex;
					align-items: center;
					gap: 0.25rem;
					padding: 0.25rem 0.5rem;
					background: var(--bg-blue);
					color: var(--text-color);
					border-radius: 4px;
					font-size: 12px;
					cursor: pointer;
				}

				.filter-badge:hover {
					background: var(--primary);
					color: white;
				}

				.conversations-list {
					flex: 1;
					overflow-y: auto;
					padding: 0.5rem;
				}

				.conversation-item {
					padding: 0.75rem;
					border-radius: 8px;
					margin-bottom: 0.5rem;
					cursor: pointer;
					border: 1px solid transparent;
					transition: all 0.2s;
				}

				.conversation-item:hover {
					background: var(--bg-light-gray);
					border-color: var(--border-color);
				}

				.conversation-item.active {
					background: var(--bg-blue);
					border-color: var(--primary);
				}

				.conversation-item-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					margin-bottom: 0.25rem;
				}

				.conversation-contact-name {
					font-weight: 600;
					font-size: 14px;
					color: var(--text-color);
				}

				.conversation-time {
					font-size: 11px;
					color: var(--text-muted);
				}

				.conversation-preview {
					font-size: 13px;
					color: var(--text-muted);
					overflow: hidden;
					text-overflow: ellipsis;
					white-space: nowrap;
					margin-bottom: 0.25rem;
				}

				.conversation-meta {
					display: flex;
					gap: 0.5rem;
					align-items: center;
				}

				.status-badge {
					display: inline-block;
					padding: 2px 6px;
					border-radius: 3px;
					font-size: 10px;
					font-weight: 600;
					text-transform: uppercase;
				}

				.status-badge.open { background: #ff9800; color: white; }
				.status-badge.pending { background: #ff5722; color: white; }
				.status-badge.resolved { background: #4caf50; color: white; }
				.status-badge.snoozed { background: #9e9e9e; color: white; }
				.status-badge.closed { background: #607d8b; color: white; }

				/* Center Panel - Conversation Transcript */
				.conversation-transcript-panel {
					flex: 1;
					display: flex;
					flex-direction: column;
					background: var(--card-bg);
				}

				.conversation-header {
					padding: 1rem;
					border-bottom: 1px solid var(--border-color);
					display: flex;
					justify-content: space-between;
					align-items: center;
				}

				.conversation-header-info h3 {
					margin: 0 0 0.25rem 0;
					font-size: 16px;
				}

				.conversation-header-meta {
					font-size: 12px;
					color: var(--text-muted);
				}

				.conversation-transcript {
					flex: 1;
					overflow-y: auto;
					padding: 1rem;
					background: var(--bg-light-gray);
				}

				.chatwoot-msg {
					display: flex;
					align-items: flex-start;
					gap: 0.75rem;
					padding: 0.75rem;
					border-radius: 12px;
					margin-bottom: 0.75rem;
					border: 1px solid transparent;
					max-width: 70%;
				}

				.chatwoot-msg.incoming {
					background: var(--gray-50, #f9fafb);
					align-self: flex-start;
				}

				.chatwoot-msg.outgoing {
					flex-direction: row-reverse;
					background: var(--blue-50, #eff6ff);
					margin-left: auto;
					align-self: flex-end;
				}

				.chatwoot-msg.private {
					background: var(--orange-50, #fff7ed);
					border-color: var(--orange-200, #fed7aa);
				}

				/* Dark mode overrides */
				[data-theme="dark"] .chatwoot-msg.incoming {
					background: rgba(255, 255, 255, 0.05);
				}

				[data-theme="dark"] .chatwoot-msg.outgoing {
					background: rgba(59, 130, 246, 0.15);
				}

				[data-theme="dark"] .chatwoot-msg.private {
					background: rgba(251, 146, 60, 0.15);
					border-color: rgba(251, 146, 60, 0.3);
				}

				.msg-avatar {
					width: 32px;
					height: 32px;
					border-radius: 50%;
					background: var(--primary);
					color: white;
					display: flex;
					align-items: center;
					justify-content: center;
					font-size: 14px;
					font-weight: 600;
					flex-shrink: 0;
				}

				.msg-content-wrapper {
					flex: 1;
					min-width: 0;
				}

				.msg-sender {
					font-size: 12px;
					font-weight: 600;
					color: var(--text-color);
					margin-bottom: 0.25rem;
				}

				.msg-content {
					font-size: 14px;
					color: var(--text-color, #1f2937);
					line-height: 1.5;
					word-wrap: break-word;
				}

				[data-theme="dark"] .msg-content {
					color: var(--text-color, #e5e7eb);
				}

				.msg-time {
					font-size: 11px;
					color: var(--text-muted);
					margin-top: 0.25rem;
				}

				.conversation-composer {
					padding: 1rem;
					border-top: 1px solid var(--border-color);
					background: var(--card-bg);
				}

				.composer-tabs {
					display: flex;
					gap: 1rem;
					margin-bottom: 0.5rem;
					border-bottom: 1px solid var(--border-color);
				}

				.composer-tab {
					padding: 0.5rem 0;
					cursor: pointer;
					border-bottom: 2px solid transparent;
					font-size: 13px;
					font-weight: 500;
					color: var(--text-muted);
				}

				.composer-tab.active {
					color: var(--text-color);
					border-bottom-color: var(--primary);
					font-weight: 600;
				}

				.composer-textarea {
					width: 100%;
					min-height: 80px;
					padding: 0.75rem;
					border: 1px solid var(--border-color);
					border-radius: 6px;
					font-size: 14px;
					resize: vertical;
					font-family: inherit;
				}

				.composer-actions {
					display: flex;
					justify-content: flex-end;
					gap: 0.5rem;
					margin-top: 0.5rem;
				}

				/* Right Panel - Details */
				.conversation-details-panel {
					width: 300px;
					min-width: 280px;
					max-width: 350px;
					border-left: 1px solid var(--border-color);
					overflow-y: auto;
					padding: 1rem;
					background: var(--card-bg);
				}

				.details-card {
					background: var(--bg-color);
					border: 1px solid var(--border-color);
					border-radius: 8px;
					padding: 1rem;
					margin-bottom: 1rem;
				}

				.details-card-header {
					font-size: 12px;
					font-weight: 600;
					text-transform: uppercase;
					color: var(--text-muted);
					margin-bottom: 0.75rem;
				}

				.details-field {
					margin-bottom: 0.75rem;
				}

				.details-field-label {
					font-size: 11px;
					font-weight: 600;
					color: var(--text-muted);
					margin-bottom: 0.25rem;
					text-transform: uppercase;
				}

				.details-field-value {
					font-size: 13px;
					color: var(--text-color, #374151);
					font-weight: 500;
				}

				[data-theme="dark"] .details-field-value {
					color: var(--text-color, #d1d5db);
				}

				.details-link {
					color: var(--primary, #2563eb);
					text-decoration: none;
					font-weight: 500;
				}

				.details-link:hover {
					text-decoration: underline;
					color: var(--primary-dark, #1d4ed8);
				}

				[data-theme="dark"] .details-link {
					color: #60a5fa;
				}

				[data-theme="dark"] .details-link:hover {
					color: #93c5fd;
				}

				.empty-state {
					display: flex;
					flex-direction: column;
					align-items: center;
					justify-content: center;
					height: 100%;
					color: var(--text-muted);
					text-align: center;
					padding: 2rem;
				}

				.empty-state-icon {
					font-size: 48px;
					margin-bottom: 1rem;
					opacity: 0.3;
				}

				.empty-state-text {
					font-size: 16px;
					font-weight: 500;
				}
			`;
			document.head.appendChild(style);
		}
	}

	setup_layout() {
		this.wrapper.html(`
			<div class="conversations-workspace">
				<div class="conversations-list-panel">
					<div class="conversations-search">
						<input type="text" placeholder="Search conversations..." class="conversation-search-input">
					</div>
					<div class="conversations-filters"></div>
					<div class="conversations-list"></div>
				</div>
				<div class="conversation-transcript-panel">
					<div class="empty-state">
						<div class="empty-state-icon">💬</div>
						<div class="empty-state-text">Select a conversation to view</div>
					</div>
				</div>
				<div class="conversation-details-panel">
					<div class="empty-state">
						<div class="empty-state-icon">ℹ️</div>
						<div class="empty-state-text">Conversation details will appear here</div>
					</div>
				</div>
			</div>
		`);

		// Setup search
		this.wrapper.find('.conversation-search-input').on('input', (e) => {
			this.filters.search = e.target.value;
			this.debounce_search();
		});
	}

	setup_filters() {
		// Add filter buttons to page
		this.page.add_field({
			fieldtype: 'Select',
			fieldname: 'status_filter',
			label: 'Status',
			options: ['All', 'Open', 'Pending', 'Snoozed', 'Resolved', 'Closed'],
			default: 'All',
			change: () => {
				const value = this.page.fields_dict.status_filter.get_value();
				this.filters.status = value === 'All' ? null : value;
				this.load_conversations();
			}
		});

		this.page.add_field({
			fieldtype: 'Select',
			fieldname: 'priority_filter',
			label: 'Priority',
			options: ['All', 'None', 'Low', 'Medium', 'High', 'Urgent'],
			default: 'All',
			change: () => {
				const value = this.page.fields_dict.priority_filter.get_value();
				this.filters.priority = value === 'All' ? null : value;
				this.load_conversations();
			}
		});

		this.page.add_field({
			fieldtype: 'Link',
			fieldname: 'assigned_filter',
			label: 'Assigned To',
			options: 'User',
			change: () => {
				this.filters.assigned_to = this.page.fields_dict.assigned_filter.get_value();
				this.load_conversations();
			}
		});
	}

	debounce_search() {
		clearTimeout(this.search_timeout);
		this.search_timeout = setTimeout(() => {
			this.load_conversations();
		}, 300);
	}

	load_conversations() {
		frappe.call({
			method: 'chat_bridge.customer_support.page.conversations.conversations.get_conversations',
			args: {
				filters: JSON.stringify(this.filters),
				limit: 50,
				offset: 0
			},
			callback: (r) => {
				if (r.message) {
					this.conversations = r.message;
					this.render_conversations_list();
				}
			}
		});
	}

	render_conversations_list() {
		const list_container = this.wrapper.find('.conversations-list');

		if (this.conversations.length === 0) {
			list_container.html(`
				<div class="empty-state">
					<div class="empty-state-icon">🔍</div>
					<div class="empty-state-text">No conversations found</div>
				</div>
			`);
			return;
		}

		const html = this.conversations.map(conv => this.render_conversation_item(conv)).join('');
		list_container.html(html);

		// Add click handlers
		list_container.find('.conversation-item').on('click', (e) => {
			const conv_name = $(e.currentTarget).data('name');
			this.select_conversation(conv_name);
		});
	}

	render_conversation_item(conv) {
		const time_ago = frappe.datetime.comment_when(conv.last_message_at);
		const status_class = (conv.status || 'open').toLowerCase();
		const active_class = this.current_conversation === conv.name ? 'active' : '';

		return `
			<div class="conversation-item ${active_class}" data-name="${conv.name}">
				<div class="conversation-item-header">
					<div class="conversation-contact-name">${frappe.utils.escape_html(conv.contact_display || 'Unknown')}</div>
					<div class="conversation-time">${time_ago}</div>
				</div>
				<div class="conversation-preview">${frappe.utils.escape_html(conv.last_message_preview || 'No messages')}</div>
				<div class="conversation-meta">
					<span class="status-badge ${status_class}">${conv.status || 'Open'}</span>
					${conv.channel ? `<span style="font-size: 11px; color: var(--text-muted);">${conv.channel}</span>` : ''}
				</div>
			</div>
		`;
	}

	select_conversation(conv_name) {
		this.current_conversation = conv_name;

		// Update active state in list
		this.wrapper.find('.conversation-item').removeClass('active');
		this.wrapper.find(`.conversation-item[data-name="${conv_name}"]`).addClass('active');

		// Load conversation details
		this.load_conversation_details(conv_name);
	}

	load_conversation_details(conv_name) {
		frappe.call({
			method: 'chat_bridge.customer_support.page.conversations.conversations.get_conversation_details',
			args: { conversation_name: conv_name },
			callback: (r) => {
				if (r.message) {
					this.render_conversation_transcript(r.message);
					this.render_conversation_details(r.message);
				}
			}
		});
	}

	render_conversation_transcript(data) {
		const { conversation, messages, contact_info } = data;
		const panel = this.wrapper.find('.conversation-transcript-panel');

		const contact_display = conversation.contact_display || 'Unknown Contact';

		panel.html(`
			<div class="conversation-header">
				<div class="conversation-header-info">
					<h3>${frappe.utils.escape_html(contact_display)}</h3>
					<div class="conversation-header-meta">
						<span class="status-badge ${(conversation.status || 'open').toLowerCase()}">${conversation.status || 'Open'}</span>
						${conversation.channel ? `• ${conversation.channel}` : ''}
						${conversation.assigned_to ? `• Assigned to ${conversation.assigned_to}` : ''}
					</div>
				</div>
				<div>
					<a href="/app/chat-conversation/${conversation.name}" class="btn btn-default btn-sm" target="_blank">
						Open in ERPNext
					</a>
				</div>
			</div>
			<div class="conversation-transcript" id="transcript-messages"></div>
			<div class="conversation-composer">
				<div class="composer-tabs">
					<div class="composer-tab active" data-type="reply">Reply</div>
					<div class="composer-tab" data-type="note">Private Note</div>
				</div>
				<textarea class="composer-textarea" placeholder="Type your message..."></textarea>
				<div class="composer-actions">
					<button class="btn btn-primary btn-sm send-message-btn">Send</button>
				</div>
			</div>
		`);

		// Render messages
		const transcript = panel.find('#transcript-messages');
		if (messages && messages.length > 0) {
			const msgs_html = messages.map(msg => this.render_message(msg)).join('');
			transcript.html(msgs_html);
			// Scroll to bottom
			transcript.scrollTop(transcript[0].scrollHeight);
		} else {
			transcript.html(`
				<div class="empty-state">
					<div class="empty-state-text">No messages yet</div>
				</div>
			`);
		}

		// Setup composer
		let message_type = 'outgoing';
		panel.find('.composer-tab').on('click', (e) => {
			panel.find('.composer-tab').removeClass('active');
			$(e.currentTarget).addClass('active');
			message_type = $(e.currentTarget).data('type') === 'note' ? 'private' : 'outgoing';
		});

		panel.find('.send-message-btn').on('click', () => {
			const message = panel.find('.composer-textarea').val().trim();
			if (message) {
				this.send_message(conversation.name, message, message_type);
			}
		});
	}

	render_message(msg) {
		const msg_type_class = msg.direction === 'Incoming' ? 'incoming' : msg.direction === 'Private' ? 'private' : 'outgoing';
		const sender_name = msg.sender_name || (msg.sender_type === 'contact' ? 'Customer' : 'Agent');
		const avatar_initial = sender_name.charAt(0).toUpperCase();
		const time_str = frappe.datetime.str_to_user(msg.sent_at);

		return `
			<div class="chatwoot-msg ${msg_type_class}">
				<div class="msg-avatar">${avatar_initial}</div>
				<div class="msg-content-wrapper">
					<div class="msg-sender">${frappe.utils.escape_html(sender_name)}</div>
					<div class="msg-content">${frappe.utils.escape_html(msg.content)}</div>
					<div class="msg-time">${time_str}</div>
				</div>
			</div>
		`;
	}

	send_message(conversation_name, message, message_type) {
		const is_private = message_type === 'private';

		frappe.call({
			method: 'chat_bridge.customer_support.page.conversations.conversations.send_message',
			args: {
				conversation_name: conversation_name,
				message: message,
				message_type: message_type,
				is_private: is_private
			},
			callback: (r) => {
				if (r.message) {
					// Clear textarea
					this.wrapper.find('.composer-textarea').val('');
					// Reload conversation
					this.load_conversation_details(conversation_name);
					// Reload conversation list to update preview
					this.load_conversations();
				}
			}
		});
	}

	render_conversation_details(data) {
		const { conversation, contact_info, labels } = data;
		const panel = this.wrapper.find('.conversation-details-panel');

		let html = '';

		// Contact Card
		html += `
			<div class="details-card">
				<div class="details-card-header">Contact</div>
				<div class="details-field">
					<div class="details-field-label">Name</div>
					<div class="details-field-value">
						${conversation.contact ?
							`<a href="/app/contact/${conversation.contact}" class="details-link" target="_blank">${frappe.utils.escape_html(conversation.contact_display || conversation.contact)}</a>` :
							frappe.utils.escape_html(conversation.contact_display || 'No contact linked')
						}
					</div>
				</div>
				${contact_info?.email_id ? `
					<div class="details-field">
						<div class="details-field-label">Email</div>
						<div class="details-field-value">${frappe.utils.escape_html(contact_info.email_id)}</div>
					</div>
				` : ''}
				${contact_info?.mobile_no ? `
					<div class="details-field">
						<div class="details-field-label">Mobile</div>
						<div class="details-field-value">${frappe.utils.escape_html(contact_info.mobile_no)}</div>
					</div>
				` : ''}
				${contact_info?.phone ? `
					<div class="details-field">
						<div class="details-field-label">Phone</div>
						<div class="details-field-value">${frappe.utils.escape_html(contact_info.phone)}</div>
					</div>
				` : ''}
				${contact_info?.company_name ? `
					<div class="details-field">
						<div class="details-field-label">Company</div>
						<div class="details-field-value">${frappe.utils.escape_html(contact_info.company_name)}</div>
					</div>
				` : ''}
			</div>
		`;

		// Conversation Info Card
		html += `
			<div class="details-card">
				<div class="details-card-header">Conversation</div>
				<div class="details-field">
					<div class="details-field-label">Status</div>
					<div class="details-field-value">
						<select class="form-control form-control-sm update-field" data-field="status">
							<option value="Open" ${conversation.status === 'Open' ? 'selected' : ''}>Open</option>
							<option value="Pending" ${conversation.status === 'Pending' ? 'selected' : ''}>Pending</option>
							<option value="Snoozed" ${conversation.status === 'Snoozed' ? 'selected' : ''}>Snoozed</option>
							<option value="Resolved" ${conversation.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
							<option value="Closed" ${conversation.status === 'Closed' ? 'selected' : ''}>Closed</option>
						</select>
					</div>
				</div>
				<div class="details-field">
					<div class="details-field-label">Priority</div>
					<div class="details-field-value">
						<select class="form-control form-control-sm update-field" data-field="priority">
							<option value="None" ${conversation.priority === 'None' ? 'selected' : ''}>None</option>
							<option value="Low" ${conversation.priority === 'Low' ? 'selected' : ''}>Low</option>
							<option value="Medium" ${conversation.priority === 'Medium' ? 'selected' : ''}>Medium</option>
							<option value="High" ${conversation.priority === 'High' ? 'selected' : ''}>High</option>
							<option value="Urgent" ${conversation.priority === 'Urgent' ? 'selected' : ''}>Urgent</option>
						</select>
					</div>
				</div>
				<div class="details-field">
					<div class="details-field-label">Assigned To</div>
					<div class="details-field-value">${conversation.assigned_to || 'Unassigned'}</div>
				</div>
			</div>
		`;

		// CRM Links Card
		html += `
			<div class="details-card">
				<div class="details-card-header">CRM Links</div>
				<div class="details-field">
					<div class="details-field-label">Customer</div>
					<div class="details-field-value">
						${conversation.customer ? `<a href="/app/customer/${conversation.customer}" class="details-link" target="_blank">${frappe.utils.escape_html(conversation.customer)}</a>` : 'Not linked'}
					</div>
				</div>
				<div class="details-field">
					<div class="details-field-label">Lead</div>
					<div class="details-field-value">
						${conversation.lead ? `<a href="/app/lead/${conversation.lead}" class="details-link" target="_blank">${frappe.utils.escape_html(conversation.lead)}</a>` : 'Not linked'}
					</div>
				</div>
				<div class="details-field">
					<div class="details-field-label">Support Issue</div>
					<div class="details-field-value">
						${conversation.issue ? `<a href="/app/issue/${conversation.issue}" class="details-link" target="_blank">${frappe.utils.escape_html(conversation.issue)}</a>` : 'Not linked'}
					</div>
				</div>
			</div>
		`;

		// Labels
		if (labels && labels.length > 0) {
			html += `
				<div class="details-card">
					<div class="details-card-header">Labels</div>
					<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
						${labels.map(l => `<span style="padding: 2px 8px; background: ${l.color || '#ccc'}; color: white; border-radius: 3px; font-size: 11px;">${frappe.utils.escape_html(l.label_name)}</span>`).join('')}
					</div>
				</div>
			`;
		}

		// Notes
		if (conversation.notes) {
			html += `
				<div class="details-card">
					<div class="details-card-header">Notes</div>
					<div>${frappe.utils.escape_html(conversation.notes)}</div>
				</div>
			`;
		}

		panel.html(html);

		// Setup field update handlers
		panel.find('.update-field').on('change', (e) => {
			const field = $(e.currentTarget).data('field');
			const value = $(e.currentTarget).val();
			this.update_conversation_field(conversation.name, field, value);
		});
	}

	update_conversation_field(conversation_name, fieldname, value) {
		frappe.call({
			method: 'chat_bridge.customer_support.page.conversations.conversations.update_conversation_field',
			args: {
				conversation_name: conversation_name,
				fieldname: fieldname,
				value: value
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					frappe.show_alert({ message: __('Updated'), indicator: 'green' });
					// Reload conversation list to reflect changes
					this.load_conversations();
				}
			}
		});
	}

	setup_realtime() {
		// Setup realtime updates for new messages
		frappe.realtime.on('chat_message_received', (data) => {
			if (this.current_conversation === data.conversation) {
				this.load_conversation_details(this.current_conversation);
			}
			// Reload list to update preview
			this.load_conversations();
		});
	}
}
