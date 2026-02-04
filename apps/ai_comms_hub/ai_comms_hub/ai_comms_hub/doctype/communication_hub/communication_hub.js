// Copyright (c) 2025, VisualGraphX and contributors
// For license information, please see license.txt

frappe.ui.form.on('Communication Hub', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.is_new()) {
			add_custom_buttons(frm);
		}

		// Add real-time updates
		setup_realtime_updates(frm);

		// Set indicator colors
		set_status_indicators(frm);

		// Show warnings
		show_warnings(frm);
	},

	onload: function(frm) {
		// Set queries for link fields
		set_link_queries(frm);
	},

	channel: function(frm) {
		// Show/hide channel-specific sections based on channel
		toggle_channel_sections(frm);
	},

	ai_mode: function(frm) {
		// Update UI based on AI mode
		update_ai_mode_ui(frm);
	},

	status: function(frm) {
		// Handle status change
		if (frm.doc.status === "Closed" && !frm.doc.closed_at) {
			frm.set_value("closed_at", frappe.datetime.now_datetime());
		}
	}
});

function add_custom_buttons(frm) {
	// View Conversation button
	frm.add_custom_button(__('View Conversation'), function() {
		view_conversation_dialog(frm);
	}, __('Actions'));

	// Takeover button (only in Autonomous or HITL mode)
	if (frm.doc.ai_mode === "Autonomous" || frm.doc.ai_mode === "HITL") {
		frm.add_custom_button(__('Take Over'), function() {
			takeover_conversation(frm);
		}, __('AI Control'));
	}

	// Hand Back button (only in Takeover mode)
	if (frm.doc.ai_mode === "Takeover") {
		frm.add_custom_button(__('Hand Back to AI'), function() {
			handback_to_ai(frm);
		}, __('AI Control'));
	}

	// HITL Draft Review buttons (when there's a draft to review)
	if (frm.doc.ai_draft_response && frm.doc.status === "Pending Review") {
		frm.add_custom_button(__('Approve Draft'), function() {
			approve_hitl_draft(frm);
		}, __('HITL Review'));

		frm.add_custom_button(__('Edit & Approve'), function() {
			edit_and_approve_draft(frm);
		}, __('HITL Review'));

		frm.add_custom_button(__('Reject Draft'), function() {
			reject_hitl_draft(frm);
		}, __('HITL Review'));

		// Highlight the HITL Review button group
		frm.page.get_inner_group_button(__('HITL Review')).addClass('btn-warning');
	}

	// Escalate to Human button (for Autonomous mode)
	if (frm.doc.ai_mode === "Autonomous" && frm.doc.status !== "Escalated") {
		frm.add_custom_button(__('Escalate to Human'), function() {
			escalate_to_human(frm);
		}, __('AI Control'));
	}

	// Generate Summary button
	if (frm.doc.total_messages > 0 && !frm.doc.context) {
		frm.add_custom_button(__('Generate Summary'), function() {
			generate_summary(frm);
		}, __('Actions'));
	}

	// View Knowledge Base button
	if (frm.doc.knowledge_base_used) {
		frm.add_custom_button(__('View Knowledge Used'), function() {
			view_knowledge_dialog(frm);
		}, __('Actions'));
	}

	// Send Message button (if conversation is open)
	if (frm.doc.status === "Open" || frm.doc.status === "In Progress" || frm.doc.status === "Escalated") {
		frm.add_custom_button(__('Send Message'), function() {
			send_message_dialog(frm);
		}, __('Actions'));
	}

	// Open HITL Console button
	frm.add_custom_button(__('HITL Console'), function() {
		frappe.set_route('hitl-console');
	}, __('Navigate'));

	// Open Takeover Console button
	if (frm.doc.ai_mode === "Takeover") {
		frm.add_custom_button(__('Takeover Console'), function() {
			frappe.set_route('takeover-console');
		}, __('Navigate'));
	}
}

function setup_realtime_updates(frm) {
	// Subscribe to real-time updates for this conversation
	frappe.realtime.on("communication_hub_update", function(data) {
		if (data.hub_id === frm.doc.name) {
			frm.reload_doc();
		}
	});

	// Listen for new messages
	frappe.realtime.on("new_message", function(data) {
		if (data.hub_id === frm.doc.name) {
			frappe.show_alert({
				message: __('New message received'),
				indicator: 'blue'
			});
			frm.reload_doc();
		}
	});

	// Listen for AI mode changes
	frappe.realtime.on("ai_mode_changed", function(data) {
		if (data.hub_id === frm.doc.name) {
			frm.reload_doc();
		}
	});
}

function set_status_indicators(frm) {
	// Set indicator based on status and AI mode
	let indicator_map = {
		"Open": "blue",
		"In Progress": "orange",
		"Pending Review": "yellow",
		"Escalated": "red",
		"Resolved": "green",
		"Closed": "gray"
	};

	let ai_mode_map = {
		"Autonomous": "green",
		"HITL": "orange",
		"Takeover": "red",
		"Manual": "gray"
	};

	frm.get_field("status").set_indicator(
		frm.doc.status,
		indicator_map[frm.doc.status]
	);

	frm.get_field("ai_mode").set_indicator(
		frm.doc.ai_mode,
		ai_mode_map[frm.doc.ai_mode]
	);
}

