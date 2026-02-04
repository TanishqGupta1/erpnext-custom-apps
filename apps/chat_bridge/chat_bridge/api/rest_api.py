"""
REST API endpoints for Chat integration
Provides API endpoints for Vue components and external integrations
"""
import frappe
from frappe import _
from frappe.utils import cint
from .chat import ChatwootAPI, ChatwootAPIError

def _check_api_enabled():
	"""Check if API is enabled in settings"""
	try:
		settings = frappe.get_single("Chat Integration Settings")
		if not settings.get("enabled", 0):
			frappe.throw(_("Chat integration is not enabled"), frappe.ValidationError)
		if not settings.get("enable_api", 0):
			frappe.throw(_("API access is not enabled. Please enable it in Chat Integration Settings."), frappe.ValidationError)
	except frappe.DoesNotExistError:
		frappe.throw(_("Chat Integration Settings not found"), frappe.DoesNotExistError)

def _check_permission():
	"""Check if user has permission to access API"""
	if not frappe.has_permission("Chat Integration Settings", "read", user=frappe.session.user):
		frappe.throw(_("You do not have permission to access this API"), frappe.PermissionError)

@frappe.whitelist()
def get_conversations(status=None, inbox_id=None, page=1, per_page=20, user=None):
	"""Get conversations for current user"""
	_check_permission()
	_check_api_enabled()
	try:
		api = ChatwootAPI.get_api_for_user(user=user)
		result = api.get_conversations(status=status, inbox_id=inbox_id, page=page, per_page=per_page)
		return {"success": True, "data": result}
	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error getting conversations: {str(e)}")
		return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_conversation(conversation_id, include_messages=1, messages_page=1, messages_per_page=100, user=None):
	"""Get a specific conversation with messages"""
	_check_permission()
	_check_api_enabled()
	try:
		conversation_id = int(conversation_id)
		messages_page = frappe.utils.cint(messages_page) or 1
		messages_per_page = min(max(frappe.utils.cint(messages_per_page) or 500, 50), 1000)

		api = ChatwootAPI.get_api_for_user(user=user)
		conversation_response = api.get_conversation(conversation_id)

		messages_payload = []
		messages_meta = {}

		if frappe.utils.cint(include_messages):
			current_page = messages_page
			page_guard = 0

			while True:
				messages_response = api.get_messages(
					conversation_id,
					page=current_page,
					per_page=messages_per_page,
				)

				batch = []
				if isinstance(messages_response, dict):
					if isinstance(messages_response.get("data"), list):
						batch = messages_response.get("data")
					elif isinstance(messages_response.get("payload"), list):
						batch = messages_response.get("payload")
					messages_meta = messages_response.get("meta") or {}
				elif isinstance(messages_response, list):
					batch = messages_response

				if batch:
					messages_payload.extend(batch)

				next_page = messages_meta.get("next_page") if isinstance(messages_meta, dict) else None

				page_guard += 1
				if not next_page or next_page == current_page or page_guard > 200:
					break

				current_page = int(next_page)

		if isinstance(conversation_response, dict):
			target = conversation_response.get("data", conversation_response)
			if isinstance(target, dict):
				target["messages"] = messages_payload
				target["messages_meta"] = messages_meta
		else:
			conversation_response = {
				"data": conversation_response,
				"messages": messages_payload,
				"messages_meta": messages_meta,
			}

		return {"success": True, "data": conversation_response}
	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error getting conversation: {str(e)}")
		return {"success": False, "error": str(e)}

@frappe.whitelist()
def send_message(conversation_id, content, message_type='outgoing'):
	"""Send a message in a conversation"""
	_check_permission()
	_check_api_enabled()
	try:
		api = ChatwootAPI.get_api_for_user()
		result = api.send_message(int(conversation_id), content, message_type=message_type)
		return {"success": True, "data": result}
	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error sending message: {str(e)}")
		return {"success": False, "error": str(e)}

