# fix_charts.py
import frappe
import json

def fix():
    """Add charts to workspace charts child table"""

    workspace = frappe.get_doc('Workspace', 'OPS Dashboard')

    charts_to_add = [
        "Quote Status Distribution",
        "Quotes by Month",
        "Quote Value by Status",
        "Monthly Quote Revenue",
        "Monthly Profit Trend"
    ]

    existing_charts = [c.chart_name for c in (workspace.charts or [])]

    for chart_name in charts_to_add:
        if chart_name not in existing_charts:
            if frappe.db.exists('Dashboard Chart', chart_name):
                workspace.append('charts', {
                    'chart_name': chart_name
                })
                print(f"Added to child table: {chart_name}")
            else:
                print(f"Chart not found: {chart_name}")

    workspace.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"\nWorkspace now has {len(workspace.charts)} charts in child table")
    print("Done!")


if __name__ == "__main__":
    fix()
