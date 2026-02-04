/**
 * Chat Quick Actions Component
 * Quick actions for sending messages, assigning conversations, etc.
 */

frappe.provide('chat_bridge');

chat_bridge.QuickActions = {
	async sendMessage(conversationId, content) {
		try {
			const response = await frappe.call({
				method: 'chat_bridge.api.rest_api.send_message',
				args: {
					conversation_id: conversationId,
					content: content,
					message_type: 'outgoing'
				}
			});
			
			if (response.message && response.message.success) {
				frappe.show_alert({
					message: __('Message sent successfully'),
					indicator: 'green'
				});
				return response.message.data;
			} else {
				frappe.show_alert({
					message: __('Failed to send message'),
					indicator: 'red'
				});
			}
		} catch (error) {
			frappe.show_alert({
				message: __('Error sending message: {0}', [error.message]),
				indicator: 'red'
			});
		}
	},

	async updateStatus(conversationId, status) {
		try {
			const response = await frappe.call({
				method: 'chat_bridge.api.rest_api.update_conversation_status',
				args: {
					conversation_id: conversationId,
					status: status
				}
			});
			
			if (response.message && response.message.success) {
				frappe.show_alert({
					message: __('Conversation status updated'),
					indicator: 'green'
				});
				return response.message.data;
			}
		} catch (error) {
			frappe.show_alert({
				message: __('Error updating status: {0}', [error.message]),
				indicator: 'red'
			});
		}
	}
};

