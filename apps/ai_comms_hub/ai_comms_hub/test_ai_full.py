"""
Test script for AI Engine - run via bench execute
"""
import frappe
from datetime import datetime
import json

def run_test():
    """Full AI Engine test"""
    print("\n=== AI Communications Hub - Full Test ===\n")

    # 1. Test helper functions
    print("1. Testing Helper Functions...")
    from ai_comms_hub.api.ai_engine import should_escalate, is_important_question, format_for_platform

    test_cases = [
        ("I want to speak to a human", True, False),
        ("What is your return policy?", False, True),
        ("I want a refund!", True, True),
        ("Hello there!", False, False),
        ("This is terrible service!", True, False),
    ]

    for msg, expected_escalate, expected_important in test_cases:
        escalate = should_escalate(msg)
        important = is_important_question(msg)
        status = "PASS" if escalate == expected_escalate and important == expected_important else "FAIL"
        print(f"  [{status}] '{msg[:30]}...' -> Escalate: {escalate}, Important: {important}")

    # 2. Test platform formatting
    print("\n2. Testing Platform Formatting...")
    test_content = "Hello! This is a **bold** message with #hashtags and some special chars. " * 3

    for platform in ["Voice", "SMS", "Twitter", "WhatsApp", "Email"]:
        formatted = format_for_platform(test_content, platform)
        print(f"  {platform}: {len(formatted)} chars - '{formatted[:50]}...'")

    # 3. Test LLM connection
    print("\n3. Testing LLM Connection...")
    try:
        from ai_comms_hub.api.llm import get_llm_settings, generate_completion
        settings = get_llm_settings()
        print(f"  API URL: {settings['api_url']}")
        print(f"  Model: {settings['model']}")
        print(f"  API Key: {'****' + settings['api_key'][-4:] if settings['api_key'] else 'NOT SET'}")

        # Quick test completion
        response = generate_completion([
            {"role": "user", "content": "Say 'Hello, AI test successful!' in exactly those words."}
        ], max_tokens=20)
        content = response["choices"][0]["message"]["content"]
        print(f"  LLM Response: {content}")
    except Exception as e:
        print(f"  LLM Error: {str(e)}")

    # 4. Test RAG (if configured)
    print("\n4. Testing RAG Knowledge Base...")
    try:
        from ai_comms_hub.api.rag import query_knowledge_base
        results = query_knowledge_base("return policy", top_k=2)
        if results:
            print(f"  Found {len(results)} results")
            for r in results[:2]:
                print(f"    - {r.get('title', 'No title')}: score {r.get('score', 0):.2f}")
        else:
            print("  No results (knowledge base may be empty)")
    except Exception as e:
        print(f"  RAG Error: {str(e)}")

    # 5. Check existing hubs
    print("\n5. Checking Existing Communication Hubs...")
    hubs = frappe.get_all(
        "Communication Hub",
        fields=["name", "channel", "status", "ai_mode", "customer_name"],
        limit=5
    )
    if hubs:
        for hub in hubs:
            print(f"  - {hub.name}: {hub.channel} | {hub.status} | {hub.ai_mode}")
    else:
        print("  No hubs found")

    # 6. Create test hub and message
    print("\n6. Creating Test Hub and Message...")
    try:
        # Create test hub
        hub = frappe.get_doc({
            "doctype": "Communication Hub",
            "channel": "Chat",
            "status": "Open",
            "ai_mode": "Autonomous",
            "subject": "AI Engine Test Conversation"
        })
        hub.insert()
        print(f"  Created hub: {hub.name}")

        # Create test message
        msg = frappe.get_doc({
            "doctype": "Communication Message",
            "communication_hub": hub.name,
            "sender_type": "Customer",
            "sender_name": "Test Customer",
            "content": "What products do you offer?",
            "timestamp": datetime.now()
        })
        msg.insert()
        print(f"  Created message: {msg.name}")

        frappe.db.commit()

        # Test AI response generation
        print("\n7. Testing AI Response Generation...")
        from ai_comms_hub.api.ai_engine import generate_response
        result = generate_response(hub.name, msg.name)

        if result and result.get("success"):
            print(f"  SUCCESS! AI Message: {result.get('message_id')}")
            print(f"  Response: {result.get('content', '')[:200]}...")
        elif result and result.get("escalated"):
            print(f"  Escalated: {result.get('reason')}")
        else:
            print(f"  Failed: {result}")

        # Cleanup
        print("\n8. Cleaning up test data...")
        frappe.delete_doc("Communication Message", msg.name, force=True)
        # Get any AI messages created
        ai_msgs = frappe.get_all("Communication Message", filters={"communication_hub": hub.name})
        for ai_msg in ai_msgs:
            frappe.delete_doc("Communication Message", ai_msg.name, force=True)
        frappe.delete_doc("Communication Hub", hub.name, force=True)
        frappe.db.commit()
        print("  Cleanup complete")

    except Exception as e:
        print(f"  Error: {str(e)}")
        frappe.db.rollback()

    print("\n=== Test Complete ===\n")
    return "Test completed"
