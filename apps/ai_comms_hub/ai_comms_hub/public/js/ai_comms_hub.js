/**
 * AI Communications Hub - Custom JavaScript
 * Copyright (c) 2025, VisualGraphX
 */

frappe.provide("ai_comms_hub");

/**
 * Initialize Communication Hub dashboard
 */
ai_comms_hub.init_dashboard = function() {
	frappe.call({
		method: "ai_comms_hub.api.dashboard.get_dashboard_data",
		callback: function(r) {
			if (r.message) {
				ai_comms_hub.render_dashboard(r.message);
			}
		}
	});
};

/**
 * Render dashboard metrics
 */
ai_comms_hub.render_dashboard = function(data) {
	const dashboard = $(".ai-comms-dashboard");

	if (!dashboard.length) return;

	// Render metrics cards
	const metrics_html = `
		<div class="row">
			<div class="col-md-3">
				<div class="analytics-card">
					<div class="analytics-metric">
						<div class="analytics-metric-label">Total Conversations</div>
						<div class="analytics-metric-value">${data.total_conversations}</div>
					</div>
				</div>
			</div>
			<div class="col-md-3">
				<div class="analytics-card">
					<div class="analytics-metric">
						<div class="analytics-metric-label">AI Resolution Rate</div>
						<div class="analytics-metric-value good">${data.ai_resolution_rate}%</div>
					</div>
				</div>
			</div>
			<div class="col-md-3">
				<div class="analytics-card">
					<div class="analytics-metric">
						<div class="analytics-metric-label">Avg Response Time</div>
						<div class="analytics-metric-value">${data.avg_response_time}s</div>
					</div>
				</div>
			</div>
			<div class="col-md-3">
				<div class="analytics-card">
					<div class="analytics-metric">
						<div class="analytics-metric-label">Escalation Rate</div>
						<div class="analytics-metric-value ${data.escalation_rate > 20 ? 'warning' : 'good'}">${data.escalation_rate}%</div>
					</div>
				</div>
			</div>
		</div>
	`;

	dashboard.html(metrics_html);
};

/**
 * Render message thread
 */
ai_comms_hub.render_messages = function(frm) {
	const messages = frm.doc.messages || [];
	const thread_html = messages.map(msg => {
		const sender_class = msg.sender_type.toLowerCase().replace(" ", "-");
		const avatar_text = msg.sender_type === "Customer" ? "C" :
		                   msg.sender_type === "AI Agent" ? "AI" : "H";

		const confidence_class = msg.rag_confidence >= 0.8 ? "high" :
		                        msg.rag_confidence >= 0.5 ? "medium" : "low";

		return `
			<div class="message-item ${sender_class}">
				<div class="message-avatar ${sender_class}">
					${avatar_text}
				</div>
				<div class="message-content">
					<div class="message-text">${frappe.utils.escape_html(msg.message_text)}</div>
					<div class="message-meta">
						<span class="message-timestamp">${frappe.datetime.str_to_user(msg.timestamp)}</span>
						${msg.rag_confidence ? `<span class="message-confidence ${confidence_class}">
							Confidence: ${(msg.rag_confidence * 100).toFixed(0)}%
						</span>` : ""}
					</div>
				</div>
			</div>
		`;
	}).join("");

	frm.fields_dict.message_thread.$wrapper.html(`
		<div class="message-thread">
			${thread_html}
		</div>
	`);

	// Scroll to bottom
	const thread = frm.fields_dict.message_thread.$wrapper.find(".message-thread");
	thread.scrollTop(thread[0].scrollHeight);
};

/**
 * Add quick action buttons
 */
ai_comms_hub.add_quick_actions = function(frm) {
	if (frm.doc.status === "Open" || frm.doc.status === "In Progress") {
		frm.add_custom_button(__("Escalate to Human"), function() {
			ai_comms_hub.escalate_conversation(frm);
		}, __("Actions"));

		frm.add_custom_button(__("Resolve"), function() {
			ai_comms_hub.resolve_conversation(frm);
		}, __("Actions"));
	}

	if (frm.doc.status === "Escalated") {
		frm.add_custom_button(__("Take Over"), function() {
			ai_comms_hub.takeover_conversation(frm);
		}, __("Actions"));
	}

	frm.add_custom_button(__("View Customer"), function() {
		frappe.set_route("Form", "Customer", frm.doc.customer);
	});
};

/**
 * Escalate conversation to human
 */
