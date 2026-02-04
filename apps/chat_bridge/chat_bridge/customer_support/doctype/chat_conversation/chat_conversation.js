let chatwootStylesBootstrapped = false;

frappe.ui.form.on("Chat Conversation", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(__("Conversation records are created by the Chat sync job."));
			return;
		}

		hide_legacy_fields(frm);

		if (!frm.custom_buttons_added) {
			add_conversation_buttons(frm);
			frm.custom_buttons_added = true;
		}

		render_workspace(frm);
	},
});

function hide_legacy_fields(frm) {
	const fields_to_hide = [
		"last_message_preview",
	];
	fields_to_hide.forEach((fieldname) => {
		if (frm.get_field(fieldname)) {
			frm.toggle_display(fieldname, false);
		}
	});
}

function add_conversation_buttons(frm) {
	frm.clear_custom_buttons();
	frm.add_custom_button(__("Reply"), () => open_quick_reply(frm), __("Conversation"));
	frm.add_custom_button(__("Private Note"), () => open_quick_reply(frm, "private"), __("Conversation"));
	frm.add_custom_button(__("Mark Resolved"), () => update_status(frm, "resolved"), __("Conversation"));
	frm.add_custom_button(__("Re-open"), () => update_status(frm, "open"), __("Conversation"));
	frm.add_custom_button(__("Assign to me"), () => assign_to_me(frm), __("Conversation"));

	if (frm.doc.external_url) {
		frm.add_custom_button(
			__("Open in Chatwoot"),
			() => window.open(frm.doc.external_url, "_blank"),
			__("Conversation")
		);
	}
}

function update_status(frm, status) {
	frappe
		.xcall("chat_bridge.api.rest_api.update_conversation_status", {
			conversation_id: frm.doc.chat_conversation_id,
			status,
		})
		.then((r) => {
			if (r?.success) {
				frappe.show_alert({ message: __("Status updated to {0}", [status]), indicator: "green" });
				frm.reload_doc();
			} else {
				frappe.msgprint(r?.error || __("Unable to update status"));
			}
		});
}

function assign_to_me(frm) {
	frm.set_value("assigned_to", frappe.session.user);
	frm.save().then(() => {
		frappe.show_alert({ message: __("Assigned to you"), indicator: "green" });
	});
}

function open_quick_reply(frm, message_type = "outgoing") {
	const d = new frappe.ui.Dialog({
		title: message_type === "private" ? __("Add Private Note") : __("Reply to Contact"),
		fields: [
			{
				fieldname: "content",
				label: __("Message"),
				fieldtype: "Text Editor",
				reqd: 1,
			},
		],
		primary_action_label: __("Send"),
		primary_action(values) {
			frappe
				.xcall("chat_bridge.api.rest_api.send_message", {
					conversation_id: frm.doc.chat_conversation_id,
					content: values.content,
					message_type,
				})
				.then((r) => {
					if (r?.success) {
						frappe.show_alert({ message: __("Message sent"), indicator: "green" });
						frm.reload_doc();
					} else {
						frappe.msgprint(r?.error || __("Unable to send message"));
					}
				})
				.finally(() => d.hide());
		},
	});
	d.show();
}

function render_workspace(frm) {
	ensure_styles();
	render_overview_panel(frm);
	render_transcript_panel(frm);
	render_composer_panel(frm);
	render_sidebar_panel(frm);
	bind_workspace_events(frm);
}

function render_overview_panel(frm) {
	const section_field = frm.get_field("overview_section");
	if (!(section_field && section_field.$wrapper && section_field.$wrapper.length)) {
		return;
	}
	const overview_html = build_overview_column(frm);
	const target = section_field.$wrapper.find(".section-body");
	if (target.length) {
		target.html(overview_html);
	} else {
		section_field.$wrapper.html(overview_html);
	}
}

function render_transcript_panel(frm) {
	const transcript_field = frm.fields_dict.transcript_html;
	if (!transcript_field) {
		return;
	}
	const transcript_html = build_thread_column(frm);
	transcript_field.$wrapper.html(transcript_html);
}

function render_composer_panel(frm) {
	const composer_field = frm.fields_dict.composer_html;
	if (!composer_field) {
		return;
	}
	composer_field.$wrapper.html(build_composer_box(frm));
}

