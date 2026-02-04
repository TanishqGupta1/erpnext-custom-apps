#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Integration Testing Script

This script tests all external integrations for AI Communications Hub:
- LLM (naga.ac)
- Eleven Labs (Voice AI)
- Qdrant (Vector Database)
- Social Media APIs
- SendGrid (Email)
- Chatwoot (Chat)
- Twilio (SMS/WhatsApp)

Usage:
    bench --site <site-name> execute ai_comms_hub.scripts.test_integrations.test_<function>

    # Or run all tests
    bench --site <site-name> execute ai_comms_hub.scripts.test_integrations.run_all_tests
"""

import frappe
from frappe import _
import requests
import json
from datetime import datetime


def run_all_tests():
	"""
	Run all integration tests.
	"""
	print("=" * 60)
	print("AI Communications Hub - Integration Tests")
	print("=" * 60)

	tests = [
		("LLM Connection", test_llm_connection),
		("Qdrant Connection", test_qdrant_connection),
		("Eleven Labs Connection", test_elevenlabs_connection),
		("SendGrid Connection", test_sendgrid_connection),
		("Chatwoot Connection", test_chatwoot_connection),
		("Twilio Connection", test_twilio_connection),
		("Facebook API", test_facebook_api),
		("Instagram API", test_instagram_api),
		("Twitter API", test_twitter_api)
	]

	results = {}

	for test_name, test_func in tests:
		print(f"\n[Testing {test_name}]")
		try:
			success, message = test_func()
			results[test_name] = {
				"success": success,
				"message": message
			}

			if success:
				print(f"✅ {test_name}: PASSED")
				print(f"   {message}")
			else:
				print(f"❌ {test_name}: FAILED")
				print(f"   {message}")

		except Exception as e:
			results[test_name] = {
				"success": False,
				"message": str(e)
			}
			print(f"❌ {test_name}: ERROR")
			print(f"   {str(e)}")

	# Summary
	print("\n" + "=" * 60)
	print("Test Summary")
	print("=" * 60)

	passed = sum(1 for r in results.values() if r["success"])
	failed = len(results) - passed

	print(f"\nTotal Tests: {len(results)}")
	print(f"✅ Passed: {passed}")
	print(f"❌ Failed: {failed}")

	if failed == 0:
		print("\n🎉 All tests passed!")
	else:
		print(f"\n⚠️  {failed} test(s) failed. Check configuration.")

	return results


def test_llm_connection():
	"""
	Test LLM (naga.ac) connection and API.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		from ai_comms_hub.api.llm import get_llm_settings, generate_completion

		settings = get_llm_settings()

		# Test simple completion
		messages = [
			{"role": "user", "content": "Say 'test successful' if you can read this"}
		]

		response = generate_completion(messages, max_tokens=50, temperature=0)

		if response and "test successful" in response.lower():
			return (True, f"LLM API working. Model: {settings['model']}")
		else:
			return (False, f"LLM responded but unexpected output: {response}")

	except Exception as e:
		return (False, f"LLM connection failed: {str(e)}")


def test_qdrant_connection():
	"""
	Test Qdrant vector database connection.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		from ai_comms_hub.api.rag import get_qdrant_settings

		settings = get_qdrant_settings()

		# Test connection
		response = requests.get(f"{settings['url']}/collections", timeout=5)
		response.raise_for_status()

		collections = response.json().get("result", {}).get("collections", [])
		collection_names = [c.get("name") for c in collections]

		if settings["collection"] in collection_names:
			# Get collection info
			response = requests.get(
				f"{settings['url']}/collections/{settings['collection']}",
				timeout=5
			)
			info = response.json().get("result", {})
			vector_count = info.get("vectors_count", 0)

			return (True, f"Qdrant connected. Collection '{settings['collection']}' has {vector_count:,} vectors")
		else:
			return (False, f"Collection '{settings['collection']}' not found. Run setup_qdrant.py")

	except Exception as e:
		return (False, f"Qdrant connection failed: {str(e)}")


def test_elevenlabs_connection():
	"""
	Test Eleven Labs (Voice AI) connection.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		settings = frappe.get_single("AI Communications Hub Settings")

		if not settings.elevenlabs_api_key:
			return (False, "Eleven Labs API key not configured")

		# Test Eleven Labs API
		headers = {
			"xi-api-key": settings.elevenlabs_api_key,
			"Content-Type": "application/json"
		}

		response = requests.get(
			"https://api.elevenlabs.io/v1/convai/agents",
			headers=headers,
			timeout=10
		)

		if response.status_code == 200:
			agents = response.json().get("agents", [])
			return (True, f"Eleven Labs connected. {len(agents)} agent(s) configured")
		else:
			return (False, f"Eleven Labs API error: {response.status_code}")

	except Exception as e:
		return (False, f"Eleven Labs connection failed: {str(e)}")


