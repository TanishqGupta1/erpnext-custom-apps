# create_quote_charts.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.create_quote_charts.create_charts

import frappe
import json

def create_charts():
    """Create charts for OPS Quote visualization"""

    charts_to_create = [
        {
            "name": "Quote Status Distribution",
            "chart_name": "Quote Status Distribution",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Count",
            "group_by_based_on": "quote_status",
            "type": "Donut",
            "filters_json": "[]",
            "is_public": 1,
            "is_standard": 0
        },
        {
            "name": "Quotes by Month",
            "chart_name": "Quotes by Month",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Count",
            "group_by_based_on": "quote_date",
            "group_by_timespan": "Monthly",
            "type": "Line",
            "filters_json": "[]",
            "is_public": 1,
            "is_standard": 0,
            "timespan": "Last Year"
        },
        {
            "name": "Quote Value by Status",
            "chart_name": "Quote Value by Status",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Sum",
            "group_by_based_on": "quote_status",
            "aggregate_function_based_on": "quote_price",
            "type": "Bar",
            "filters_json": "[]",
            "is_public": 1,
            "is_standard": 0
        },
        {
            "name": "Monthly Quote Revenue",
            "chart_name": "Monthly Quote Revenue",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Sum",
            "group_by_based_on": "quote_date",
            "group_by_timespan": "Monthly",
            "aggregate_function_based_on": "quote_price",
            "type": "Bar",
            "filters_json": "[]",
            "is_public": 1,
            "is_standard": 0,
            "timespan": "Last Year"
        },
        {
            "name": "Monthly Profit Trend",
            "chart_name": "Monthly Profit Trend",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Sum",
            "group_by_based_on": "quote_date",
            "group_by_timespan": "Monthly",
            "aggregate_function_based_on": "profit_margin",
            "type": "Line",
            "filters_json": "[]",
            "is_public": 1,
            "is_standard": 0,
            "timespan": "Last Year"
        }
    ]

    created_charts = []

    for chart_data in charts_to_create:
        chart_name = chart_data["name"]

        if frappe.db.exists("Dashboard Chart", chart_name):
            print(f"Chart '{chart_name}' already exists, updating...")
            chart = frappe.get_doc("Dashboard Chart", chart_name)
            for key, value in chart_data.items():
                if key != "name":
                    setattr(chart, key, value)
            chart.save(ignore_permissions=True)
        else:
            print(f"Creating chart: {chart_name}")
            chart = frappe.get_doc({
                "doctype": "Dashboard Chart",
                **chart_data
            })
            chart.insert(ignore_permissions=True)

        created_charts.append(chart_name)

    frappe.db.commit()
    print(f"\nCreated/updated {len(created_charts)} charts")

    return created_charts


def add_charts_to_workspace():
    """Add the charts to OPS Dashboard workspace"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    # Parse existing content
    content = json.loads(workspace.content) if workspace.content else []

    # Find the OPS Quotes header index
    quotes_header_index = None
    for i, item in enumerate(content):
        if item.get('type') == 'header' and 'Quote' in str(item.get('data', {}).get('text', '')):
            quotes_header_index = i
            break

    if quotes_header_index is None:
        print("OPS Quotes header not found, adding at end")
        quotes_header_index = len(content)

    # Check which charts are already in workspace
    existing_charts = [
        item.get('data', {}).get('chart_name')
        for item in content
        if item.get('type') == 'chart'
    ]

    charts_to_add = [
        "Quote Status Distribution",
        "Quotes by Month",
        "Quote Value by Status",
        "Monthly Quote Revenue",
        "Monthly Profit Trend"
    ]

    # Find insert position (after the number cards in OPS Quotes section)
    insert_index = quotes_header_index + 1
    for i in range(quotes_header_index + 1, len(content)):
        item = content[i]
        if item.get('type') == 'header':
            # Next section started
            insert_index = i
            break
        elif item.get('type') in ['number_card', 'shortcut']:
            insert_index = i + 1

    # Add charts section header if not exists
    has_chart_header = False
    for item in content:
        if item.get('type') == 'header' and 'Chart' in str(item.get('data', {}).get('text', '')):
            has_chart_header = True
            break

    items_to_insert = []

    if not has_chart_header:
        items_to_insert.append({
            'type': 'spacer',
            'data': {'height': 15}
        })
        items_to_insert.append({
            'type': 'header',
            'data': {
                'text': 'Quote Analytics',
                'level': 4,
                'col': 12
            }
        })

    # Add charts (2 per row with col: 6)
    for chart_name in charts_to_add:
        if chart_name not in existing_charts:
            items_to_insert.append({
                'type': 'chart',
                'data': {
                    'chart_name': chart_name,
                    'col': 6
                }
            })
            print(f"Adding chart: {chart_name}")

    # Insert items at the right position
    for i, item in enumerate(items_to_insert):
        content.insert(insert_index + i, item)

    workspace.content = json.dumps(content)
    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"\nAdded {len(items_to_insert)} items to workspace")


def setup():
    """Main setup function"""
    print("=== Creating OPS Quote Charts ===\n")
    create_charts()
    print("\n=== Adding Charts to Dashboard ===\n")
    add_charts_to_workspace()
    print("\nDone!")


if __name__ == "__main__":
    setup()