function render_sidebar_panel(frm) {
	if (frm.doc.contact && frm._contact_sidebar_info === undefined && !frm._contact_sidebar_fetching) {
		frm._contact_sidebar_fetching = true;
		frappe.db.get_value(
			"Contact",
			frm.doc.contact,
			["email_id", "mobile_no", "phone", "company_name"],
			(value) => {
				frm._contact_sidebar_info = value || null;
				frm._contact_sidebar_fetching = false;
				render_sidebar_panel(frm);
			}
		);
		return;
	}
	const sidebar = get_sidebar_wrapper(frm);
	if (!(sidebar && sidebar.length && sidebar.is(":visible"))) {
		frm._sidebar_retry_count = (frm._sidebar_retry_count || 0) + 1;
		if (frm._sidebar_retry_count <= 5) {
			setTimeout(() => render_sidebar_panel(frm), 200 * frm._sidebar_retry_count);
		}
		return;
	}
	frm._sidebar_retry_count = 0;
	let container = sidebar.find(".chatwoot-sidebar");
	if (!container.length) {
		container = $('<div class="chatwoot-sidebar chatwoot-sidecards"></div>');
		sidebar.prepend(container);
	}
	container.html(build_details_column(frm, frm._contact_sidebar_info));
	remove_default_tag_sections(sidebar);
	bind_sidebar_events(frm, sidebar);
}