def test_sendgrid_connection():
	"""
	Test SendGrid email service connection.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		settings = frappe.get_single("AI Communications Hub Settings")

		if not settings.sendgrid_api_key:
			return (False, "SendGrid API key not configured")

		# Test SendGrid API
		headers = {
			"Authorization": f"Bearer {settings.sendgrid_api_key}",
			"Content-Type": "application/json"
		}

		response = requests.get(
			"https://api.sendgrid.com/v3/user/account",
			headers=headers,
			timeout=10
		)

		if response.status_code == 200:
			account = response.json()
			return (True, f"SendGrid connected. Account: {account.get('username', 'Unknown')}")
		else:
			return (False, f"SendGrid API error: {response.status_code}")

	except Exception as e:
		return (False, f"SendGrid connection failed: {str(e)}")


def test_chatwoot_connection():
	"""
	Test Chatwoot live chat connection.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		settings = frappe.get_single("AI Communications Hub Settings")

		if not settings.chatwoot_api_key or not settings.chatwoot_account_id:
			return (False, "Chatwoot credentials not configured")

		# Test Chatwoot API
		headers = {"api_access_token": settings.chatwoot_api_key}

		response = requests.get(
			f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/inboxes",
			headers=headers,
			timeout=10
		)

		if response.status_code == 200:
			inboxes = response.json().get("payload", [])
			return (True, f"Chatwoot connected. {len(inboxes)} inbox(es) configured")
		else:
			return (False, f"Chatwoot API error: {response.status_code}")

	except Exception as e:
		return (False, f"Chatwoot connection failed: {str(e)}")


def test_twilio_connection():
	"""
	Test Twilio SMS/WhatsApp connection.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		settings = frappe.get_single("AI Communications Hub Settings")

		if not settings.twilio_account_sid or not settings.twilio_auth_token:
			return (False, "Twilio credentials not configured")

		# Test Twilio API
		from requests.auth import HTTPBasicAuth

		auth = HTTPBasicAuth(settings.twilio_account_sid, settings.twilio_auth_token)

		response = requests.get(
			f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}.json",
			auth=auth,
			timeout=10
		)

		if response.status_code == 200:
			account = response.json()
			return (True, f"Twilio connected. Account: {account.get('friendly_name', 'Unknown')}")
		else:
			return (False, f"Twilio API error: {response.status_code}")

	except Exception as e:
		return (False, f"Twilio connection failed: {str(e)}")


def test_facebook_api():
	"""
	Test Facebook Messenger API.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		settings = frappe.get_single("AI Communications Hub Settings")

		if not settings.facebook_access_token:
			return (False, "Facebook access token not configured")

		# Test Facebook Graph API
		response = requests.get(
			"https://graph.facebook.com/v18.0/me",
			params={"access_token": settings.facebook_access_token},
			timeout=10
		)

		if response.status_code == 200:
			page = response.json()
			return (True, f"Facebook connected. Page: {page.get('name', 'Unknown')}")
		else:
			return (False, f"Facebook API error: {response.status_code}")

	except Exception as e:
		return (False, f"Facebook connection failed: {str(e)}")