function show_warnings(frm) {
	// Show warning if outside 24-hour window for Meta platforms
	if ((frm.doc.channel === "Facebook" || frm.doc.channel === "Instagram") &&
	    !frm.doc.within_24h_window) {
		frm.dashboard.add_comment(
			__('This conversation is outside the 24-hour messaging window. You may need to use a message template.'),
			'orange',
			true
		);
	}

	// Show warning if negative sentiment
	if (frm.doc.sentiment === "Negative") {
		frm.dashboard.add_comment(
			__('Negative sentiment detected. Consider escalating to human agent.'),
			'red',
			true
		);
	}

	// Show warning if low RAG confidence
	if (frm.doc.rag_confidence && frm.doc.rag_confidence < 60) {
		frm.dashboard.add_comment(
			__('Low knowledge base confidence ({0}%). AI may need human guidance.', [frm.doc.rag_confidence]),
			'orange',
			true
		);
	}
}

function set_link_queries(frm) {
	// Filter assigned_to to only show Customer Support users
	frm.set_query("assigned_to", function() {
		return {
			query: "frappe.core.doctype.user.user.user_query",
			filters: {
				enabled: 1,
				"Has Role": ["in", ["Customer Support", "System Manager"]]
			}
		};
	});
}

function toggle_channel_sections(frm) {
	// Show/hide sections based on channel
	let channel = frm.doc.channel;

	// Voice section
	frm.toggle_display("section_voice", channel === "Voice");

	// Social section
	frm.toggle_display("section_social", ["Facebook", "Instagram", "Twitter", "LinkedIn"].includes(channel));

	// Email section
	frm.toggle_display("section_email", channel === "Email");

	// Chat section
	frm.toggle_display("section_chat", ["Chat", "WhatsApp", "SMS"].includes(channel));
}

function update_ai_mode_ui(frm) {
	// Change field colors based on AI mode
	let ai_mode = frm.doc.ai_mode;

	if (ai_mode === "Takeover") {
		frm.set_df_property("ai_mode", "bold", 1);
	} else {
		frm.set_df_property("ai_mode", "bold", 0);
	}
}

function view_conversation_dialog(frm) {
	// Show conversation history in a dialog
	frappe.call({
		method: "ai_comms_hub.customer_support.doctype.communication_hub.communication_hub.get_conversation_history",
		args: {
			hub_id: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.messages) {
				let messages = r.message.messages;

				let html = '<div class="conversation-history">';
				messages.forEach(function(msg) {
					let sender_class = msg.sender_type === "AI" ? "ai-message" :
					                   msg.sender_type === "Agent" ? "agent-message" :
					                   "customer-message";

					html += `
						<div class="message ${sender_class}">
							<div class="message-header">
								<strong>${msg.sender_name}</strong>
								<span class="text-muted">${frappe.datetime.str_to_user(msg.timestamp)}</span>
							</div>
							<div class="message-content">${msg.content}</div>
							${msg.is_function_call ? `<div class="function-call"><em>Function: ${msg.function_name}</em></div>` : ''}
						</div>
					`;
				});
				html += '</div>';

				// Add CSS
				html += `
					<style>
						.conversation-history { max-height: 500px; overflow-y: auto; }
						.message { padding: 10px; margin: 10px 0; border-radius: 5px; }
						.customer-message { background-color: #e3f2fd; }
						.ai-message { background-color: #f3e5f5; }
						.agent-message { background-color: #e8f5e9; }
						.message-header { margin-bottom: 5px; }
						.message-content { font-size: 14px; }
						.function-call { margin-top: 5px; font-size: 12px; color: #666; }
					</style>
				`;

				frappe.msgprint({
					title: __('Conversation History'),
					message: html,
					wide: true
				});
			}
		}
	});
}

function takeover_conversation(frm) {
	frappe.confirm(
		__('Are you sure you want to take over this conversation? The AI will pause and you will handle all responses.'),
		function() {
			frappe.call({
				method: "ai_comms_hub.api.ai_engine.takeover_conversation",
				args: {
					hub_id: frm.doc.name,
					agent_user: frappe.session.user
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __('Conversation taken over successfully'),
							indicator: 'green'
						});
						frm.reload_doc();
					}
				}
			});
		}
	);
}

function handback_to_ai(frm) {
	frappe.confirm(
		__('Are you sure you want to hand this conversation back to AI? The AI will resume autonomous responses.'),
		function() {
			frappe.call({
				method: "ai_comms_hub.api.ai_engine.handback_conversation",
				args: {
					hub_id: frm.doc.name
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __('Conversation handed back to AI'),
							indicator: 'green'
						});
						frm.reload_doc();
					}
				}
			});
		}
	);
}