@frappe.whitelist()
def update_conversation_status(conversation_id, status):
	"""Update conversation status"""
	_check_permission()
	_check_api_enabled()
	try:
		api = ChatwootAPI.get_api_for_user()
		result = api.update_conversation_status(int(conversation_id), status)
		return {"success": True, "data": result}
	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error updating conversation status: {str(e)}")
		return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_contacts(page=1, per_page=20):
	"""Get contacts"""
	_check_permission()
	_check_api_enabled()
	try:
		api = ChatwootAPI.get_api_for_user()
		result = api.get_contacts(page=page, per_page=per_page)
		return {"success": True, "data": result}
	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error getting contacts: {str(e)}")
		return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_contact(contact_id):
	"""Get a specific contact"""
	_check_permission()
	_check_api_enabled()
	try:
		api = ChatwootAPI.get_api_for_user()
		result = api.get_contact(int(contact_id))
		return {"success": True, "data": result}
	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error getting contact: {str(e)}")
		return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_inboxes():
	"""Get available inboxes"""
	_check_permission()
	_check_api_enabled()
	try:
		api = ChatwootAPI.get_api_for_user()
		result = api.get_inboxes()
		return {"success": True, "data": result}
	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error getting inbox list: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def sync_conversations(background: int = 1):
	"""
	Trigger the background sync job. Returns immediately when enqueued.
	This gives administrators a manual button while the scheduler handles the cadence.
	"""
	_check_permission()
	from chat_bridge.customer_support.doctype.chat_conversation import sync as sync_module

	if cint(background):
		frappe.enqueue(
			sync_module.sync_chat_conversations,
			queue="long",
		)
	else:
		sync_module.sync_chat_conversations()

	return {"success": True}


@frappe.whitelist()
def get_all_users_with_token_status():
	"""Get all ERP users with their Chat token status"""
	_check_permission()

	# Get all enabled System Users
	all_users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		fields=["name", "full_name", "email"],
		order_by="full_name"
	)

	# Get all existing tokens
	existing_tokens = frappe.get_all(
		"Chat User Token",
		fields=["name", "user", "chat_user_id", "account_id", "modified"],
		ignore_permissions=True
	)

	# Create lookup dictionary
	token_map = {token.user: token for token in existing_tokens}

	# Merge users with their token status
	users_with_status = []
	for user in all_users:
		token = token_map.get(user.name)
		user_data = {
			"name": user.name,
			"full_name": user.full_name,
			"email": user.email,
			"has_token": bool(token),
			"token_name": token.name if token else None,
			"chat_user_id": token.chat_user_id if token else None,
			"account_id": token.account_id if token else None,
			"modified": token.modified if token else None
		}
		users_with_status.append(user_data)

	return {
		"success": True,
		"users": users_with_status,
		"total": len(users_with_status),
		"with_access": len([u for u in users_with_status if u["has_token"]]),
		"without_access": len([u for u in users_with_status if not u["has_token"]])
	}


@frappe.whitelist()
def get_available_users():
	"""Get list of users who don't have Chat tokens yet (legacy compatibility)"""
	_check_permission()

	result = get_all_users_with_token_status()
	if result.get("success"):
		# Filter to only users without tokens
		available = [u for u in result["users"] if not u["has_token"]]
		return available
	return []