def test_instagram_api():
	"""
	Test Instagram DMs API.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		settings = frappe.get_single("AI Communications Hub Settings")

		if not settings.instagram_access_token:
			return (False, "Instagram access token not configured")

		# Test Instagram Graph API
		response = requests.get(
			"https://graph.facebook.com/v18.0/me",
			params={"access_token": settings.instagram_access_token},
			timeout=10
		)

		if response.status_code == 200:
			account = response.json()
			return (True, f"Instagram connected. Account: {account.get('username', 'Unknown')}")
		else:
			return (False, f"Instagram API error: {response.status_code}")

	except Exception as e:
		return (False, f"Instagram connection failed: {str(e)}")


def test_twitter_api():
	"""
	Test Twitter/X API.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		settings = frappe.get_single("AI Communications Hub Settings")

		if not settings.twitter_bearer_token:
			return (False, "Twitter bearer token not configured")

		# Test Twitter API v2
		headers = {"Authorization": f"Bearer {settings.twitter_bearer_token}"}

		response = requests.get(
			"https://api.twitter.com/2/users/me",
			headers=headers,
			timeout=10
		)

		if response.status_code == 200:
			user = response.json().get("data", {})
			return (True, f"Twitter connected. User: @{user.get('username', 'Unknown')}")
		else:
			return (False, f"Twitter API error: {response.status_code}")

	except Exception as e:
		return (False, f"Twitter connection failed: {str(e)}")


def test_function_calling():
	"""
	Test AI function calling with a sample function.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		from ai_comms_hub.api.functions import get_order_status

		# Test with a dummy order
		result = get_order_status("TEST-ORDER-001")

		if result and "error" not in result:
			return (True, "Function calling tested successfully")
		else:
			return (False, f"Function calling failed: {result.get('error', 'Unknown error')}")

	except Exception as e:
		return (False, f"Function calling test failed: {str(e)}")


def test_rag_search():
	"""
	Test RAG (Retrieval-Augmented Generation) search.

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		from ai_comms_hub.api.rag import query_knowledge_base

		# Test search
		results = query_knowledge_base("test product", top_k=1)

		if results:
			return (True, f"RAG search working. Found {len(results)} result(s)")
		else:
			return (False, "RAG search returned no results. Knowledge base may be empty.")

	except Exception as e:
		return (False, f"RAG search failed: {str(e)}")


def test_message_delivery():
	"""
	Test message delivery system (without actually sending).

	Returns:
		tuple: (success: bool, message: str)
	"""
	try:
		# Just test that the module can be imported
		from ai_comms_hub.api.message import deliver_message

		return (True, "Message delivery module loaded successfully")

	except Exception as e:
		return (False, f"Message delivery test failed: {str(e)}")


# CLI interface

def main():
	"""Main test interface."""
	print("=" * 60)
	print("AI Communications Hub - Integration Tests")
	print("=" * 60)
	print("\nAvailable tests:")
	print("1. Test LLM connection")
	print("2. Test Qdrant connection")
	print("3. Test Eleven Labs connection")
	print("4. Test SendGrid connection")
	print("5. Test Chatwoot connection")
	print("6. Test Twilio connection")
	print("7. Test Facebook API")
	print("8. Test Instagram API")
	print("9. Test Twitter API")
	print("10. Run all tests")
	print("\n0. Exit")

	choice = input("\nSelect test (0-10): ")

	tests = {
		"1": test_llm_connection,
		"2": test_qdrant_connection,
		"3": test_elevenlabs_connection,
		"4": test_sendgrid_connection,
		"5": test_chatwoot_connection,
		"6": test_twilio_connection,
		"7": test_facebook_api,
		"8": test_instagram_api,
		"9": test_twitter_api,
		"10": run_all_tests
	}

	if choice in tests:
		if choice == "10":
			run_all_tests()
		else:
			success, message = tests[choice]()
			if success:
				print(f"\n✅ Test PASSED")
				print(f"   {message}")
			else:
				print(f"\n❌ Test FAILED")
				print(f"   {message}")
	else:
		print("Exiting...")


if __name__ == "__main__":
	main()
