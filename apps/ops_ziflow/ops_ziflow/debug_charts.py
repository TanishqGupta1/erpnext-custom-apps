# debug_charts.py
import frappe
import json

def debug():
    """Debug charts on dashboard"""

    # Check if charts exist
    print("=== Dashboard Charts ===")
    charts = frappe.get_all('Dashboard Chart',
        filters={'document_type': 'OPS Quote'},
        fields=['name', 'chart_type', 'type', 'is_public']
    )
    for c in charts:
        print(f"  - {c.name} ({c.type}, public: {c.is_public})")

    # Check workspace content
    print("\n=== Workspace Content ===")
    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    if workspace.content:
        content = json.loads(workspace.content)
        print(f"Total items: {len(content)}")

        for i, item in enumerate(content):
            item_type = item.get('type')
            data = item.get('data', {})
            if item_type == 'chart':
                print(f"  [{i}] CHART: {data.get('chart_name')} (col: {data.get('col')})")
            elif item_type == 'header':
                print(f"  [{i}] HEADER: {data.get('text')}")
            elif item_type == 'number_card':
                print(f"  [{i}] NUMBER_CARD: {data.get('number_card_name')}")

    # Check workspace charts child table
    print("\n=== Workspace Charts Child Table ===")
    print(f"Charts in child table: {len(workspace.charts or [])}")
    for c in (workspace.charts or []):
        print(f"  - {c.chart_name}")

if __name__ == "__main__":
    debug()