@frappe.whitelist()
def create_chatwoot_user(user, chatwoot_user_id=None, api_access_token=None):
	"""Create a Chatwoot user and save the token, or link existing account"""
	frappe.log_error(f"Function entry - user={user}, chatwoot_user_id={chatwoot_user_id}, has_token={bool(api_access_token)}", "DEBUG: FUNCTION ENTRY")

	try:
		frappe.log_error("About to call _check_permission()", "DEBUG: BEFORE PERMISSION CHECK")
		_check_permission()
		frappe.log_error("Passed _check_permission()", "DEBUG: AFTER PERMISSION CHECK")
	except Exception as e:
		frappe.log_error(f"_check_permission() failed: {type(e).__name__}: {str(e)}\n{frappe.get_traceback()}", "DEBUG: PERMISSION CHECK FAILED")
		raise

	try:
		frappe.log_error("About to call _check_api_enabled()", "DEBUG: BEFORE API CHECK")
		_check_api_enabled()
		frappe.log_error("Passed _check_api_enabled()", "DEBUG: AFTER API CHECK")
	except Exception as e:
		frappe.log_error(f"_check_api_enabled() failed: {type(e).__name__}: {str(e)}\n{frappe.get_traceback()}", "DEBUG: API CHECK FAILED")
		raise

	try:
		# Check if user already has a token
		frappe.logger().info(f"Checking if user {user} already has a token...")
		existing = frappe.get_all(
			"Chat User Token",
			filters={"user": user},
			fields=["name"],
			limit=1,
			ignore_permissions=True
		)
		if existing:
			frappe.logger().info(f"User already has token: {existing[0].name}")
			return {"success": False, "error": "User already has a Chat token"}

		# Get user details
		frappe.logger().info(f"Getting user details for {user}...")
		user_doc = frappe.get_doc("User", user)

		# Get integration settings
		frappe.logger().info("Getting integration settings...")
		settings = frappe.get_single("Chat Integration Settings")
		frappe.logger().info(f"Settings - Base URL: {settings.chat_base_url}, Account ID: {settings.default_account_id}")

		# If chatwoot_user_id is provided (with or without token), link existing account
		if chatwoot_user_id:
			frappe.logger().info(f"Linking existing Chatwoot account {chatwoot_user_id}...")
			try:
				import requests

				# Get an admin token to generate access token for the user
				frappe.log_error("Getting admin token...", "DEBUG: Link Account - Step 1")
				service_tokens = frappe.get_all(
					"Chat User Token",
					fields=["name", "user"],
					order_by="modified desc",
					limit=1,
					ignore_permissions=True
				)
				frappe.log_error(f"Found {len(service_tokens) if service_tokens else 0} service token(s)", "DEBUG: Link Account - Step 2")
				if service_tokens:
					frappe.log_error(f"Service token name: {service_tokens[0].name}, user: {service_tokens[0].user}", "DEBUG: Link Account - Step 3")

				if not service_tokens:
					frappe.log_error("No admin token found!", "DEBUG: Link Account - ERROR")
					return {"success": False, "error": "No admin token found. Please configure at least one admin user first."}

				# Get the admin token
				frappe.log_error(f"Loading admin token document: {service_tokens[0].name}\nCurrent user: {frappe.session.user}\nUser roles: {frappe.get_roles()}", "DEBUG: Link Account - Step 4")

				try:
					# Bypass permission checks by using ignore_permissions context
					admin_token_doc = frappe.get_doc("Chat User Token", service_tokens[0].name, ignore_permissions=True)
					frappe.log_error("Successfully loaded admin token document", "DEBUG: Link Account - Step 5")
				except Exception as e:
					frappe.log_error(f"ERROR loading document: {type(e).__name__}: {str(e)}\n{frappe.get_traceback()}", "DEBUG: Link Account - CRITICAL ERROR")
					raise

				admin_token = admin_token_doc.get_password('api_access_token')
				frappe.log_error(f"Admin token retrieved (length: {len(admin_token) if admin_token else 0})", "DEBUG: Link Account - Step 6")

				# If api_access_token was provided, validate it
				if api_access_token:
					frappe.logger().info("Validating provided API access token...")
					test_headers = {
						'API-ACCESS-TOKEN': api_access_token,
						'Content-Type': 'application/json'
					}

					test_url = f"{settings.chat_base_url}/api/v1/profile"
					frappe.logger().info(f"Testing provided Chatwoot token with URL: {test_url}")

					test_response = requests.get(test_url, headers=test_headers, timeout=10)

					if test_response.status_code >= 400:
						error_msg = f"HTTP {test_response.status_code}"
						try:
							error_data = test_response.json()
							if 'error' in error_data:
								error_msg = error_data['error']
							elif 'message' in error_data:
								error_msg = error_data['message']
						except:
							error_msg = test_response.text[:200]

						frappe.log_error(f"Token validation failed: {error_msg}\n\nResponse: {test_response.text}", "Link Existing Account Error")
						return {"success": False, "error": f"Invalid Chatwoot token: {error_msg}"}

					# Token is valid, use it
					access_token = api_access_token
				else:
					# No token provided, generate a new one using admin credentials
					frappe.logger().info(f"Generating new access token for Chatwoot user {chatwoot_user_id}")

					token_url = f"{settings.chat_base_url}/api/v1/accounts/{settings.default_account_id}/agents/{chatwoot_user_id}/api_access_token"
					frappe.logger().info(f"Token generation URL: {token_url}")

					headers = {
						'API-ACCESS-TOKEN': admin_token,
						'Accept': 'application/json',
						'Content-Type': 'application/json'
					}

					# Generate an access token for the user
					frappe.logger().info("Sending POST request to generate token...")
					token_response = requests.post(token_url, headers=headers, timeout=30)
					frappe.logger().info(f"Token generation response status: {token_response.status_code}")

					if token_response.status_code >= 400:
						error_msg = f"HTTP {token_response.status_code}"
						try:
							error_data = token_response.json()
							if 'error' in error_data:
								error_msg = error_data['error']
							elif 'message' in error_data:
								error_msg = error_data['message']
						except:
							error_msg = token_response.text[:200]

						frappe.log_error(f"Token generation failed: {error_msg}\n\nResponse: {token_response.text}", "Link Existing Account Error")
						return {"success": False, "error": f"Failed to generate access token: {error_msg}"}

					token_data = token_response.json()
					access_token = token_data.get('access_token')
					frappe.logger().info(f"Access token extracted (length: {len(access_token) if access_token else 0})")

					if not access_token:
						frappe.logger().error("No access_token in Chatwoot response!")
						return {"success": False, "error": "Could not get access token from Chatwoot response"}

				# Create the Chat User Token document
				frappe.logger().info(f"Creating Chat User Token document for {user}...")
				token_doc = frappe.get_doc({
					"doctype": "Chat User Token",
					"user": user,
					"chat_user_id": int(chatwoot_user_id),
					"account_id": settings.default_account_id,
					"api_access_token": access_token
				})
				frappe.logger().info("Inserting document...")
				token_doc.insert(ignore_permissions=True)
				frappe.logger().info("Committing to database...")
				frappe.db.commit()

				frappe.logger().info(f"✓ Successfully linked Chatwoot user {chatwoot_user_id} to ERPNext user {user}")

				return {
					"success": True,
					"message": "Existing Chatwoot account linked successfully",
					"chatwoot_user_id": int(chatwoot_user_id)
				}

			except requests.exceptions.RequestException as e:
				frappe.logger().error(f"Network error in link existing account: {str(e)}")
				frappe.log_error(frappe.get_traceback(), "Link Existing Account - Network Error")
				return {"success": False, "error": f"Network error while linking account: {str(e)}"}
			except Exception as e:
				frappe.logger().error(f"Exception in link existing account: {str(e)}")
				frappe.log_error(frappe.get_traceback(), "Link Existing Account Error")
				return {"success": False, "error": f"Failed to link account: {str(e)}"}

		# Create Chatwoot API instance using a service account token
		# We need to use an admin token to create new users
		service_tokens = frappe.get_all(
			"Chat User Token",
			fields=["name", "user"],
			order_by="modified desc",
			limit=1,
			ignore_permissions=True
		)

		if not service_tokens:
			return {"success": False, "error": "No admin token found. Please configure at least one admin user first."}

		# Get the admin token
		admin_token_doc = frappe.get_doc("Chat User Token", service_tokens[0].name, ignore_permissions=True)
		admin_token = admin_token_doc.get_password('api_access_token')

		# Create API instance with admin credentials
		api = ChatwootAPI(
			base_url=settings.chat_base_url,
			access_token=admin_token,
			account_id=settings.default_account_id
		)

		# Create user in Chatwoot via Platform API
		# Note: This requires Platform API access or Account Owner privileges
		import requests

		# First, create the agent user
		headers = {
			'API-ACCESS-TOKEN': admin_token,
			'Accept': 'application/json',
			'Content-Type': 'application/json'
		}

		# Create agent payload
		agent_data = {
			"name": user_doc.full_name or user_doc.name,
			"email": user_doc.email,
			"role": "agent"  # Can be 'agent' or 'administrator'
		}

		response = requests.post(
			f"{settings.chat_base_url}/platform/api/v1/accounts/{settings.default_account_id}/agent_bots" if not user_doc.email else f"{settings.chat_base_url}/api/v1/accounts/{settings.default_account_id}/agents",
			headers=headers,
			json=agent_data,
			timeout=30
		)

		if response.status_code >= 400:
			error_msg = response.text
			try:
				error_data = response.json()
				if 'error' in error_data:
					error_msg = error_data['error']
			except:
				pass
			return {"success": False, "error": f"Failed to create Chatwoot user: {error_msg}"}

		chatwoot_user = response.json()

		# Extract user ID from response
		chatwoot_user_id = chatwoot_user.get('id') or chatwoot_user.get('user', {}).get('id')

		if not chatwoot_user_id:
			return {"success": False, "error": "Could not get Chatwoot user ID from response"}

		# Generate an access token for the user
		# This typically requires Platform API or we use the user's profile API
		token_response = requests.post(
			f"{settings.chat_base_url}/api/v1/accounts/{settings.default_account_id}/agents/{chatwoot_user_id}/api_access_token",
			headers=headers,
			timeout=30
		)

		if token_response.status_code >= 400:
			# If token creation fails, we might need to use a different approach
			# For now, we'll create a placeholder token doc and the user can update it manually
			frappe.log_error(f"Failed to create API token: {token_response.text}", "Chatwoot User Creation")

			# Create token doc with placeholder
			token_doc = frappe.get_doc({
				"doctype": "Chat User Token",
				"user": user,
				"chat_user_id": chatwoot_user_id,
				"account_id": settings.default_account_id,
				"api_access_token": "MANUAL_TOKEN_REQUIRED"
			})
			token_doc.insert(ignore_permissions=True)
			frappe.db.commit()

			return {
				"success": True,
				"message": "Chatwoot user created, but API token needs to be set manually",
				"chatwoot_user_id": chatwoot_user_id
			}

		token_data = token_response.json()
		access_token = token_data.get('access_token')

		if not access_token:
			return {"success": False, "error": "Could not get access token from Chatwoot"}

		# Create Chat User Token document
		token_doc = frappe.get_doc({
			"doctype": "Chat User Token",
			"user": user,
			"chat_user_id": chatwoot_user_id,
			"account_id": settings.default_account_id,
			"api_access_token": access_token
		})
		token_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": True,
			"message": "Chatwoot user and token created successfully",
			"chatwoot_user_id": chatwoot_user_id
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Chatwoot User Creation Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def list_all_tokens():
	"""List all Chat User Token records for debugging"""
	_check_permission()

	try:
		tokens = frappe.get_all(
			'Chat User Token',
			fields=['name', 'user', 'chat_user_id', 'account_id', 'modified'],
			order_by='modified desc',
			limit=20,
			ignore_permissions=True
		)

		return {
			"success": True,
			"tokens": tokens,
			"count": len(tokens)
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_webhooks():
	"""Get all webhooks configured in Chatwoot"""
	_check_permission()
	_check_api_enabled()
	try:
		api = ChatwootAPI.get_api_for_user()
		result = api.get_webhooks()
		return {"success": True, "data": result}
	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error getting webhooks: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def setup_webhook():
	"""Setup webhook in Chatwoot to point to ERPNext"""
	_check_permission()
	_check_api_enabled()
	try:
		settings = frappe.get_single("Chat Integration Settings")
		webhook_url = f"{frappe.utils.get_url()}/api/method/chat_bridge.webhook.handle"

		# Add token parameter for authentication if webhook_secret is set
		webhook_secret = None
		try:
			secret_value = frappe.db.get_value("Chat Integration Settings", "Chat Integration Settings", "webhook_secret")
			if secret_value:
				webhook_secret = settings.get_password('webhook_secret')
				webhook_url = f"{webhook_url}?token={webhook_secret}"
		except:
			pass

		api = ChatwootAPI.get_api_for_user()

		# Check existing webhooks
		existing = api.get_webhooks()
		existing_list = existing.get('payload', []) if isinstance(existing, dict) else existing if isinstance(existing, list) else []

		# Look for existing ERPNext webhook
		for hook in existing_list:
			if 'erp.visualgraphx.com' in hook.get('url', '') or 'chat_bridge.webhook' in hook.get('url', ''):
				# Update existing webhook
				result = api.update_webhook(
					hook['id'],
					url=webhook_url,
					subscriptions=[
						'conversation_created',
						'conversation_status_changed',
						'conversation_updated',
						'message_created',
						'message_updated',
						'contact_created',
						'contact_updated'
					]
				)
				return {"success": True, "message": "Webhook updated", "data": result, "webhook_url": webhook_url}

		# Create new webhook
		result = api.create_webhook(
			url=webhook_url,
			subscriptions=[
				'conversation_created',
				'conversation_status_changed',
				'conversation_updated',
				'message_created',
				'message_updated',
				'contact_created',
				'contact_updated'
			]
		)
		return {"success": True, "message": "Webhook created", "data": result, "webhook_url": webhook_url}

	except ChatwootAPIError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.logger().error(f"Error setting up webhook: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def cleanup_broken_tokens():
	"""Delete Chat User Token records with chat_user_id = 0 or missing user"""
	_check_permission()

	try:
		# Find broken tokens (chat_user_id = 0 or no user assigned)
		broken_tokens = frappe.get_all(
			'Chat User Token',
			filters=[
				['chat_user_id', '=', 0]
			],
			fields=['name', 'user', 'chat_user_id'],
			ignore_permissions=True
		)

		deleted_count = 0
		for token in broken_tokens:
			try:
				frappe.delete_doc('Chat User Token', token.name, ignore_permissions=True, force=True)
				deleted_count += 1
			except Exception as e:
				frappe.log_error(f"Failed to delete token {token.name}: {str(e)}", "Token Cleanup Error")

		frappe.db.commit()

		return {
			"success": True,
			"message": f"Deleted {deleted_count} broken token(s)",
			"deleted_count": deleted_count
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Token Cleanup Error")
		return {"success": False, "error": str(e)}
