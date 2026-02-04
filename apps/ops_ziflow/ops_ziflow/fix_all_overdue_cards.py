# fix_all_overdue_cards.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.fix_all_overdue_cards.fix_cards

import frappe
from frappe.utils import today
import json

def fix_cards():
    """Fix all Number Cards with 'Today' string in filters"""

    # Find all cards with "Today" in filters
    cards = frappe.get_all('Number Card',
        filters=[['filters_json', 'like', '%"Today"%']],
        fields=['name', 'filters_json']
    )

    print(f"Found {len(cards)} cards with 'Today' filter issue")

    for card_info in cards:
        card_name = card_info.name
        print(f"\nFixing: {card_name}")
        print(f"  Old: {card_info.filters_json}")

        card = frappe.get_doc('Number Card', card_name)

        # Parse and fix filters
        try:
            filters = json.loads(card.filters_json)
            new_filters = []

            for f in filters:
                if len(f) >= 4 and f[3] == "Today":
                    # Replace "Today" with actual date
                    f[3] = today()
                new_filters.append(f)

            card.filters_json = json.dumps(new_filters)
            card.save(ignore_permissions=True)
            print(f"  New: {card.filters_json}")

        except Exception as e:
            print(f"  Error: {e}")

    frappe.db.commit()
    print("\nDone!")


if __name__ == "__main__":
    fix_cards()
