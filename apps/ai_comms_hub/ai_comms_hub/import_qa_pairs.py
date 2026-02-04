import frappe
import json

def get_or_create_category(cat_name):
    if not cat_name:
        cat_name = "General"
    cat_name = cat_name.strip()[:140]
    if not frappe.db.exists("Chatwoot FAQ Category", cat_name):
        cat = frappe.new_doc("Chatwoot FAQ Category")
        cat.category_name = cat_name
        cat.insert(ignore_permissions=True)
        frappe.db.commit()
    return cat_name

def import_qa_pairs():
    """Import Q&A pairs from Qdrant conversation history"""
    with open("/tmp/qa_pairs.json", "r") as f:
        qa_pairs = json.load(f)
    
    existing = set()
    for faq in frappe.get_all("Chatwoot FAQ", fields=["question"]):
        existing.add(faq.question.lower().strip()[:50] if faq.question else "")
    
    cat_name = get_or_create_category("Customer Conversations")
    
    imported = 0
    duplicates = 0
    
    for qa in qa_pairs:
        question = qa.get("question", "").strip()
        answer = qa.get("answer", "").strip()
        
        if not question or not answer:
            continue
        
        # Skip if question is too short or already exists
        if len(question) < 10:
            continue
        
        # Check for duplicates using first 50 chars
        if question.lower()[:50] in existing:
            duplicates += 1
            continue
        
        # Clean up the answer (remove markdown artifacts)
        answer = answer.replace("**", "").replace("✅", "").replace("❌", "")
        
        try:
            faq = frappe.new_doc("Chatwoot FAQ")
            faq.question = question[:500]
            faq.answer = answer[:10000]
            faq.category = cat_name
            faq.enabled = 1
            faq.priority = "4 - Low"  # Lower priority for conversation-based FAQs
            faq.tags = "conversation, imported, chatwoot"
            faq.sync_status = "Not Synced"
            faq.insert(ignore_permissions=True)
            existing.add(question.lower()[:50])
            imported += 1
        except Exception as e:
            pass
    
    frappe.db.commit()
    return f"Imported {imported} Q&A pairs, skipped {duplicates} duplicates"
