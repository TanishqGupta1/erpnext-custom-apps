// Copyright (c) 2025, VisualGraphX and contributors
// For license information, please see license.txt

frappe.listview_settings['Chatwoot FAQ'] = {
    add_fields: ["sync_status", "enabled", "category"],

    get_indicator: function(doc) {
        let status_map = {
            "Not Synced": ["orange", "Not Synced", "sync_status,=,Not Synced"],
            "Pending": ["yellow", "Pending", "sync_status,=,Pending"],
            "Synced": ["green", "Synced", "sync_status,=,Synced"],
            "Failed": ["red", "Failed", "sync_status,=,Failed"]
        };

        let status = status_map[doc.sync_status];
        if (status) {
            return [__(status[1]), status[0], status[2]];
        }
    },

    onload: function(listview) {
        // Import from Qdrant button
        listview.page.add_inner_button(__('Import from Qdrant'), function() {
            frappe.confirm(
                __('This will import existing FAQs from Qdrant into Frappe. Continue?'),
                function() {
                    frappe.call({
                        method: 'ai_comms_hub.services.qdrant_faq_sync.import_existing_faqs',
                        callback: function(r) {
                            if (r.message && r.message.status === 'started') {
                                frappe.show_alert({
                                    message: __('Import started in background. You will be notified when complete.'),
                                    indicator: 'blue'
                                });
                            }
                        }
                    });
                }
            );
        });

        // Sync All button
        listview.page.add_inner_button(__('Sync All to Qdrant'), function() {
            frappe.confirm(
                __('This will sync all enabled FAQs to Qdrant. Continue?'),
                function() {
                    frappe.call({
                        method: 'ai_comms_hub.services.qdrant_faq_sync.manual_sync_all_faqs',
                        callback: function(r) {
                            if (r.message && r.message.status === 'started') {
                                frappe.show_alert({
                                    message: __('Sync started in background.'),
                                    indicator: 'blue'
                                });
                            }
                        }
                    });
                }
            );
        });

        // View Stats button
        listview.page.add_inner_button(__('View Stats'), function() {
            frappe.call({
                method: 'ai_comms_hub.services.qdrant_faq_sync.get_qdrant_faq_stats',
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        let stats = r.message;
                        let html = `
                            <table class="table table-bordered">
                                <tr><th colspan="2">Qdrant Collection</th></tr>
                                <tr><td>Total Points</td><td>${stats.qdrant.total_points}</td></tr>
                                <tr><td>Frappe FAQs</td><td>${stats.qdrant.frappe_faqs}</td></tr>
                                <tr><td>Legacy FAQs</td><td>${stats.qdrant.legacy_faqs}</td></tr>
                                <tr><th colspan="2">Frappe Database</th></tr>
                                <tr><td>Total FAQs</td><td>${stats.frappe.total_docs}</td></tr>
                                <tr><td>Synced FAQs</td><td>${stats.frappe.synced_docs}</td></tr>
                            </table>
                        `;
                        frappe.msgprint({
                            title: __('FAQ Statistics'),
                            message: html,
                            indicator: 'blue'
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            message: r.message.error || __('Failed to fetch stats'),
                            indicator: 'red'
                        });
                    }
                }
            });
        });
    }
};
