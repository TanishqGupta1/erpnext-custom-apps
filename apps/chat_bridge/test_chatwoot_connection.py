#!/usr/bin/env python3
"""
Test Chatwoot API connection
"""
import frappe
import requests

def test_connection():
    """Test Chatwoot API connection and token generation"""

    # Get settings
    settings = frappe.get_single("Chat Integration Settings")
    print(f"Chatwoot Base URL: {settings.chat_base_url}")
    print(f"Default Account ID: {settings.default_account_id}")

    # Get an admin token
    token_record = frappe.get_all(
        "Chat User Token",
        fields=["name", "user", "chat_user_id"],
        order_by="modified desc",
        limit=1
    )

    if not token_record:
        print("ERROR: No admin token found!")
        return

    token_doc = frappe.get_doc("Chat User Token", token_record[0].name)
    admin_token = token_doc.get_password('api_access_token')

    print(f"\nAdmin Token User: {token_record[0].user}")
    print(f"Admin Chat User ID: {token_record[0].chat_user_id}")
    print(f"Token starts with: {admin_token[:20]}...")

    # Test 1: Get profile with admin token
    print("\n=== Test 1: Get Profile ===")
    headers = {
        'API-ACCESS-TOKEN': admin_token,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(
            f"{settings.chat_base_url}/api/v1/profile",
            headers=headers,
            timeout=10
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            profile = response.json()
            print(f"Profile: {profile.get('name')} (ID: {profile.get('id')})")
        else:
            print(f"Error: {response.text[:300]}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Try to generate token for Reena (user ID 3)
    print("\n=== Test 2: Generate Token for User ID 3 ===")
    try:
        token_response = requests.post(
            f"{settings.chat_base_url}/api/v1/accounts/{settings.default_account_id}/agents/3/api_access_token",
            headers=headers,
            timeout=30
        )

        print(f"Status: {token_response.status_code}")
        print(f"Response: {token_response.text[:500]}")

        if token_response.status_code == 200:
            token_data = token_response.json()
            print(f"\nSuccess! Generated token: {token_data.get('access_token', 'N/A')[:50]}...")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_connection()