function ensure_styles() {
	if (chatwootStylesBootstrapped) {
		return;
	}

	const style = document.createElement("style");
	style.innerHTML = `
		.chatwoot-card {
			background: var(--card-bg, var(--bg-color));
			border: 1px solid var(--border-color, #d0d7de);
			border-radius: 12px;
			padding: 1rem;
			box-shadow: 0 1px 2px rgba(15, 23, 42, 0.18);
		}
		body[data-theme="dark"] .chatwoot-card {
			background: var(--card-bg, #0d1117);
			border-color: var(--border-color, #30363d);
		}
		.chatwoot-card + .chatwoot-card {
			margin-top: 0.75rem;
		}
		.chatwoot-card-header {
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 0.5rem;
			font-weight: 600;
			margin-bottom: 0.75rem;
		}
		.chatwoot-card-actions {
			display: flex;
			gap: 0.35rem;
		}
		.chatwoot-card-actions button {
			border: 1px solid var(--border-color, #d0d7de);
			background: transparent;
			border-radius: 6px;
			padding: 0.1rem 0.55rem;
			font-size: 0.75rem;
			cursor: pointer;
			color: var(--text-color, #0f172a);
		}
		body[data-theme="dark"] .chatwoot-card-actions button {
			border-color: #30363d;
			color: #e2e8f0;
		}
		.chatwoot-card-actions button:hover {
			border-color: #1f6feb;
			color: #1f6feb;
		}
		.chatwoot-thread-card {
			display: flex;
			flex-direction: column;
		}
		.chatwoot-sidecards .chatwoot-card {
			margin-bottom: 0.75rem;
		}
		.chatwoot-contact-card .chatwoot-contact-name {
			font-size: 1rem;
			font-weight: 600;
			margin-bottom: 0.25rem;
		}
		.chatwoot-contact-card .chatwoot-contact-meta {
			display: flex;
			flex-direction: column;
			gap: 0.1rem;
			font-size: 0.85rem;
		}
		.chatwoot-contact-card .chatwoot-contact-meta span {
			color: var(--text-muted, #6b7280);
		}
		body[data-theme="dark"] .chatwoot-contact-card .chatwoot-contact-meta span {
			color: #94a3b8;
		}
		.chatwoot-contact-card .chatwoot-contact-meta strong {
			color: var(--text-color, #0f172a);
		}
		body[data-theme="dark"] .chatwoot-contact-card .chatwoot-contact-meta strong {
			color: #e2e8f0;
		}
		.chatwoot-sidebar-actions {
			display: flex;
			flex-direction: column;
			gap: 0.35rem;
		}
		.chatwoot-thread-scroll {
			overflow-y: auto;
			max-height: 520px;
			padding-right: 0.25rem;
		}
		.chatwoot-empty {
			color: var(--text-muted, #6b7280);
			text-align: center;
			padding: 2rem 1rem;
		}
		.chatwoot-msg {
			display: flex;
			align-items: flex-start;
			gap: 0.75rem;
			padding: 0.75rem;
			border-radius: 12px;
			margin-bottom: 0.5rem;
			border: 1px solid transparent;
		}
		.chatwoot-msg:last-child {
			margin-bottom: 0;
		}
		.chatwoot-msg.agent {
			flex-direction: row-reverse;
			background: rgba(31, 111, 235, 0.08);
		}
		body[data-theme="dark"] .chatwoot-msg.agent {
			background: rgba(56, 139, 253, 0.15);
		}
		.chatwoot-msg.contact {
			background: rgba(15, 23, 42, 0.05);
		}
		body[data-theme="dark"] .chatwoot-msg.contact {
			background: rgba(255, 255, 255, 0.05);
		}
		.chatwoot-msg.private {
			background: rgba(163, 113, 247, 0.1);
		}
		.chatwoot-msg.is-latest {
			border-color: #f97316;
			box-shadow: 0 0 0 1px rgba(249, 115, 22, 0.32);
		}
		.chatwoot-msg-avatar {
			width: 36px;
			height: 36px;
			border-radius: 50%;
			background: #1f2937;
			color: #fff;
			display: flex;
			align-items: center;
			justify-content: center;
			font-size: 0.75rem;
			font-weight: 600;
			text-transform: uppercase;
			flex-shrink: 0;
		}
		.chatwoot-msg.agent .chatwoot-msg-avatar {
			background: #1f6feb;
		}
		.chatwoot-msg.private .chatwoot-msg-avatar {
			background: #a371f7;
		}
		.chatwoot-msg-body {
			flex: 1;
			min-width: 0;
		}
		.chatwoot-msg-header {
			display: flex;
			justify-content: space-between;
			gap: 0.5rem;
			margin-bottom: 0.35rem;
			align-items: center;
		}
		.chatwoot-msg-sender {
			font-weight: 600;
			color: var(--text-color, #0f172a);
		}
		body[data-theme="dark"] .chatwoot-msg-sender {
			color: #f8fafc;
		}
		.chatwoot-msg-content {
			color: var(--text-color, #111827);
			line-height: 1.4;
			word-break: break-word;
		}
		body[data-theme="dark"] .chatwoot-msg-content {
			color: #e2e8f0;
		}
		.chatwoot-badge-new {
			background: linear-gradient(120deg, #f97316, #f59e0b);
			color: #fff;
			font-size: 0.65rem;
			font-weight: 700;
			padding: 0.1rem 0.35rem;
			border-radius: 999px;
			margin-right: 0.35rem;
		}
		.chatwoot-msg-time {
			color: var(--text-muted, #6b7280);
			font-size: 0.75rem;
			white-space: nowrap;
		}
		.chatwoot-composer {
			margin-top: 1rem;
			display: flex;
			flex-direction: column;
			gap: 0.5rem;
		}
		.chatwoot-composer textarea {
			min-height: 120px;
			resize: vertical;
			padding: 0.75rem;
			border-radius: 10px;
			border: 1px solid var(--border-color, #d0d7de);
			background: var(--bg-color, #fff);
			color: var(--text-color, #0f172a);
		}
		body[data-theme="dark"] .chatwoot-composer textarea {
			background: #0f172a;
			color: #f8fafc;
		}
		.chatwoot-composer-actions {
			display: flex;
			gap: 0.5rem;
		}
		.chatwoot-composer-hint {
			font-size: 0.75rem;
			color: var(--text-muted, #6b7280);
		}
		.chatwoot-props {
			display: flex;
			flex-direction: column;
			gap: 0.5rem;
		}
		.chatwoot-prop {
			display: flex;
			justify-content: space-between;
			gap: 0.75rem;
		}
		.chatwoot-prop-label {
			color: var(--text-muted, #6b7280);
			font-size: 0.85rem;
		}
		.chatwoot-pill {
			border-radius: 999px;
			padding: 0.1rem 0.7rem;
			font-size: 0.75rem;
			font-weight: 600;
			background: rgba(15, 23, 42, 0.07);
		}
		body[data-theme="dark"] .chatwoot-pill {
			background: rgba(148, 163, 184, 0.1);
		}
		.chatwoot-pill.status-open { color: #2563eb; }
		.chatwoot-pill.status-resolved { color: #059669; }
		.chatwoot-pill.status-pending { color: #d97706; }
		.chatwoot-pill.status-snoozed { color: #7c3aed; }
		.chatwoot-pill.status-closed { color: #6b7280; }
		.chatwoot-chip {
			display: inline-flex;
			align-items: center;
			gap: 0.25rem;
			margin: 0.15rem;
			padding: 0.1rem 0.65rem;
			border-radius: 999px;
			background: rgba(37, 99, 235, 0.1);
			color: var(--text-color, #1e293b);
			font-size: 0.75rem;
			font-weight: 500;
		}
		body[data-theme="dark"] .chatwoot-chip {
			color: #f8fafc;
		}
		.chatwoot-chip button {
			border: none;
			background: transparent;
			color: inherit;
			margin-left: 0.35rem;
			cursor: pointer;
			font-size: 0.85rem;
		}
		.chatwoot-chip button:hover {
			opacity: 0.7;
		}
		.chatwoot-filter-bar {
			display: flex;
			flex-wrap: wrap;
			gap: 0.4rem;
			margin-top: 0.75rem;
		}
		.chatwoot-filter-bar button {
			border: 1px solid var(--border-color, #d0d7de);
			background: transparent;
			padding: 0.25rem 0.75rem;
			border-radius: 999px;
			font-size: 0.75rem;
			cursor: pointer;
			transition: all 0.2s ease;
		}
		.chatwoot-filter-bar button.is-active {
			background: #1f6feb;
			color: #fff;
			border-color: #1f6feb;
		}
		.chatwoot-filter-bar button:hover {
			border-color: #1f6feb;
			color: #1f6feb;
		}
		.chatwoot-sidebar-links a {
			display: block;
			margin-bottom: 0.3rem;
			word-break: break-all;
		}
	`;
	document.head.appendChild(style);
	chatwootStylesBootstrapped = true;
}

