/**
 * Real-time handlers for Chat events
 * Extends ERPNext Socket.IO namespace for live conversation updates
 */

frappe.socketio.on('chatwoot:message:created', function(data) {
	// Broadcast new message to connected users
	if (data.conversation_id) {
		frappe.realtime.publish('chat_message', {
			conversation_id: data.conversation_id,
			message: data.message,
			contact: data.contact
		});
	}
});

frappe.socketio.on('chatwoot:conversation:updated', function(data) {
	// Broadcast conversation status/assignment changes
	if (data.conversation_id) {
		frappe.realtime.publish('chat_conversation_update', {
			conversation_id: data.conversation_id,
			status: data.status,
			assignee: data.assignee
		});
	}
});

