# fix_chart_layout.py
import frappe
import json

def fix():
    """Fix chart layout - remove duplicates, add spacing, enable legends"""

    print("=== Fixing Chart Layout ===\n")

    # 1. Update charts with proper legend settings
    charts_to_update = [
        {
            "name": "Quote Status Distribution",
            "custom_options": json.dumps({
                "colors": ["#5e64ff", "#ecad4b", "#36a2eb", "#4bc0c0", "#ff6384", "#9966ff"],
                "height": 300,
                "maxSlices": 10,
                "legend": {
                    "position": "right"
                }
            })
        },
        {
            "name": "Top Quote Values",
            "custom_options": json.dumps({
                "colors": ["#5e64ff", "#ecad4b", "#36a2eb", "#4bc0c0", "#ff6384", "#9966ff"],
                "height": 300,
                "maxSlices": 10,
                "legend": {
                    "position": "right"
                }
            })
        },
        {
            "name": "Quotes by Month",
            "custom_options": json.dumps({
                "colors": ["#5e64ff"],
                "height": 280,
                "barOptions": {
                    "spaceRatio": 0.5
                },
                "axisOptions": {
                    "xAxisMode": "tick",
                    "shortenYAxisNumbers": 1
                }
            })
        },
        {
            "name": "Monthly Quote Revenue",
            "custom_options": json.dumps({
                "colors": ["#4bc0c0"],
                "height": 280,
                "barOptions": {
                    "spaceRatio": 0.5
                },
                "axisOptions": {
                    "xAxisMode": "tick",
                    "shortenYAxisNumbers": 1
                }
            })
        },
        {
            "name": "Monthly Profit Trend",
            "custom_options": json.dumps({
                "colors": ["#ff6384"],
                "height": 280,
                "lineOptions": {
                    "regionFill": 1,
                    "hideDots": 0,
                    "dotSize": 4
                },
                "axisOptions": {
                    "xAxisMode": "tick",
                    "shortenYAxisNumbers": 1
                }
            })
        },
        {
            "name": "Conversion Rate Trend",
            "custom_options": json.dumps({
                "colors": ["#36a2eb"],
                "height": 280,
                "lineOptions": {
                    "regionFill": 1,
                    "hideDots": 0,
                    "dotSize": 4
                },
                "axisOptions": {
                    "xAxisMode": "tick",
                    "shortenYAxisNumbers": 1
                }
            })
        }
    ]

    for config in charts_to_update:
        if frappe.db.exists("Dashboard Chart", config["name"]):
            chart = frappe.get_doc("Dashboard Chart", config["name"])
            chart.custom_options = config["custom_options"]
            chart.save(ignore_permissions=True)
            print(f"Updated: {config['name']}")

    # 2. Delete duplicate "Quote Value by Status" if exists and recreate properly
    if frappe.db.exists("Dashboard Chart", "Quote Value by Status"):
        frappe.delete_doc("Dashboard Chart", "Quote Value by Status", force=True)
        print("Deleted duplicate: Quote Value by Status")

    frappe.db.commit()

    # 3. Update workspace content with proper spacing
    update_workspace_layout()


def update_workspace_layout():
    """Update workspace with proper spacing between charts"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    # Parse existing content
    content = json.loads(workspace.content) if workspace.content else []

    # Remove all chart-related items
    content = [item for item in content if not (
        item.get('type') == 'chart' or
        (item.get('type') == 'header' and 'Analytics' in str(item.get('data', {}).get('text', ''))) or
        (item.get('type') == 'spacer' and content.index(item) > 25)
    )]

    # Find end of OPS Quotes number cards section
    insert_index = len(content)
    for i, item in enumerate(content):
        if item.get('type') == 'number_card' and 'Profit' in str(item.get('data', {}).get('number_card_name', '')):
            insert_index = i + 1
            break

    # Build new chart section with proper spacing
    new_items = [
        # Spacer before analytics section
        {'type': 'spacer', 'data': {'height': 30}},

        # Analytics header
        {
            'type': 'header',
            'data': {
                'text': '<span class="h5"><b>Quote Analytics</b></span>',
                'level': 5,
                'col': 12
            }
        },

        # Spacer after header
        {'type': 'spacer', 'data': {'height': 15}},

        # Row 1: Donut charts side by side
        {
            'type': 'chart',
            'data': {'chart_name': 'Quote Status Distribution', 'col': 6}
        },
        {
            'type': 'chart',
            'data': {'chart_name': 'Top Quote Values', 'col': 6}
        },

        # Spacer between rows
        {'type': 'spacer', 'data': {'height': 25}},

        # Row 2: Monthly volume charts
        {
            'type': 'chart',
            'data': {'chart_name': 'Quotes by Month', 'col': 6}
        },
        {
            'type': 'chart',
            'data': {'chart_name': 'Monthly Quote Revenue', 'col': 6}
        },

        # Spacer between rows
        {'type': 'spacer', 'data': {'height': 25}},

        # Row 3: Trend charts
        {
            'type': 'chart',
            'data': {'chart_name': 'Monthly Profit Trend', 'col': 6}
        },
        {
            'type': 'chart',
            'data': {'chart_name': 'Conversion Rate Trend', 'col': 6}
        },

        # Final spacer
        {'type': 'spacer', 'data': {'height': 20}}
    ]

    # Insert new items
    for i, item in enumerate(new_items):
        content.insert(insert_index + i, item)

    workspace.content = json.dumps(content)

    # Update charts child table
    chart_names = [
        "Quote Status Distribution",
        "Top Quote Values",
        "Quotes by Month",
        "Monthly Quote Revenue",
        "Monthly Profit Trend",
        "Conversion Rate Trend"
    ]

    workspace.charts = []
    for chart_name in chart_names:
        if frappe.db.exists('Dashboard Chart', chart_name):
            workspace.append('charts', {'chart_name': chart_name})

    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"\nWorkspace updated with {len(chart_names)} charts and proper spacing")
    print("Done!")


if __name__ == "__main__":
    fix()
