/**
 * Chat Conversations Component
 * Vue component for displaying Chat conversations in CRM
 * 
 * TODO: Convert to proper Vue component file (.vue) when CRM frontend is ready
 */

frappe.provide('chat_bridge');

chat_bridge.ConversationsWidget = class {
	constructor(element) {
		this.element = element;
		this.conversations = [];
		this.loading = false;
		this.init();
	}

	async init() {
		await this.loadConversations();
		this.render();
	}

	async loadConversations() {
		this.loading = true;
		try {
			const response = await frappe.call({
				method: 'chat_bridge.api.rest_api.get_conversations',
				args: {
					status: 'open',
					page: 1,
					per_page: 20
				}
			});
			
			if (response.message && response.message.success) {
				this.conversations = response.message.data.payload || [];
			}
		} catch (error) {
			console.error('Error loading conversations:', error);
		} finally {
			this.loading = false;
		}
	}

	render() {
		// Basic rendering - will be replaced with Vue component
		const html = `
			<div class="chatwoot-conversations-widget">
				<h4>Chat Conversations</h4>
				${this.loading ? '<p>Loading...</p>' : ''}
				<ul>
					${this.conversations.map(conv => `
						<li>
							<a href="#" onclick="chat_bridge.openConversation(${conv.id})">
								${conv.contact?.name || 'Unknown'} - ${conv.status}
							</a>
						</li>
					`).join('')}
				</ul>
			</div>
		`;
		this.element.innerHTML = html;
	}
};

chat_bridge.openConversation = function(conversationId) {
	// Open conversation detail view in new Conversations page
	frappe.set_route('conversations');
	// TODO: Add conversation ID parameter to pre-select the conversation
};