function build_overview_column(frm) {
	const stats = [
		{ label: __("Status"), value: build_status_pill(frm.doc.status) },
		{ label: __("Priority"), value: build_priority_pill(frm.doc.priority) },
		{ label: __("Assigned To"), value: format_assignee(frm.doc.assigned_to) },
		{ label: __("Contact"), value: format_contact_reference(frm.doc.contact, frm.doc.contact_display) },
		{ label: __("Channel"), value: format_text(frm.doc.channel) },
		{ label: __("Inbox"), value: frm.doc.inbox_id ? `#${frappe.utils.escape_html(String(frm.doc.inbox_id))}` : __("Not set") },
		{ label: __("Last Message"), value: format_datetime(frm.doc.last_message_at) },
	];

	const filters = build_status_filters(frm.doc.status);
	const stats_html = stats
		.map(
			(stat) => `<div class="chatwoot-prop">
				<span class="chatwoot-prop-label">${stat.label}</span>
				<span class="chatwoot-prop-value">${stat.value || __("Not available")}</span>
			</div>`
		)
		.join("");

	const timeline = frm.doc.timeline_links
		? `<div class="chatwoot-card">
				<div class="chatwoot-card-header">${__("Linked Communications")}</div>
				<div class="chatwoot-sidebar-links">${frm.doc.timeline_links}</div>
			</div>`
		: "";

	return `
		<div class="chatwoot-card chatwoot-overview-card">
			<div class="chatwoot-card-header">${__("Conversation Overview")}</div>
			<div class="chatwoot-props">${stats_html}</div>
			${filters}
		</div>
		${timeline}
	`;
}

function build_thread_column(frm) {
	const messages_html = build_message_list(frm);

	return `
		<div class="chatwoot-card chatwoot-thread-card">
			<div class="chatwoot-card-header">${__("Conversation Transcript")}</div>
			${messages_html}
		</div>
	`;
}