function approve_hitl_draft(frm) {
	frappe.confirm(
		__('Approve and send the AI draft response as-is?'),
		function() {
			frappe.call({
				method: "ai_comms_hub.api.ai_engine.approve_hitl_draft",
				args: {
					hub_id: frm.doc.name
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __('Draft approved and sent'),
							indicator: 'green'
						});
						frm.reload_doc();
					} else {
						frappe.msgprint(__('Error: {0}', [r.message?.error || 'Unknown error']));
					}
				}
			});
		}
	);
}

function edit_and_approve_draft(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Edit AI Draft'),
		fields: [
			{
				fieldname: 'draft_response',
				fieldtype: 'Text Editor',
				label: __('Response'),
				reqd: 1,
				default: frm.doc.ai_draft_response
			}
		],
		primary_action_label: __('Approve & Send'),
		primary_action: function(values) {
			frappe.call({
				method: "ai_comms_hub.api.ai_engine.approve_hitl_draft",
				args: {
					hub_id: frm.doc.name,
					edited_response: values.draft_response
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __('Edited response approved and sent'),
							indicator: 'green'
						});
						d.hide();
						frm.reload_doc();
					} else {
						frappe.msgprint(__('Error: {0}', [r.message?.error || 'Unknown error']));
					}
				}
			});
		}
	});

	d.show();
}

function reject_hitl_draft(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Reject Draft & Send Custom Response'),
		fields: [
			{
				fieldname: 'info',
				fieldtype: 'HTML',
				options: '<p class="text-muted">The AI draft will be rejected. Enter your own response to send to the customer.</p>'
			},
			{
				fieldname: 'agent_response',
				fieldtype: 'Text Editor',
				label: __('Your Response'),
				reqd: 1
			}
		],
		primary_action_label: __('Send Response'),
		primary_action: function(values) {
			frappe.call({
				method: "ai_comms_hub.api.ai_engine.reject_hitl_draft",
				args: {
					hub_id: frm.doc.name,
					agent_response: values.agent_response
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __('Response sent'),
							indicator: 'green'
						});
						d.hide();
						frm.reload_doc();
					} else {
						frappe.msgprint(__('Error: {0}', [r.message?.error || 'Unknown error']));
					}
				}
			});
		}
	});

	d.show();
}

function escalate_to_human(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Escalate to Human Agent'),
		fields: [
			{
				fieldname: 'reason',
				fieldtype: 'Small Text',
				label: __('Escalation Reason'),
				reqd: 1,
				description: __('Why is this conversation being escalated?')
			}
		],
		primary_action_label: __('Escalate'),
		primary_action: function(values) {
			frappe.call({
				method: 'frappe.client.set_value',
				args: {
					doctype: 'Communication Hub',
					name: frm.doc.name,
					fieldname: {
						ai_mode: 'HITL',
						status: 'Escalated',
						escalation_reason: values.reason,
						escalated_at: frappe.datetime.now_datetime(),
						escalated_by_ai: 0
					}
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __('Conversation escalated to human agent'),
							indicator: 'orange'
						});
						d.hide();
						frm.reload_doc();
					}
				}
			});
		}
	});

	d.show();
}

function generate_summary(frm) {
	frappe.show_alert({
		message: __('Generating summary...'),
		indicator: 'blue'
	});

	frappe.call({
		method: "ai_comms_hub.api.llm.generate_conversation_summary",
		args: {
			hub_id: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				frm.set_value("context", r.message);
				frm.save();
				frappe.show_alert({
					message: __('Summary generated successfully'),
					indicator: 'green'
				});
			}
		}
	});
}

function view_knowledge_dialog(frm) {
	// Show knowledge base documents used
	if (!frm.doc.rag_documents) {
		frappe.msgprint(__('No knowledge base documents recorded'));
		return;
	}

	try {
		let docs = JSON.parse(frm.doc.rag_documents);
		let html = '<div class="knowledge-docs"><ul>';

		docs.forEach(function(doc) {
			html += `<li><strong>${doc.title || doc.id}</strong> (Score: ${doc.score})</li>`;
		});

		html += '</ul></div>';

		frappe.msgprint({
			title: __('Knowledge Base Documents Used'),
			message: html
		});
	} catch (e) {
		frappe.msgprint(__('Unable to parse knowledge base documents'));
	}
}

function send_message_dialog(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Send Message'),
		fields: [
			{
				fieldname: 'message',
				fieldtype: 'Text',
				label: __('Message'),
				reqd: 1
			},
			{
				fieldname: 'sender_type',
				fieldtype: 'Select',
				label: __('Send As'),
				options: 'Agent\nAI',
				default: 'Agent',
				reqd: 1
			}
		],
		primary_action_label: __('Send'),
		primary_action: function(values) {
			frappe.call({
				method: "ai_comms_hub.api.send_message",
				args: {
					hub_id: frm.doc.name,
					content: values.message,
					sender_type: values.sender_type,
					sender_name: frappe.session.user_fullname
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __('Message sent successfully'),
							indicator: 'green'
						});
						d.hide();
						frm.reload_doc();
					}
				}
			});
		}
	});

	d.show();
}
