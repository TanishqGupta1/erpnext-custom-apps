// Copyright (c) 2024, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("OPS ZiFlow Proof", {
    refresh: function(frm) {
        render_proof_preview(frm);
    },

    preview_url: function(frm) {
        render_proof_preview(frm);
    },

    raw_payload: function(frm) {
        render_proof_preview(frm);
    }
});

function render_proof_preview(frm) {
    let preview_url = frm.doc.preview_url;

    // If no preview_url field, try to extract from raw_payload
    if (!preview_url && frm.doc.raw_payload) {
        try {
            const payload = JSON.parse(frm.doc.raw_payload);
            preview_url = extract_preview_url(payload);
        } catch (e) {
            console.log("Could not parse raw_payload:", e);
        }
    }

    // Render the preview HTML
    const wrapper = frm.fields_dict.proof_preview_html.$wrapper;

    if (preview_url) {
        wrapper.html(`
            <div class="proof-preview-container" style="text-align: center; padding: 10px;">
                <div style="
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    padding: 10px;
                    background: var(--card-bg);
                    display: inline-block;
                    max-width: 100%;
                ">
                    <img
                        src="${preview_url}"
                        alt="Proof Preview"
                        style="
                            max-width: 250px;
                            max-height: 300px;
                            object-fit: contain;
                            border-radius: 4px;
                            cursor: pointer;
                        "
                        onclick="window.open('${preview_url}', '_blank')"
                        onerror="this.parentElement.innerHTML='<div style=\\'color: var(--text-muted); padding: 20px;\\'>Preview not available</div>'"
                        title="Click to view full size"
                    />
                    <div style="margin-top: 8px; font-size: 11px; color: var(--text-muted);">
                        Click image to view full size
                    </div>
                </div>
            </div>
        `);
    } else {
        // Try to show a placeholder or link to ZiFlow
        let ziflow_link = frm.doc.ziflow_url;
        if (ziflow_link) {
            wrapper.html(`
                <div class="proof-preview-container" style="text-align: center; padding: 20px;">
                    <div style="
                        border: 1px dashed var(--border-color);
                        border-radius: 8px;
                        padding: 30px;
                        background: var(--subtle-accent);
                    ">
                        <div style="color: var(--text-muted); margin-bottom: 10px;">
                            <i class="fa fa-image" style="font-size: 32px;"></i>
                        </div>
                        <div style="color: var(--text-muted); margin-bottom: 15px;">
                            No preview available
                        </div>
                        <a href="${ziflow_link}" target="_blank" class="btn btn-sm btn-default">
                            <i class="fa fa-external-link"></i> View in ZiFlow
                        </a>
                    </div>
                </div>
            `);
        } else {
            wrapper.html(`
                <div class="proof-preview-container" style="text-align: center; padding: 20px;">
                    <div style="
                        border: 1px dashed var(--border-color);
                        border-radius: 8px;
                        padding: 30px;
                        background: var(--subtle-accent);
                        color: var(--text-muted);
                    ">
                        <div style="margin-bottom: 10px;">
                            <i class="fa fa-image" style="font-size: 32px;"></i>
                        </div>
                        No preview available
                    </div>
                </div>
            `);
        }
    }
}

function extract_preview_url(payload) {
    // ZiFlow uses 'image_link' for larger preview and 'thumbnail_link' for small thumbnail
    // Prefer larger image_link over thumbnail_link
    if (payload.image_link) return payload.image_link;
    if (payload.thumbnail_link) return payload.thumbnail_link;

    // Check other common field names
    const url_keys = ["thumbnail_url", "preview_url", "thumbnail", "preview", "image_url"];
    for (let key of url_keys) {
        if (payload[key]) {
            return payload[key];
        }
    }

    // Check versions array
    const versions = payload.versions || [];
    if (versions.length > 0) {
        const latest = versions[versions.length - 1];
        if (latest) {
            if (latest.image_link) return latest.image_link;
            if (latest.thumbnail_link) return latest.thumbnail_link;
            for (let key of url_keys) {
                if (latest[key]) {
                    return latest[key];
                }
            }
        }
    }

    return null;
}