function build_details_column(frm, contactDetails) {
	const info = [
		{ label: __("Chat Conversation ID"), value: format_text(frm.doc.chat_conversation_id) },
		{ label: __("Account ID"), value: format_text(frm.doc.account_id) },
		{ label: __("Inbox ID"), value: format_text(frm.doc.inbox_id) },
		{ label: __("Last Synced"), value: format_datetime(frm.doc.last_synced) },
		{ label: __("Messages Loaded"), value: `${(frm.doc.messages || []).length}` },
	];

	const info_html = info
		.map(
			(item) => `<div class="chatwoot-prop">
				<span class="chatwoot-prop-label">${item.label}</span>
				<span class="chatwoot-prop-value">${item.value || __("Not available")}</span>
			</div>`
		)
		.join("");

	const labels = (frm.doc.labels || []).map((row) => row.crm_label).filter(Boolean);
	const tags = get_doc_tags(frm);

	const labels_html = labels.length
		? labels
				.map(
					(label) => `<span class="chatwoot-chip" data-label="${frappe.utils.escape_html(label)}">
					${frappe.utils.escape_html(label)}
					<button type="button" data-action="remove-label" data-label="${frappe.utils.escape_html(label)}" title="${__(
						"Remove"
					)}">&times;</button>
				</span>`
				)
				.join("")
		: `<div class="text-muted small">${__("No labels attached")}</div>`;

	const tags_html = tags.length
		? tags
				.map(
					(tag) => `<span class="chatwoot-chip" data-tag="${frappe.utils.escape_html(tag)}">
					${frappe.utils.escape_html(tag)}
					<button type="button" data-action="remove-tag" data-tag="${frappe.utils.escape_html(tag)}" title="${__(
						"Remove"
					)}">&times;</button>
				</span>`
				)
				.join("")
		: `<div class="text-muted small">${__("No tags added yet")}</div>`;

	const actions = frm.doc.external_url
		? `<a class="btn btn-default btn-xs" target="_blank" rel="noopener" href="${frm.doc.external_url}">
				${__("Open Conversation in Chatwoot")}
			</a>`
		: `<div class="text-muted small">${__("External link unavailable")}</div>`;

	const notes = frm.doc.notes
		? `<div class="chatwoot-note">${frappe.utils.escape_html(frm.doc.notes).replace(/\n/g, "<br>")}</div>`
		: `<div class="text-muted small">${__("No agent notes yet")}</div>`;

	const contactSection = build_contact_sidebar(frm, contactDetails);

	return `
		${contactSection}
		<div class="chatwoot-card">
			<div class="chatwoot-card-header">${__("Conversation Details")}</div>
			<div class="chatwoot-props">${info_html}</div>
		</div>
		<div class="chatwoot-card" data-section="labels">
			<div class="chatwoot-card-header">
				<span>${__("Labels")}</span>
				<div class="chatwoot-card-actions">
					<button type="button" data-action="add-label">${__("Add")}</button>
				</div>
			</div>
			${labels_html}
		</div>
		<div class="chatwoot-card" data-section="tags">
			<div class="chatwoot-card-header">
				<span>${__("Tags")}</span>
				<div class="chatwoot-card-actions">
					<button type="button" data-action="add-tag">${__("Add")}</button>
				</div>
			</div>
			${tags_html}
		</div>
		<div class="chatwoot-card">
			<div class="chatwoot-card-header">${__("Actions")}</div>
			${actions}
		</div>
		<div class="chatwoot-card" data-section="notes">
			<div class="chatwoot-card-header">
				<span>${__("Agent Notes")}</span>
				<div class="chatwoot-card-actions">
					<button type="button" data-action="edit-notes">${__("Edit")}</button>
				</div>
			</div>
			${notes}
		</div>
	`;
}

function build_contact_sidebar(frm, contactDetails) {
	if (!frm.doc.contact && !contactDetails) {
		return "";
	}
	const name = frappe.utils.escape_html(frm.doc.contact_display || frm.doc.contact || __("Contact"));
	const email = contactDetails?.email_id || __("Not available");
	const phone = contactDetails?.mobile_no || contactDetails?.phone || __("Not available");
	const company = contactDetails?.company_name;
	const contactLink = frm.doc.contact
		? `<a class="btn btn-default btn-xs" target="_blank" rel="noopener" href="/app/contact/${encodeURIComponent(
				frm.doc.contact
		  )}">${__("Open Contact Record")}</a>`
		: "";

	return `<div class="chatwoot-card chatwoot-contact-card">
		<div class="chatwoot-card-header">${__("Contact")}</div>
		<div class="chatwoot-contact-name">${name}</div>
		<div class="chatwoot-contact-meta">
			<span><strong>${__("Email")}:</strong> ${frappe.utils.escape_html(email)}</span>
			<span><strong>${__("Phone")}:</strong> ${frappe.utils.escape_html(phone)}</span>
			${
				company
					? `<span><strong>${__("Company")}:</strong> ${frappe.utils.escape_html(company)}</span>`
					: ""
			}
		</div>
		<div class="chatwoot-sidebar-actions">${contactLink}</div>
	</div>`;
}

