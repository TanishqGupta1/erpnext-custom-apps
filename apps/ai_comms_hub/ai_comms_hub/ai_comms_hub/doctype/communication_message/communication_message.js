// Copyright (c) 2025, VisualGraphX and contributors
// For license information, please see license.txt

frappe.ui.form.on('Communication Message', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.is_new()) {
			add_message_buttons(frm);
		}

		// Set delivery status indicator
		set_delivery_indicator(frm);

		// Show function call details if applicable
		if (frm.doc.is_function_call) {
			show_function_call_details(frm);
		}
	},

	is_function_call: function(frm) {
		// Toggle function call fields visibility
		frm.toggle_display("function_name", frm.doc.is_function_call);
		frm.toggle_display("function_args", frm.doc.is_function_call);
		frm.toggle_display("function_result", frm.doc.is_function_call);
		frm.toggle_display("function_success", frm.doc.is_function_call);
		frm.toggle_display("function_error", frm.doc.is_function_call);
	}
});

function add_message_buttons(frm) {
	// Mark as Delivered button
	if (frm.doc.delivery_status === "Pending" || frm.doc.delivery_status === "Sent") {
		frm.add_custom_button(__('Mark as Delivered'), function() {
			mark_as_delivered(frm);
		}, __('Delivery'));
	}

	// Mark as Read button
	if (frm.doc.delivery_status === "Delivered" && !frm.doc.read_by_customer) {
		frm.add_custom_button(__('Mark as Read'), function() {
			mark_as_read(frm);
		}, __('Delivery'));
	}

	// Retry Delivery button
	if (frm.doc.delivery_status === "Failed") {
		frm.add_custom_button(__('Retry Delivery'), function() {
			retry_delivery(frm);
		}, __('Delivery'));
	}

	// Execute Function button (if function call and not executed)
	if (frm.doc.is_function_call && !frm.doc.function_success && !frm.doc.function_error) {
		frm.add_custom_button(__('Execute Function'), function() {
			execute_function(frm);
		});
	}

	// View Conversation button
	frm.add_custom_button(__('View Conversation'), function() {
		frappe.set_route("Form", "Communication Hub", frm.doc.communication_hub);
	});
}

function set_delivery_indicator(frm) {
	let status_map = {
		"Pending": "orange",
		"Sent": "blue",
		"Delivered": "green",
		"Read": "green",
		"Failed": "red"
	};

	frm.get_field("delivery_status").set_indicator(
		frm.doc.delivery_status,
		status_map[frm.doc.delivery_status]
	);
}

function show_function_call_details(frm) {
	if (!frm.doc.function_result) {
		return;
	}

	try {
		let result = JSON.parse(frm.doc.function_result);

		frm.dashboard.add_comment(
			__('Function Result: {0}', [JSON.stringify(result, null, 2)]),
			'blue',
			true
		);
	} catch (e) {
		// Result is not valid JSON
	}
}

function mark_as_delivered(frm) {
	frappe.call({
		method: "ai_comms_hub.customer_support.doctype.communication_message.communication_message.mark_as_delivered",
		args: {
			message_id: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.show_alert({
					message: __('Message marked as delivered'),
					indicator: 'green'
				});
				frm.reload_doc();
			}
		}
	});
}

function mark_as_read(frm) {
	frappe.call({
		method: "ai_comms_hub.customer_support.doctype.communication_message.communication_message.mark_as_read",
		args: {
			message_id: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.show_alert({
					message: __('Message marked as read'),
					indicator: 'green'
				});
				frm.reload_doc();
			}
		}
	});
}

function retry_delivery(frm) {
	frappe.confirm(
		__('Are you sure you want to retry delivering this message?'),
		function() {
			frappe.call({
				method: "ai_comms_hub.api.message.deliver_message",
				args: {
					message_id: frm.doc.name
				},
				callback: function(r) {
					frappe.show_alert({
						message: __('Message delivery queued'),
						indicator: 'blue'
					});
					setTimeout(function() {
						frm.reload_doc();
					}, 2000);
				}
			});
		}
	);
}

function execute_function(frm) {
	frappe.show_alert({
		message: __('Executing function...'),
		indicator: 'blue'
	});

	frappe.call({
		method: "ai_comms_hub.customer_support.doctype.communication_message.communication_message.execute_function_call",
		args: {
			message_id: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				if (r.message.error) {
					frappe.msgprint({
						title: __('Function Execution Failed'),
						message: r.message.error,
						indicator: 'red'
					});
				} else {
					frappe.show_alert({
						message: __('Function executed successfully'),
						indicator: 'green'
					});
				}
				frm.reload_doc();
			}
		}
	});
}
