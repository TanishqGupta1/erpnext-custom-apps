frappe.listview_settings["OPS ZiFlow Proof"] = {
    add_fields: ["ops_order", "ops_line_id", "proof_status", "preview_url", "ziflow_url", "proof_name", "ziflow_proof_id"],

    hide_name_column: true,

    get_indicator: function(doc) {
        const status_colors = {
            "Approved": "green",
            "In Review": "orange",
            "Pending": "yellow",
            "Rejected": "red",
            "Changes Requested": "orange",
            "Draft": "gray",
            "Archived": "gray"
        };
        return [__(doc.proof_status), status_colors[doc.proof_status] || "gray", "proof_status,=," + doc.proof_status];
    },

    onload: function(listview) {
        listview.page.add_inner_button(__("View by Order"), function() {
            frappe.set_route("query-report", "ZiFlow Proofs by Order");
        });
    },

    formatters: {
        ziflow_proof_id: function(value, field, doc) {
            if (doc.preview_url) {
                return '<div style="display: flex; align-items: center; gap: 10px;">' +
                    '<img src="' + doc.preview_url + '" ' +
                    'class="proof-list-thumb" ' +
                    'style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px; border: 1px solid var(--border-color); cursor: pointer; flex-shrink: 0;" ' +
                    'onerror="this.style.display=\'none\'" ' +
                    'title="Click to preview" />' +
                    '<a href="/app/ops-ziflow-proof/' + doc.name + '">' + (value || '') + '</a>' +
                    '</div>';
            }
            return '<a href="/app/ops-ziflow-proof/' + doc.name + '">' + (value || '') + '</a>';
        }
    },

    refresh: function(listview) {
        setTimeout(function() {
            listview.$result.find(".proof-list-thumb").off("click").on("click", function(e) {
                e.stopPropagation();
                e.preventDefault();
                var img = $(this);
                var src = img.attr("src");
                if (src) {
                    var d = new frappe.ui.Dialog({
                        title: "Proof Preview",
                        size: "large",
                        fields: [{fieldtype: "HTML", fieldname: "preview_html"}]
                    });
                    d.fields_dict.preview_html.$wrapper.html(
                        '<div style="text-align: center; padding: 20px;">' +
                        '<img src="' + src + '" style="max-width: 100%; max-height: 70vh;" />' +
                        '</div>'
                    );
                    d.show();
                }
            });
        }, 100);
    }
};