function build_status_filters(current_status) {
	const statuses = ["Open", "Pending", "Snoozed", "Resolved", "Closed"];
	const buttons = statuses
		.map(
			(status) => `<button type="button" data-filter-status="${status}" class="${
				status === current_status ? "is-active" : ""
			}">
				${__(status)}
			</button>`
		)
		.join("");
	return `<div class="chatwoot-filter-bar">${buttons}</div>`;
}

function build_status_pill(status) {
	if (!status) {
		return "";
	}
	const slug = String(status).toLowerCase();
	return `<span class="chatwoot-pill status-${slug}">${__(title_case(status))}</span>`;
}

function build_priority_pill(priority) {
	if (!priority || priority === "None") {
		return __("None");
	}
	return `<span class="chatwoot-pill">${__(title_case(priority))}</span>`;
}

function build_message_list(frm) {
	const seen = new Set();
	const messages = [];

	(frm.doc.messages || []).forEach((message) => {
		if (!message.message_id || seen.has(message.message_id)) {
			return;
		}
		seen.add(message.message_id);
		messages.push(message);
	});

	messages.sort((a, b) => new Date(b.sent_at || 0) - new Date(a.sent_at || 0));

	if (!messages.length) {
		return `<div class="chatwoot-empty">${__("No messages synced yet.")}</div>`;
	}

	const rows = messages
		.map((message, index) => build_message_row(frm, message, index === 0))
		.join("");

	return `<div class="chatwoot-thread-scroll">${rows}</div>`;
}

function build_message_row(frm, message, is_latest) {
	const direction = (message.direction || "").toLowerCase();
	const cls = direction === "outgoing" ? "agent" : direction === "private" ? "private" : "contact";
	const sender_name = frappe.utils.escape_html(get_sender_name(frm, message, direction));
	const tag = get_sender_tag(message, direction);
	const timestamp = format_datetime(message.sent_at);
	const body = format_message_body(message.content);
	const initials = derive_initials(sender_name);

	return `<div class="chatwoot-msg ${cls}${is_latest ? " is-latest" : ""}">
		<div class="chatwoot-msg-avatar">${initials}</div>
		<div class="chatwoot-msg-body">
			<div class="chatwoot-msg-header">
				<span class="chatwoot-msg-sender">${sender_name}${tag ? ` (${frappe.utils.escape_html(tag)})` : ""}</span>
				<span class="chatwoot-msg-meta">
					${is_latest ? `<span class="chatwoot-badge-new">${__("NEW")}</span>` : ""}
					<span class="chatwoot-msg-time">${timestamp}</span>
				</span>
			</div>
			<div class="chatwoot-msg-content">${body}</div>
		</div>
	</div>`;
}

function build_composer_box(frm) {
	return `<div class="chatwoot-card chatwoot-composer" data-conversation="${frm.doc.chat_conversation_id}">
		<div class="chatwoot-card-header">${__("Reply / Private Note")}</div>
		<textarea placeholder="${__("Write your reply or internal note...")}"></textarea>
		<div class="chatwoot-composer-actions">
			<button type="button" class="btn btn-primary" data-action="send">${__("Send Reply")}</button>
			<button type="button" class="btn btn-default" data-action="note">${__("Add Private Note")}</button>
		</div>
		<div class="chatwoot-composer-hint">${__("Press Ctrl + Enter to send quickly")}</div>
	</div>`;
}

function bind_workspace_events(frm) {
	const composer_wrapper = frm.fields_dict.composer_html?.$wrapper;
	if (composer_wrapper?.length) {
		const composer = composer_wrapper.find(".chatwoot-composer");
		const textarea = composer.find("textarea");
		composer.find("[data-action='send']").on("click", () => submit_composer(frm, textarea, "outgoing"));
		composer.find("[data-action='note']").on("click", () => submit_composer(frm, textarea, "private"));
		textarea.on("keydown", (event) => {
			if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
				event.preventDefault();
				submit_composer(frm, textarea, "outgoing");
			}
		});
	}

	const overview_wrapper = frm.get_field("overview_section")?.$wrapper;
	if (overview_wrapper?.length) {
		overview_wrapper.find("[data-filter-status]").on("click", (event) => {
			const status = event.currentTarget.dataset.filterStatus;
			if (status) {
				frappe.set_route("List", "Chat Conversation", { status });
			}
		});
	}
}

