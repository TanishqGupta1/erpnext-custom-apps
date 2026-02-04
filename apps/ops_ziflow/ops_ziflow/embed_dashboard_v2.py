# embed_dashboard_v2.py
# Run with: bench --site erp.visualgraphx.com execute ops_ziflow.embed_dashboard_v2.embed_external_dashboard

import frappe
import json

def embed_external_dashboard():
    """Embed the external staging dashboard into the Home workspace using Custom HTML Block."""

    # Get Home workspace
    home = frappe.get_doc("Workspace", "Home")
    print(f"Current Home workspace title: {home.title}")

    # First, create the Custom HTML Block if it doesn't exist
    block_name = "OPS Dashboard Embed"

    if not frappe.db.exists("Custom HTML Block", block_name):
        custom_block = frappe.new_doc("Custom HTML Block")
        custom_block.name = block_name
        custom_block.html = '''
<style>
    .ops-dashboard-container {
        width: 100%;
        height: calc(100vh - 60px);
        min-height: 900px;
        border: none;
        border-radius: 8px;
        overflow: hidden;
        margin: -15px;
    }
    .ops-dashboard-container iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
    /* Hide workspace header and footer when showing embed */
    .workspace-header, .workspace-footer {
        display: none !important;
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
        print(f"Created Custom HTML Block: {block_name}")
    else:
        # Update existing block
        custom_block = frappe.get_doc("Custom HTML Block", block_name)
        custom_block.html = '''
<style>
    .ops-dashboard-container {
        width: 100%;
        height: calc(100vh - 60px);
        min-height: 900px;
        border: none;
        border-radius: 8px;
        overflow: hidden;
        margin: -15px;
    }
    .ops-dashboard-container iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
    /* Hide workspace header and footer when showing embed */
    .workspace-header, .workspace-footer {
        display: none !important;
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
        print(f"Updated Custom HTML Block: {block_name}")

    # Update Home workspace content with the custom block
    iframe_content = [
        {
            "id": "dashboard_embed",
            "type": "custom_block",
            "data": {
                "custom_block_name": block_name,
                "col": 12
            }
        }
    ]

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
