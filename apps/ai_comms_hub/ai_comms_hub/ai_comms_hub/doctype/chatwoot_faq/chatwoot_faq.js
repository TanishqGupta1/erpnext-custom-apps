// Copyright (c) 2025, VisualGraphX and contributors
// For license information, please see license.txt

frappe.ui.form.on('Chatwoot FAQ', {
    refresh: function(frm) {
        // Add sync status indicator
        set_sync_indicator(frm);

        // Add custom buttons
        if (!frm.is_new()) {
            add_faq_buttons(frm);
        }
    },

    enabled: function(frm) {
        // If disabled, show warning that it will be removed from Qdrant
        if (!frm.doc.enabled && frm.doc.sync_status === "Synced") {
            frappe.show_alert({
                message: __('FAQ will be removed from search on save'),
                indicator: 'orange'
            });
        }
    }
});

function set_sync_indicator(frm) {
    let indicator_map = {
        "Not Synced": "orange",
        "Pending": "yellow",
        "Synced": "green",
        "Failed": "red"
    };

    let indicator = indicator_map[frm.doc.sync_status] || "gray";
    frm.page.set_indicator(frm.doc.sync_status, indicator);
}

function add_faq_buttons(frm) {
    // Sync Now button
    frm.add_custom_button(__('Sync to Qdrant'), function() {
        sync_to_qdrant(frm);
    }, __('Actions'));

    // Test Search button
    frm.add_custom_button(__('Test Search'), function() {
        test_search(frm);
    }, __('Actions'));

    // View Point ID (if synced)
    if (frm.doc.qdrant_point_id) {
        frm.add_custom_button(__('View Point ID'), function() {
            frappe.msgprint({
                title: __('Qdrant Point ID'),
                message: `<code>${frm.doc.qdrant_point_id}</code>`,
                indicator: 'blue'
            });
        }, __('Actions'));
    }
}

function sync_to_qdrant(frm) {
    frappe.show_alert({
        message: __('Syncing to Qdrant...'),
        indicator: 'blue'
    });

    frm.call({
        method: 'sync_now',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                if (r.message.status === 'success') {
                    frappe.show_alert({
                        message: __('Successfully synced to Qdrant'),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('Sync Failed'),
                        message: r.message.message || r.message.error || __('Unknown error'),
                        indicator: 'red'
                    });
                }
                frm.reload_doc();
            }
        }
    });
}

function test_search(frm) {
    // Open dialog to test searching for this FAQ
    let d = new frappe.ui.Dialog({
        title: __('Test FAQ Search'),
        fields: [
            {
                label: __('Search Query'),
                fieldname: 'query',
                fieldtype: 'Data',
                default: frm.doc.question,
                reqd: 1
            }
        ],
        primary_action_label: __('Search'),
        primary_action: function(values) {
            frappe.call({
                method: 'ai_comms_hub.services.qdrant_faq_sync.search_faqs',
                args: {
                    query: values.query,
                    limit: 5
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        let results_html = r.message.map(function(item, idx) {
                            let is_current = item.doc_name === frm.doc.name;
                            let highlight = is_current ? 'style="background-color: #e8f5e9; padding: 8px; border-radius: 4px;"' : 'style="padding: 8px;"';
                            return `
                                <div ${highlight}>
                                    <strong>${idx + 1}. ${item.question}</strong>
                                    <br><small>Score: ${(item.score * 100).toFixed(1)}% | Category: ${item.category || 'None'}</small>
                                    ${is_current ? ' <span class="badge badge-success">This FAQ</span>' : ''}
                                </div>
                            `;
                        }).join('<hr style="margin: 8px 0;">');

                        frappe.msgprint({
                            title: __('Search Results'),
                            message: results_html,
                            indicator: 'blue'
                        });
                    } else {
                        frappe.msgprint(__('No results found. Make sure FAQs are synced to Qdrant.'));
                    }
                }
            });
            d.hide();
        }
    });
    d.show();
}
