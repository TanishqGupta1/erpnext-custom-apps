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

def import_ops_faqs():
    """Import OnPrintShop FAQs from Qdrant export"""
    with open("/tmp/ops_faqs.json", "r") as f:
        data = json.load(f)
    
    points = data.get("result", {}).get("points", [])
    
    existing = set()
    for faq in frappe.get_all("Chatwoot FAQ", fields=["question"]):
        existing.add(faq.question.lower().strip() if faq.question else "")
    
    imported = 0
    for point in points:
        payload = point.get("payload", {})
        question = payload.get("question", "").strip()
        answer = payload.get("answer", "").strip()
        category = payload.get("category", "General")
        
        if not question or not answer:
            continue
        if question.lower() in existing:
            continue
        
        cat_name = get_or_create_category(f"OnPrintShop - {category}")
        faq = frappe.new_doc("Chatwoot FAQ")
        faq.question = question[:500]
        faq.answer = answer
        faq.category = cat_name
        faq.enabled = 1
        faq.priority = "3 - Normal"
        faq.tags = "onprintshop, imported"
        faq.sync_status = "Not Synced"
        faq.insert(ignore_permissions=True)
        existing.add(question.lower())
        imported += 1
    
    frappe.db.commit()
    return f"Imported {imported} OnPrintShop FAQs"

def import_vgx_knowledge():
    """Import VisualGraphX knowledge from Qdrant export"""
    with open("/tmp/vgx_data.json", "r") as f:
        data = json.load(f)
    
    points = data.get("result", {}).get("points", [])
    
    existing = set()
    for faq in frappe.get_all("Chatwoot FAQ", fields=["question"]):
        existing.add(faq.question.lower().strip() if faq.question else "")
    
    question_map = {
        "contact": "What are Visual GraphX contact details?",
        "equipment": "What equipment does Visual GraphX use?",
        "services": "What services does Visual GraphX offer?",
        "system": "What systems does Visual GraphX use?",
        "policy": "What are Visual GraphX policies?",
        "materials": "What materials does Visual GraphX use?",
        "turnaround": "What are Visual GraphX turnaround times?",
        "products": "What products does Visual GraphX offer?",
        "company_overview": "What is Visual GraphX company overview?"
    }
    
    imported = 0
    for point in points:
        payload = point.get("payload", {})
        text = payload.get("text", "").strip()
        vgx_type = payload.get("type", "general")
        
        if not text:
            continue
        
        question = question_map.get(vgx_type, f"Visual GraphX {vgx_type} information")
        
        if question.lower() in existing:
            continue
        
        cat_name = get_or_create_category("Company Information")
        faq = frappe.new_doc("Chatwoot FAQ")
        faq.question = question
        faq.answer = text
        faq.category = cat_name
        faq.enabled = 1
        faq.priority = "2 - High"
        faq.tags = "visualgraphx, company, imported"
        faq.sync_status = "Not Synced"
        faq.insert(ignore_permissions=True)
        existing.add(question.lower())
        imported += 1
    
    frappe.db.commit()
    return f"Imported {imported} VisualGraphX knowledge items"

def import_products():
    """Import product info from Qdrant export"""
    with open("/tmp/products.json", "r") as f:
        data = json.load(f)
    
    points = data.get("result", {}).get("points", [])
    
    existing = set()
    for faq in frappe.get_all("Chatwoot FAQ", fields=["question"]):
        existing.add(faq.question.lower().strip() if faq.question else "")
    
    imported = 0
    for point in points:
        payload = point.get("payload", {})
        product_name = payload.get("product_name", "").strip()
        text = payload.get("text", "").strip()
        
        if not product_name or not text:
            continue
        
        question = f"What is {product_name}?"
        
        if question.lower() in existing:
            continue
        
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        cat_name = get_or_create_category("Products")
        faq = frappe.new_doc("Chatwoot FAQ")
        faq.question = question[:500]
        faq.answer = text
        faq.category = cat_name
        faq.enabled = 1
        faq.priority = "3 - Normal"
        faq.tags = "product, imported"
        faq.sync_status = "Not Synced"
        faq.insert(ignore_permissions=True)
        existing.add(question.lower())
        imported += 1
    
    frappe.db.commit()
    return f"Imported {imported} product FAQs"