function bind_sidebar_events(frm, sidebar) {
	if (!(sidebar && sidebar.length)) {
		return;
	}

	sidebar.off(".chatwootSidebar");
	sidebar.on("click.chatwootSidebar", "[data-action='add-label']", () => prompt_add_label(frm));
	sidebar.on("click.chatwootSidebar", "[data-action='remove-label']", (event) =>
		remove_label_from_doc(frm, event.currentTarget.dataset.label)
	);
	sidebar.on("click.chatwootSidebar", "[data-action='add-tag']", () => prompt_add_tag(frm));
	sidebar.on("click.chatwootSidebar", "[data-action='remove-tag']", (event) =>
		remove_tag_from_doc(frm, event.currentTarget.dataset.tag)
	);
	sidebar.on("click.chatwootSidebar", "[data-action='edit-notes']", () => prompt_edit_notes(frm));
}

function submit_composer(frm, textarea, message_type) {
	const content = (textarea.val() || "").trim();
	if (!content) {
		frappe.show_alert({ message: __("Write a message first"), indicator: "orange" });
		textarea.focus();
		return;
	}

	const container = textarea.closest(".chatwoot-composer");
	const buttons = container.find("button");
	buttons.prop("disabled", true);
	textarea.prop("disabled", true);

	frappe
		.xcall("chat_bridge.api.rest_api.send_message", {
			conversation_id: frm.doc.chat_conversation_id,
			content,
			message_type,
		})
		.then((r) => {
			if (r?.success) {
				frappe.show_alert({ message: __("Message sent"), indicator: "green" });
				textarea.val("");
				frm.reload_doc();
			} else {
				frappe.msgprint(r?.error || __("Unable to send message"));
			}
		})
		.finally(() => {
			buttons.prop("disabled", false);
			textarea.prop("disabled", false);
		});
}

function get_sender_name(frm, message, direction) {
	if (message.sender_name) {
		return message.sender_name;
	}

	if (direction === "incoming" && frm.doc.contact_display) {
		return frm.doc.contact_display;
	}

	if (direction === "outgoing" && frm.doc.assigned_to) {
		const info = frappe.user_info(frm.doc.assigned_to);
		if (info && info.full_name) {
			return info.full_name;
		}
	}

	if (message.sender_type) {
		return title_case(message.sender_type.replace(/_/g, " "));
	}

	return __("Unknown");
}

function get_sender_tag(message, direction) {
	if (message.is_private || direction === "private") {
		return __("Private");
	}
	if (direction === "outgoing") {
		return __("Agent");
	}
	const sender_type = (message.sender_type || "").toLowerCase();
	if (sender_type.includes("bot")) {
		return __("Bot");
	}
	return __("User");
}

function derive_initials(value) {
	const cleaned = (value || "").trim();
	if (!cleaned) {
		return "CW";
	}
	const parts = cleaned.split(/\s+/);
	return parts
		.map((part) => part[0])
		.slice(0, 2)
		.join("")
		.toUpperCase();
}

function title_case(value) {
	return (value || "")
		.toLowerCase()
		.replace(/(^|\s)\S/g, (txt) => txt.toUpperCase());
}

function format_assignee(user) {
	if (!user) {
		return __("Unassigned");
	}
	const info = frappe.user_info(user);
	return info?.full_name ? frappe.utils.escape_html(info.full_name) : frappe.utils.escape_html(user);
}

function format_contact_reference(contact, display) {
	if (!contact && !display) {
		return __("Not linked");
	}
	const label = frappe.utils.escape_html(display || contact);
	if (!contact) {
		return label;
	}
	return `<a href="/app/contact/${encodeURIComponent(contact)}" target="_blank">${label}</a>`;
}

function format_text(value) {
	if (value === null || value === undefined || value === "") {
		return "";
	}
	return frappe.utils.escape_html(String(value));
}

function format_datetime(value) {
	if (!value) {
		return __("Unknown time");
	}
	try {
		return frappe.datetime.str_to_user(value);
	} catch (error) {
		return frappe.utils.escape_html(String(value));
	}
}

