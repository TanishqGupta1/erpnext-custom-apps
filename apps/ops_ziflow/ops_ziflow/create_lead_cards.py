# create_lead_cards.py
# Run with: bench --site erp.visualgraphx.com execute create_lead_cards.create_cards

import frappe

def create_cards():
    """Create Chatwoot Lead number cards."""

    cards_to_create = [
        {
            "name": "Total Chatwoot Leads",
            "label": "Total Leads",
            "document_type": "Chatwoot Lead",
            "function": "Count",
            "color": "#667eea",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly",
        },
        {
            "name": "New Chatwoot Leads",
            "label": "New Leads",
            "document_type": "Chatwoot Lead",
            "function": "Count",
            "color": "#f6ad55",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily",
            "filters_json": '[["Chatwoot Lead","status","=","New"]]',
        },
    ]

    for card_def in cards_to_create:
        name = card_def["name"]
        if frappe.db.exists("Number Card", name):
            print(f"Card already exists: {name}")
        else:
            try:
                card = frappe.get_doc({"doctype": "Number Card", **card_def})
                card.insert(ignore_permissions=True)
                frappe.db.commit()
                print(f"Created card: {name}")
            except Exception as e:
                print(f"Error creating {name}: {e}")

    print("Done creating cards")
