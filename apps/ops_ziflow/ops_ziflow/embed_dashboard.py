# embed_dashboard.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.embed_dashboard.embed_external_dashboard

import frappe
import json

def embed_external_dashboard():
    """Embed the external staging dashboard into the Home workspace."""

    # Get Home workspace
    home = frappe.get_doc("Workspace", "Home")
    print(f"Current Home workspace title: {home.title}")

    # Create new content with embedded iframe
    iframe_content = [
        {
            "id": "dashboard_embed",
            "type": "custom_block",
            "data": {
                "custom_block_name": "OPS Dashboard Embed",
                "col": 12
            }
        }
    ]

    # First, create the Custom Block if it doesn't exist
    if not frappe.db.exists("Custom Block", "OPS Dashboard Embed"):
        custom_block = frappe.new_doc("Custom Block")
        custom_block.name = "OPS Dashboard Embed"
        custom_block.custom_block_name = "OPS Dashboard Embed"
        custom_block.html = '''
<style>
    .ops-dashboard-container {
        width: 100%;
        height: calc(100vh - 120px);
        min-height: 800px;
        border: none;
        border-radius: 8px;
        overflow: hidden;
    }
    .ops-dashboard-container iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
</style>
<div class="ops-dashboard-container">
    <iframe src="https://staging.visualgraphx.com/admin/welcome.php"
            allow="fullscreen"
            loading="lazy">
    </iframe>
</div>
'''
        custom_block.flags.ignore_permissions = True
        custom_block.insert()
        print("Created Custom Block: OPS Dashboard Embed")
    else:
        # Update existing block
        custom_block = frappe.get_doc("Custom Block", "OPS Dashboard Embed")
        custom_block.html = '''
<style>
    .ops-dashboard-container {
        width: 100%;
        height: calc(100vh - 120px);
        min-height: 800px;
        border: none;
        border-radius: 8px;
        overflow: hidden;
    }
    .ops-dashboard-container iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
</style>
<div class="ops-dashboard-container">
    <iframe src="https://staging.visualgraphx.com/admin/welcome.php"
            allow="fullscreen"
            loading="lazy">
    </iframe>
</div>
'''
        custom_block.flags.ignore_permissions = True
        custom_block.save()
        print("Updated Custom Block: OPS Dashboard Embed")

    # Update Home workspace content
    home.title = "OPS Dashboard"
    home.content = json.dumps(iframe_content)

    # Clear other elements since we're using full-page embed
    home.number_cards = []
    home.shortcuts = []
    home.links = []

    home.flags.ignore_permissions = True
    home.save()
    frappe.db.commit()

    print("\nSuccessfully embedded staging dashboard into Home workspace!")
    print("Visit /app/home to see the embedded dashboard.")

if __name__ == "__main__":
    embed_external_dashboard()
