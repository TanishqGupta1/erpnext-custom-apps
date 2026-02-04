"""
Chat API Wrapper
Handles all API calls to Chat with authentication and error handling
"""
import frappe
from frappe import _
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from typing import Dict, List, Optional, Any
import json

class ChatwootAPIError(Exception):
	"""Custom exception for Chat API errors"""
	pass

class ChatwootAPI:
	"""Wrapper class for Chat Application API"""
	
	def __init__(self, base_url: str, access_token: str, account_id: int):
		"""
		Initialize Chat API client
		
		Args:
			base_url: Chat instance base URL (e.g., https://msg.visualgraphx.com)
			access_token: API access token
			account_id: Chat account ID
		"""
		self.base_url = base_url.rstrip('/')
		self.access_token = access_token
		self.account_id = account_id
		self.timeout = 30  # Request timeout in seconds
	
	def _get_headers(self) -> Dict[str, str]:
		"""Get request headers with authentication"""
		return {
			'API-ACCESS-TOKEN': self.access_token,
			'Accept': 'application/json',
			'Content-Type': 'application/json'
		}
	
	def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
		"""
		Make HTTP request to Chat API
		
		Args:
			method: HTTP method (GET, POST, PUT, DELETE)
			endpoint: API endpoint (e.g., /api/v1/accounts/1/contacts)
			data: Request body data (for POST/PUT)
			params: Query parameters
		
		Returns:
			Response JSON data
		
		Raises:
			ChatwootAPIError: On API errors
		"""
		url = f"{self.base_url}{endpoint}"
		headers = self._get_headers()
		
		try:
			response = requests.request(
				method=method,
				url=url,
				headers=headers,
				json=data,
				params=params,
				timeout=self.timeout
			)
			
			# Handle different status codes
			if response.status_code == 401:
				raise ChatwootAPIError("Unauthorized: Invalid API token")
			elif response.status_code == 429:
				raise ChatwootAPIError("Rate limit exceeded: Too many requests")
			elif response.status_code == 503:
				raise ChatwootAPIError("Service unavailable: Chat server is down")
			elif response.status_code >= 400:
				error_msg = f"API error {response.status_code}"
				try:
					error_data = response.json()
					if 'error' in error_data:
						error_msg = error_data['error']
				except:
					error_msg = response.text or error_msg
				raise ChatwootAPIError(f"{error_msg} (Status: {response.status_code})")
			
			# Parse JSON response
			if response.text:
				return response.json()
			return {}
			
		except Timeout:
			raise ChatwootAPIError("Request timeout: Chat server did not respond in time")
		except ConnectionError:
			raise ChatwootAPIError("Connection error: Could not reach Chat server")
		except RequestException as e:
			raise ChatwootAPIError(f"Request failed: {str(e)}")
	
	# Account operations
	def get_account(self) -> Dict:
		"""Get account details"""
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/account')
	
	# Contact operations
	def get_contacts(self, page: int = 1, per_page: int = 20) -> Dict:
		"""List all contacts with pagination"""
		params = {'page': page, 'per_page': per_page}
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/contacts', params=params)
	
	def get_contact(self, contact_id: int) -> Dict:
		"""Get a specific contact by ID"""
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/contacts/{contact_id}')
	
	def create_contact(self, name: str, email: Optional[str] = None, phone_number: Optional[str] = None, 
	                  identifier: Optional[str] = None, custom_attributes: Optional[Dict] = None) -> Dict:
		"""Create a new contact"""
		data = {'name': name}
		if email:
			data['email'] = email
		if phone_number:
			data['phone_number'] = phone_number
		if identifier:
			data['identifier'] = identifier
		if custom_attributes:
			data['custom_attributes'] = custom_attributes
		
		return self._make_request('POST', f'/api/v1/accounts/{self.account_id}/contacts', data=data)
	
	def update_contact(self, contact_id: int, name: Optional[str] = None, email: Optional[str] = None,
	                  phone_number: Optional[str] = None, custom_attributes: Optional[Dict] = None) -> Dict:
		"""Update an existing contact"""
		data = {}
		if name:
			data['name'] = name
		if email:
			data['email'] = email
		if phone_number:
			data['phone_number'] = phone_number
		if custom_attributes:
			data['custom_attributes'] = custom_attributes
		
		return self._make_request('PUT', f'/api/v1/accounts/{self.account_id}/contacts/{contact_id}', data=data)
	
	def search_contacts(self, query: str) -> Dict:
		"""Search contacts by name, email, or phone"""
		params = {'q': query}
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/contacts/search', params=params)
	
	# Conversation operations
	def get_conversations(
		self,
		status: Optional[str] = "all",
		inbox_id: Optional[int] = None,
		page: int = 1,
		per_page: int = 20,
		assignee_type: str = "all",
	) -> Dict:
		"""List conversations with optional filters"""
		params = {
			'page': page,
			'per_page': per_page,
			'assignee_type': assignee_type or "all",
		}
		if status:
			params['status'] = status
		if inbox_id:
			params['inbox_id'] = inbox_id
		
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/conversations', params=params)
	
	def get_conversation(self, conversation_id: int) -> Dict:
		"""Get a specific conversation with messages"""
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/conversations/{conversation_id}')
	
	def update_conversation_status(self, conversation_id: int, status: str) -> Dict:
		"""Update conversation status (open, resolved, pending)"""
		data = {'status': status}
		return self._make_request('PUT', f'/api/v1/accounts/{self.account_id}/conversations/{conversation_id}', data=data)
	
	def assign_conversation(self, conversation_id: int, agent_id: int) -> Dict:
		"""Assign conversation to an agent"""
		data = {'assignee_id': agent_id}
		return self._make_request('PUT', f'/api/v1/accounts/{self.account_id}/conversations/{conversation_id}', data=data)
	
	def add_labels_to_conversation(self, conversation_id: int, labels: List[str]) -> Dict:
		"""Add labels to a conversation"""
		data = {'labels': labels}
		return self._make_request('POST', 
			f'/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/labels', data=data)
	
	# Message operations
	def get_messages(self, conversation_id: int, page: int = 1, per_page: int = 200) -> Dict:
		"""Get messages for a conversation"""
		params = {'page': page, 'per_page': per_page}
		return self._make_request('GET', 
			f'/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages', params=params)
	
	def send_message(self, conversation_id: int, content: str, message_type: str = 'outgoing',
	                content_type: str = 'text', content_attributes: Optional[Dict] = None,
	                private: bool = False) -> Dict:
		"""Send a message in a conversation"""
		data = {
			'content': content,
			'message_type': message_type,
			'content_type': content_type,
			'private': private
		}
		if content_attributes:
			data['content_attributes'] = content_attributes
		
		return self._make_request('POST', 
			f'/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages', data=data)
	
	# Inbox operations
	def get_inboxes(self) -> Dict:
		"""List all inboxes"""
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/inboxes')
	
	def get_inbox(self, inbox_id: int) -> Dict:
		"""Get a specific inbox"""
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/inboxes/{inbox_id}')
	
	# Label operations
	def get_labels(self) -> Dict:
		"""List all labels"""
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/labels')
	
	# Team operations
	def get_teams(self) -> Dict:
		"""List all teams"""
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/teams')

	# Webhook operations
	def get_webhooks(self) -> Dict:
		"""List all webhooks for the account"""
		return self._make_request('GET', f'/api/v1/accounts/{self.account_id}/webhooks')

	def create_webhook(self, url: str, subscriptions: Optional[List[str]] = None) -> Dict:
		"""
		Create a webhook for the account

		Args:
			url: Webhook endpoint URL
			subscriptions: List of events to subscribe to.
				Options: conversation_created, conversation_status_changed,
				         conversation_updated, message_created, message_updated,
				         webwidget_triggered, contact_created, contact_updated
		"""
		if subscriptions is None:
			subscriptions = [
				'conversation_created',
				'conversation_status_changed',
				'conversation_updated',
				'message_created',
				'message_updated',
				'contact_created',
				'contact_updated'
			]

		data = {
			'url': url,
			'subscriptions': subscriptions
		}
		return self._make_request('POST', f'/api/v1/accounts/{self.account_id}/webhooks', data=data)

	def delete_webhook(self, webhook_id: int) -> Dict:
		"""Delete a webhook by ID"""
		return self._make_request('DELETE', f'/api/v1/accounts/{self.account_id}/webhooks/{webhook_id}')

	def update_webhook(self, webhook_id: int, url: Optional[str] = None, subscriptions: Optional[List[str]] = None) -> Dict:
		"""Update an existing webhook"""
		data = {}
		if url:
			data['url'] = url
		if subscriptions:
			data['subscriptions'] = subscriptions
		return self._make_request('PUT', f'/api/v1/accounts/{self.account_id}/webhooks/{webhook_id}', data=data)

	@staticmethod
	def get_api_for_user(user: Optional[str] = None) -> 'ChatAPI':
		"""
		Get ChatwootAPI instance for current or specified user
		
		Args:
			user: ERPNext username (defaults to current user)
		
		Returns:
			ChatwootAPI instance configured with user's token
		
		Raises:
			frappe.ValidationError: If user token not found or settings not configured
		"""
		if not user:
			user = frappe.session.user
		
		# Get user token
		token_name = frappe.db.get_value("Chat User Token", {"user": user}, "name")
		if not token_name:
			frappe.throw(_("No Chat API token found for user {0}.").format(user), frappe.ValidationError)
		
		token_doc = frappe.get_doc("Chat User Token", token_name)
		
		# Get integration settings
		settings = frappe.get_single("Chat Integration Settings")
		if not settings.chat_base_url:
			frappe.throw("Chat Base URL not configured in Integration Settings")
		
		return ChatwootAPI(
			base_url=settings.chat_base_url,
			access_token=token_doc.get_password('api_access_token'),
			account_id=token_doc.account_id or settings.default_account_id
		)