function format_message_body(content) {
	if (!content) {
		return `<span class="text-muted">${__("No content")}</span>`;
	}
	return frappe.utils.escape_html(content).replace(/\n/g, "<br>");
}

function get_doc_tags(frm) {
	return (frm.doc._user_tags || "")
		.split(",")
		.map((tag) => tag.trim())
		.filter(Boolean);
}

function get_sidebar_wrapper(frm) {
	let sidebar = null;
	if (frm.layout?.side_section?.wrapper) {
		sidebar = $(frm.layout.side_section.wrapper);
	} else if (frm.layout?.side_section?.$wrapper) {
		sidebar = frm.layout.side_section.$wrapper;
	} else if (frm.layout?.wrapper) {
		sidebar = frm.layout.wrapper
			.find(".form-sidebar, .form-side-section, .layout-side-section, .page-sidebar, .side-section")
			.first();
	}
	if ((!sidebar || !sidebar.length) && frm.sidebar?.wrapper) {
		sidebar = $(frm.sidebar.wrapper);
	}
	if ((!sidebar || !sidebar.length) && frm.page?.sidebar) {
		sidebar = $(frm.page.sidebar);
	}
	return sidebar && sidebar.length ? sidebar : null;
}

function remove_default_tag_sections(sidebar) {
	if (!(sidebar && sidebar.length)) {
		return;
	}
	const selectors = [
		".tags-section",
		".form-tags",
		".sidebar-tags",
		".tag-area",
		".sidebar-section:has(.sidebar-label:contains('Tags'))",
	];
	selectors.forEach((selector) => {
		const target = sidebar.find(selector);
		if (target.length) {
			target.remove();
		}
	});
}

function prompt_add_label(frm) {
	frappe.prompt(
		[
			{
				fieldname: "label",
				label: __("CRM Label"),
				fieldtype: "Link",
				options: "CRM Label",
				reqd: 1,
			},
		],
		(values) => {
			const label = values.label;
			if (!label) {
				return;
			}
			add_label_to_doc(frm, label);
		},
		__("Add Label")
	);
}

function add_label_to_doc(frm, label) {
	const exists = (frm.doc.labels || []).some((row) => row.crm_label === label);
	if (exists) {
		frappe.show_alert({ message: __("Label already added"), indicator: "orange" });
		return;
	}
	const child = frm.add_child("labels");
	child.crm_label = label;
	frm.save().then(() => frm.reload_doc());
}

function remove_label_from_doc(frm, label) {
	if (!label) {
		return;
	}
	const rows = (frm.doc.labels || []).filter((row) => row.crm_label !== label);
	if (rows.length === (frm.doc.labels || []).length) {
		return;
	}
	frm.clear_table("labels");
	rows.forEach((row) => {
		const child = frm.add_child("labels");
		child.crm_label = row.crm_label;
	});
	frm.save().then(() => frm.reload_doc());
}

function prompt_add_tag(frm) {
	frappe.prompt(
		[
			{
				fieldname: "tag",
				label: __("Tag"),
				fieldtype: "Data",
				reqd: 1,
			},
		],
		(values) => {
			const tag = (values.tag || "").trim();
			if (!tag) {
				return;
			}
			frappe
				.xcall("frappe.desk.doctype.tag.tag.add_tag", {
					tag,
					dt: frm.doctype,
					dn: frm.docname,
				})
				.then(() => {
					frappe.show_alert({ message: __("Tag added"), indicator: "green" });
					frm.reload_doc();
				});
		},
		__("Add Tag")
	);
}

function remove_tag_from_doc(frm, tag) {
	if (!tag) {
		return;
	}
	frappe
		.xcall("frappe.desk.doctype.tag.tag.remove_tag", {
			tag,
			dt: frm.doctype,
			dn: frm.docname,
		})
		.then(() => {
			frappe.show_alert({ message: __("Tag removed"), indicator: "green" });
			frm.reload_doc();
		});
}

function prompt_edit_notes(frm) {
	frappe.prompt(
		[
			{
				fieldname: "notes",
				label: __("Agent Notes"),
				fieldtype: "Small Text",
				default: frm.doc.notes || "",
			},
		],
		(values) => {
			frm.set_value("notes", values.notes || "");
			frm.save().then(() => frm.reload_doc());
		},
		__("Edit Agent Notes")
	);
}
