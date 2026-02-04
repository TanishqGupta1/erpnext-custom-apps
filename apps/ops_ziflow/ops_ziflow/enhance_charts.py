# enhance_charts.py
import frappe
import json

def enhance():
    """Enhance OPS Quote charts with better colors and styling"""

    # Define enhanced chart configurations
    charts_config = [
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
            "is_standard": 0,
            "color": "#5e64ff",
            "custom_options": json.dumps({
                "colors": ["#5e64ff", "#ecad4b", "#36a2eb", "#4bc0c0", "#ff6384", "#9966ff"],
                "axisOptions": {
                    "shortenYAxisNumbers": 1
                }
            })
        },
        {
            "name": "Quotes by Month",
            "chart_name": "Quotes by Month",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Count",
            "group_by_based_on": "quote_date",
            "group_by_timespan": "Monthly",
            "type": "Bar",
            "filters_json": "[]",
            "is_public": 1,
            "is_standard": 0,
            "timespan": "Last Year",
            "color": "#5e64ff",
            "custom_options": json.dumps({
                "colors": ["#5e64ff"],
                "barOptions": {
                    "spaceRatio": 0.4
                },
                "axisOptions": {
                    "xAxisMode": "tick",
                    "shortenYAxisNumbers": 1
                }
            })
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
            "is_standard": 0,
            "color": "#36a2eb",
            "custom_options": json.dumps({
                "colors": ["#36a2eb"],
                "barOptions": {
                    "spaceRatio": 0.3
                },
                "axisOptions": {
                    "shortenYAxisNumbers": 1
                },
                "tooltipOptions": {
                    "formatTooltipY": "d => '$' + d.toLocaleString()"
                }
            })
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
            "timespan": "Last Year",
            "color": "#4bc0c0",
            "custom_options": json.dumps({
                "colors": ["#4bc0c0"],
                "barOptions": {
                    "spaceRatio": 0.4
                },
                "axisOptions": {
                    "xAxisMode": "tick",
                    "shortenYAxisNumbers": 1
                }
            })
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
            "timespan": "Last Year",
            "color": "#ff6384",
            "custom_options": json.dumps({
                "colors": ["#ff6384"],
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
            "name": "Revenue vs Cost Comparison",
            "chart_name": "Revenue vs Cost Comparison",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Sum",
            "group_by_based_on": "quote_date",
            "group_by_timespan": "Monthly",
            "aggregate_function_based_on": "quote_price",
            "type": "Line",
            "filters_json": "[]",
            "is_public": 1,
            "is_standard": 0,
            "timespan": "Last Year",
            "color": "#5e64ff",
            "custom_options": json.dumps({
                "colors": ["#5e64ff", "#ff6384"],
                "lineOptions": {
                    "regionFill": 1,
                    "hideDots": 0,
                    "dotSize": 3
                },
                "axisOptions": {
                    "shortenYAxisNumbers": 1
                }
            })
        },
        {
            "name": "Top Quote Values",
            "chart_name": "Top Quote Values",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Sum",
            "group_by_based_on": "quote_status",
            "aggregate_function_based_on": "profit_margin",
            "type": "Percentage",
            "filters_json": "[]",
            "is_public": 1,
            "is_standard": 0,
            "color": "#9966ff",
            "custom_options": json.dumps({
                "colors": ["#5e64ff", "#ecad4b", "#36a2eb", "#4bc0c0", "#ff6384", "#9966ff"],
                "axisOptions": {
                    "shortenYAxisNumbers": 1
                }
            })
        },
        {
            "name": "Conversion Rate Trend",
            "chart_name": "Conversion Rate Trend",
            "chart_type": "Group By",
            "document_type": "OPS Quote",
            "group_by_type": "Count",
            "group_by_based_on": "quote_date",
            "group_by_timespan": "Monthly",
            "type": "Line",
            "filters_json": json.dumps([["OPS Quote", "quote_status", "=", "Converted"]]),
            "is_public": 1,
            "is_standard": 0,
            "timespan": "Last Year",
            "color": "#4bc0c0",
            "custom_options": json.dumps({
                "colors": ["#4bc0c0"],
                "lineOptions": {
                    "regionFill": 1,
                    "hideDots": 0,
                    "dotSize": 4,
                    "heatline": 1
                },
                "axisOptions": {
                    "xAxisMode": "tick",
                    "shortenYAxisNumbers": 1
                }
            })
        }
    ]

    print("=== Enhancing OPS Quote Charts ===\n")

    for chart_data in charts_config:
        chart_name = chart_data["name"]

        if frappe.db.exists("Dashboard Chart", chart_name):
            print(f"Updating: {chart_name}")
            chart = frappe.get_doc("Dashboard Chart", chart_name)
            for key, value in chart_data.items():
                if key != "name":
                    setattr(chart, key, value)
            chart.save(ignore_permissions=True)
        else:
            print(f"Creating: {chart_name}")
            chart = frappe.get_doc({
                "doctype": "Dashboard Chart",
                **chart_data
            })
            chart.insert(ignore_permissions=True)

    frappe.db.commit()
    print(f"\nEnhanced {len(charts_config)} charts")

    # Update workspace with new charts
    update_workspace()


def update_workspace():
    """Update workspace with enhanced chart layout"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    # Parse existing content
    content = json.loads(workspace.content) if workspace.content else []

    # Remove old chart items and Quote Analytics header
    content = [item for item in content if not (
        item.get('type') == 'chart' or
        (item.get('type') == 'header' and 'Analytics' in str(item.get('data', {}).get('text', ''))) or
        (item.get('type') == 'spacer' and content.index(item) > 30)  # Remove spacers near end
    )]

    # Find OPS Quotes section end
    insert_index = len(content)
    for i, item in enumerate(content):
        if item.get('type') == 'header' and 'Quote' in str(item.get('data', {}).get('text', '')):
            # Find end of this section
            for j in range(i + 1, len(content)):
                if content[j].get('type') == 'header':
                    insert_index = j
                    break
            else:
                insert_index = len(content)
            break

    # Add new chart section
    new_items = [
        {'type': 'spacer', 'data': {'height': 20}},
        {
            'type': 'header',
            'data': {
                'text': '<span class="h5"><b>Quote Analytics</b></span>',
                'level': 5,
                'col': 12
            }
        },
        # Row 1: Status Distribution and Conversion Trend
        {
            'type': 'chart',
            'data': {'chart_name': 'Quote Status Distribution', 'col': 6}
        },
        {
            'type': 'chart',
            'data': {'chart_name': 'Top Quote Values', 'col': 6}
        },
        # Row 2: Monthly trends
        {
            'type': 'chart',
            'data': {'chart_name': 'Quotes by Month', 'col': 6}
        },
        {
            'type': 'chart',
            'data': {'chart_name': 'Monthly Quote Revenue', 'col': 6}
        },
        # Row 3: Profit and Conversion
        {
            'type': 'chart',
            'data': {'chart_name': 'Monthly Profit Trend', 'col': 6}
        },
        {
            'type': 'chart',
            'data': {'chart_name': 'Conversion Rate Trend', 'col': 6}
        },
        # Row 4: Value comparison
        {
            'type': 'chart',
            'data': {'chart_name': 'Quote Value by Status', 'col': 12}
        }
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
        "Conversion Rate Trend",
        "Quote Value by Status"
    ]

    # Clear and re-add
    workspace.charts = []
    for chart_name in chart_names:
        if frappe.db.exists('Dashboard Chart', chart_name):
            workspace.append('charts', {'chart_name': chart_name})

    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"\nUpdated workspace with {len(chart_names)} charts in optimized layout")
    print("Done!")


if __name__ == "__main__":
    enhance()