ai_comms_hub.escalate_conversation = function(frm) {
	frappe.prompt([
		{
			label: __("Escalation Reason"),
			fieldname: "reason",
			fieldtype: "Select",
			options: [
				"Negative Sentiment",
				"Low Confidence",
				"Human Requested",
				"Refund Request",
				"Technical Issue",
				"VIP Customer",
				"High Value Order",
				"Other"
			],
			reqd: 1
		},
		{
			label: __("Notes"),
			fieldname: "notes",
			fieldtype: "Small Text"
		}
	], function(values) {
		frappe.call({
			method: "ai_comms_hub.api.functions.escalate_to_human",
			args: {
				hub_id: frm.doc.name,
				reason: values.reason,
				notes: values.notes
			},
			callback: function(r) {
				if (r.message && r.message.escalated) {
					frappe.show_alert({
						message: __("Conversation escalated to human agent"),
						indicator: "orange"
					});
					frm.reload_doc();
				}
			}
		});
	}, __("Escalate to Human"));
};

/**
 * Resolve conversation
 */
ai_comms_hub.resolve_conversation = function(frm) {
	frappe.confirm(
		__("Are you sure you want to mark this conversation as resolved?"),
		function() {
			frappe.call({
				method: "frappe.client.set_value",
				args: {
					doctype: "Communication Hub",
					name: frm.doc.name,
					fieldname: "status",
					value: "Resolved"
				},
				callback: function(r) {
					frappe.show_alert({
						message: __("Conversation marked as resolved"),
						indicator: "green"
					});
					frm.reload_doc();
				}
			});
		}
	);
};

/**
 * Take over conversation (human)
 */
ai_comms_hub.takeover_conversation = function(frm) {
	frappe.confirm(
		__("Take over this conversation? AI will be disabled."),
		function() {
			frappe.call({
				method: "frappe.client.set_value",
				args: {
					doctype: "Communication Hub",
					name: frm.doc.name,
					fieldname: {
						ai_mode: "Human Takeover",
						status: "In Progress"
					}
				},
				callback: function(r) {
					frappe.show_alert({
						message: __("You are now handling this conversation"),
						indicator: "blue"
					});
					frm.reload_doc();
				}
			});
		}
	);
};

/**
 * Search knowledge base
 */
ai_comms_hub.search_knowledge_base = function(query, callback) {
	frappe.call({
		method: "ai_comms_hub.api.functions.search_knowledge_base",
		args: {
			query: query,
			top_k: 5
		},
		callback: function(r) {
			if (r.message && callback) {
				callback(r.message);
			}
		}
	});
};

/**
 * Show knowledge base search dialog
 */
ai_comms_hub.show_kb_search = function(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Search Knowledge Base"),
		fields: [
			{
				label: __("Search Query"),
				fieldname: "query",
				fieldtype: "Data",
				reqd: 1
			},
			{
				fieldname: "results",
				fieldtype: "HTML"
			}
		],
		primary_action_label: __("Search"),
		primary_action: function() {
			const query = dialog.get_value("query");

			ai_comms_hub.search_knowledge_base(query, function(results) {
				let results_html = "<ul class='kb-article-list'>";

				results.forEach(article => {
					results_html += `
						<li class="kb-article-item" onclick="ai_comms_hub.insert_kb_article('${article.title}', '${article.content}')">
							<div class="kb-article-title">${article.title}</div>
							<div class="kb-article-meta">Relevance: ${(article.score * 100).toFixed(0)}%</div>
						</li>
					`;
				});

				results_html += "</ul>";

				dialog.fields_dict.results.$wrapper.html(results_html);
			});
		}
	});

	dialog.show();
};

/**
 * Insert knowledge base article content
 */
ai_comms_hub.insert_kb_article = function(title, content) {
	frappe.show_alert({
		message: __("Article inserted: {0}", [title]),
		indicator: "green"
	});
	// Could copy to clipboard or insert into reply field
	navigator.clipboard.writeText(content);
};

/**
 * Real-time updates for conversations
 */
ai_comms_hub.setup_realtime = function(frm) {
	if (frm.doc.doctype !== "Communication Hub") return;

	frappe.realtime.on("new_message", function(data) {
		if (data.hub_id === frm.doc.name) {
			frappe.show_alert({
				message: __("New message received"),
				indicator: "blue"
			});
			frm.reload_doc();
		}
	});

	frappe.realtime.on("status_changed", function(data) {
		if (data.hub_id === frm.doc.name) {
			frm.reload_doc();
		}
	});
};

// Auto-initialize on page load
$(document).ready(function() {
	// Check if on Communication Hub form
	if (cur_frm && cur_frm.doc.doctype === "Communication Hub") {
		ai_comms_hub.setup_realtime(cur_frm);
	}
});
