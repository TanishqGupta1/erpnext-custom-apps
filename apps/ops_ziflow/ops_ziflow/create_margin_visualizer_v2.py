"""
Script to create the OPS Product Margin Visualizer Client Script v2
Run with: bench --site erp.visualgraphx.com execute ops_ziflow.create_margin_visualizer_v2.create_client_script
"""
import frappe

def create_client_script():
    """Create or update the margin visualizer client script"""

    script_content = '''/**
 * OPS Product Margin Visualizer v2
 * A visual editor for product cut/safe margins and product pages
 */

frappe.provide('ops_ziflow');
frappe.provide('ops_ziflow.margin_visualizer');

ops_ziflow.margin_visualizer = {
    frm: null,

    init: function(frm) {
        if (!frm || !frm.doc) return;
        this.frm = frm;

        // Wait for DOM to be ready
        setTimeout(() => {
            this.render_visualizer();
        }, 100);
    },

    parse_margins: function(json_str) {
        const defaults = { top: 0, bottom: 0, left: 0, right: 0 };
        if (!json_str) return defaults;
        try {
            const parsed = JSON.parse(json_str);
            return {
                top: parseFloat(parsed.top) || 0,
                bottom: parseFloat(parsed.bottom) || 0,
                left: parseFloat(parsed.left) || 0,
                right: parseFloat(parsed.right) || 0
            };
        } catch (e) {
            return defaults;
        }
    },

    to_json: function(margins) {
        return JSON.stringify({
            top: String(margins.top),
            bottom: String(margins.bottom),
            left: String(margins.left),
            right: String(margins.right)
        });
    },

    render_visualizer: function() {
        const me = this;
        const frm = this.frm;

        if (!frm || !frm.fields_dict || !frm.fields_dict.products_draw_area_margins) {
            console.log('Fields not ready yet');
            return;
        }

        const safe_margins = this.parse_margins(frm.doc.products_draw_area_margins);
        const cut_margins = this.parse_margins(frm.doc.products_draw_cutting_margins);
        const product_pages = frm.doc.productpages || 0;

        const visualizer_html = `
<style>
    .ops-margin-visualizer {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .ops-margin-visualizer .section-title {
        font-size: 14px;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .ops-margin-visualizer .section-title i {
        color: #5e64ff;
    }
    .ops-margin-visualizer .info-box {
        background: #f7fafc;
        border-left: 3px solid #5e64ff;
        padding: 12px 16px;
        font-size: 12px;
        color: #4a5568;
        margin-bottom: 20px;
        border-radius: 0 4px 4px 0;
    }
    .ops-margin-visualizer .info-box .green { color: #38a169; font-weight: 600; }
    .ops-margin-visualizer .info-box .red { color: #e53e3e; font-weight: 600; }

    .ops-margin-main-container {
        display: flex;
        gap: 24px;
        flex-wrap: wrap;
    }
    .ops-svg-container {
        flex: 0 0 280px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .ops-svg-container svg {
        width: 100%;
        max-width: 280px;
        height: auto;
    }
    .ops-inputs-container {
        flex: 1;
        min-width: 300px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .ops-margin-box {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 16px;
    }
    .ops-margin-box.cut-box {
        border-left: 3px solid #e53e3e;
    }
    .ops-margin-box.safe-box {
        border-left: 3px solid #38a169;
    }
    .ops-margin-box .box-title {
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .ops-margin-box.cut-box .box-title {
        color: #e53e3e;
    }
    .ops-margin-box.safe-box .box-title {
        color: #38a169;
    }
    .ops-margin-box .box-title .line {
        width: 24px;
        height: 3px;
        border-radius: 2px;
    }
    .ops-margin-box.cut-box .box-title .line {
        background: #e53e3e;
    }
    .ops-margin-box.safe-box .box-title .line {
        background: #38a169;
    }
    .ops-margin-inputs-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }
    .ops-margin-input-group label {
        display: block;
        font-size: 11px;
        color: #718096;
        margin-bottom: 4px;
        font-weight: 500;
    }
    .ops-margin-input-group input {
        width: 100%;
        padding: 8px 10px;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 13px;
        transition: border-color 0.2s;
    }
    .ops-margin-input-group input:focus {
        outline: none;
        border-color: #5e64ff;
        box-shadow: 0 0 0 3px rgba(94, 100, 255, 0.1);
    }
    .ops-margin-box.cut-box input:focus {
        border-color: #e53e3e;
        box-shadow: 0 0 0 3px rgba(229, 62, 62, 0.1);
    }
    .ops-margin-box.safe-box input:focus {
        border-color: #38a169;
        box-shadow: 0 0 0 3px rgba(56, 161, 105, 0.1);
    }

    /* Product Pages Table */
    .ops-pages-section {
        margin-top: 24px;
        border-top: 1px solid #e2e8f0;
        padding-top: 20px;
    }
    .ops-pages-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .ops-pages-header .section-title {
        margin-bottom: 0;
    }
    .ops-pages-info {
        font-size: 11px;
        color: #a0aec0;
        margin-bottom: 12px;
    }
    .ops-pages-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    .ops-pages-table th {
        background: #4299e1;
        color: white;
        padding: 10px 12px;
        text-align: left;
        font-weight: 500;
    }
    .ops-pages-table th:first-child {
        border-radius: 6px 0 0 0;
        width: 50px;
    }
    .ops-pages-table th:last-child {
        border-radius: 0 6px 0 0;
        width: 60px;
    }
    .ops-pages-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #e2e8f0;
        vertical-align: middle;
    }
    .ops-pages-table tr:hover td {
        background: #f7fafc;
    }
    .ops-pages-table input[type="text"] {
        width: 100%;
        padding: 6px 10px;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 13px;
    }
    .ops-pages-table input[type="number"] {
        width: 60px;
        padding: 6px 10px;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 13px;
        text-align: center;
    }
    .ops-pages-table .toggle-switch {
        position: relative;
        width: 44px;
        height: 24px;
    }
    .ops-pages-table .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }
    .ops-pages-table .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #cbd5e0;
        border-radius: 24px;
        transition: 0.3s;
    }
    .ops-pages-table .toggle-slider:before {
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        border-radius: 50%;
        transition: 0.3s;
    }
    .ops-pages-table input:checked + .toggle-slider {
        background-color: #38a169;
    }
    .ops-pages-table input:checked + .toggle-slider:before {
        transform: translateX(20px);
    }
    .ops-pages-table .delete-btn {
        color: #e53e3e;
        cursor: pointer;
        padding: 4px 8px;
        border: none;
        background: transparent;
        font-size: 16px;
        transition: opacity 0.2s;
    }
    .ops-pages-table .delete-btn:hover {
        opacity: 0.7;
    }
    .ops-add-page-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background: #38a169;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
    }
    .ops-add-page-btn:hover {
        background: #2f855a;
    }
    .ops-no-pages {
        text-align: center;
        padding: 24px;
        color: #a0aec0;
        font-size: 13px;
    }
</style>

<div class="ops-margin-visualizer" id="ops-margin-visualizer">
    <div class="section-title">
        <i class="fa fa-th-large"></i> Setup Product Margin (Inch)
    </div>

    <div class="info-box">
        All margins i.e. top, right, bottom, and left are used to set the safe margin
        (<span class="green">Green Line</span>) and cut or trim margin
        (<span class="red">Red Line</span>) in the designer studio.<br>
        <strong>Note:</strong> Margins are included in the product bleed size (width & height).
    </div>

    <div class="ops-margin-main-container">
        <div class="ops-svg-container">
            <svg viewBox="0 0 260 220" xmlns="http://www.w3.org/2000/svg">
                <!-- Labels -->
                <text x="130" y="14" fill="#1a202c" font-size="12" font-weight="600" text-anchor="middle">Top</text>
                <text x="130" y="212" fill="#1a202c" font-size="12" font-weight="600" text-anchor="middle">Bottom</text>
                <text x="10" y="110" fill="#1a202c" font-size="12" font-weight="600" text-anchor="middle" transform="rotate(-90, 10, 110)">Left</text>
                <text x="250" y="110" fill="#1a202c" font-size="12" font-weight="600" text-anchor="middle" transform="rotate(90, 250, 110)">Right</text>

                <!-- Outer box (product area) -->
                <rect x="30" y="25" width="200" height="170" fill="white" stroke="#e2e8f0" stroke-width="1"/>

                <!-- Cut margin (red dashed) -->
                <rect x="40" y="35" width="180" height="150" fill="none" stroke="#e53e3e" stroke-width="2" stroke-dasharray="6,4" class="ops-cut-rect"/>

                <!-- Safe margin (green dashed) -->
                <rect x="55" y="50" width="150" height="120" fill="none" stroke="#38a169" stroke-width="2" stroke-dasharray="6,4" class="ops-safe-rect"/>

                <!-- Legend -->
                <line x1="35" y1="205" x2="55" y2="205" stroke="#e53e3e" stroke-width="2" stroke-dasharray="4,2"/>
                <text x="60" y="208" fill="#e53e3e" font-size="10" font-weight="500">Cut Margin</text>
                <line x1="135" y1="205" x2="155" y2="205" stroke="#38a169" stroke-width="2" stroke-dasharray="4,2"/>
                <text x="160" y="208" fill="#38a169" font-size="10" font-weight="500">Safe Margin</text>
            </svg>
        </div>

        <div class="ops-inputs-container">
            <div class="ops-margin-box cut-box">
                <div class="box-title">
                    <span class="line"></span> Cut/Bleed Margin
                </div>
                <div class="ops-margin-inputs-grid">
                    <div class="ops-margin-input-group">
                        <label>Top</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="top" value="${cut_margins.top}">
                    </div>
                    <div class="ops-margin-input-group">
                        <label>Right</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="right" value="${cut_margins.right}">
                    </div>
                    <div class="ops-margin-input-group">
                        <label>Bottom</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="bottom" value="${cut_margins.bottom}">
                    </div>
                    <div class="ops-margin-input-group">
                        <label>Left</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="left" value="${cut_margins.left}">
                    </div>
                </div>
            </div>

            <div class="ops-margin-box safe-box">
                <div class="box-title">
                    <span class="line"></span> Safe/Draw Area Margin
                </div>
                <div class="ops-margin-inputs-grid">
                    <div class="ops-margin-input-group">
                        <label>Top</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="top" value="${safe_margins.top}">
                    </div>
                    <div class="ops-margin-input-group">
                        <label>Right</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="right" value="${safe_margins.right}">
                    </div>
                    <div class="ops-margin-input-group">
                        <label>Bottom</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="bottom" value="${safe_margins.bottom}">
                    </div>
                    <div class="ops-margin-input-group">
                        <label>Left</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="left" value="${safe_margins.left}">
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="ops-pages-section">
        <div class="ops-pages-header">
            <div class="section-title">
                <i class="fa fa-file-o"></i> Setup Product Pages
            </div>
            <button type="button" class="ops-add-page-btn" id="ops-add-page-btn">
                <i class="fa fa-plus"></i> Add Page
            </button>
        </div>
        <div class="ops-pages-info">
            Special characters like SPACE, &, ', ., /, <, >, COMMA(,) are not allowed. Page name should not start with a number.
        </div>
        <div id="ops-pages-table-container">
            <!-- Table will be rendered here -->
        </div>
    </div>
</div>
        `;

        // Remove existing visualizer
        $('#ops-margin-visualizer').remove();

        // Find the Custom Size section and insert before it
        const $section = $(frm.fields_dict.custom_size_section.wrapper);
        $section.before(visualizer_html);

        // Hide original fields
        $(frm.fields_dict.products_draw_area_margins.wrapper).hide();
        $(frm.fields_dict.products_draw_cutting_margins.wrapper).hide();
        $(frm.fields_dict.productpages.wrapper).hide();

        // Render pages table
        this.render_pages_table();

        // Bind events
        this.bind_events();
    },

    bind_events: function() {
        const me = this;
        const frm = this.frm;

        // Unbind first to prevent duplicates
        $('#ops-margin-visualizer').off('input', '.ops-margin-input');
        $('#ops-margin-visualizer').off('click', '#ops-add-page-btn');
        $('#ops-margin-visualizer').off('click', '.ops-delete-page');
        $('#ops-margin-visualizer').off('input change', '.ops-page-input');

        // Margin input changes
        $('#ops-margin-visualizer').on('input', '.ops-margin-input', function() {
            const $input = $(this);
            const type = $input.data('type');
            const dir = $input.data('dir');
            const value = parseFloat($input.val()) || 0;

            const field_name = type === 'cut' ? 'products_draw_cutting_margins' : 'products_draw_area_margins';
            const current = me.parse_margins(frm.doc[field_name]);
            current[dir] = value;

            frm.set_value(field_name, me.to_json(current));
            me.update_svg();
        });

        // Add page button
        $('#ops-margin-visualizer').on('click', '#ops-add-page-btn', function() {
            me.add_page();
        });

        // Delete page button
        $('#ops-margin-visualizer').on('click', '.ops-delete-page', function() {
            const idx = $(this).data('idx');
            me.delete_page(idx);
        });

        // Page input changes
        $('#ops-margin-visualizer').on('input change', '.ops-page-input', function() {
            me.save_pages();
        });
    },

    update_svg: function() {
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);

        // Scale: base rect is 200x170 starting at 30,25
        // Safe rect default: 55,50 150x120
        // Cut rect default: 40,35 180x150
        const scale = 60;

        const cutX = 40 + (Math.abs(cut.left) * scale);
        const cutY = 35 + (Math.abs(cut.top) * scale);
        const cutW = 180 - ((Math.abs(cut.left) + Math.abs(cut.right)) * scale);
        const cutH = 150 - ((Math.abs(cut.top) + Math.abs(cut.bottom)) * scale);

        const safeX = cutX + (safe.left * scale);
        const safeY = cutY + (safe.top * scale);
        const safeW = cutW - ((safe.left + safe.right) * scale);
        const safeH = cutH - ((safe.top + safe.bottom) * scale);

        $('.ops-cut-rect').attr({
            x: Math.max(35, Math.min(cutX, 100)),
            y: Math.max(30, Math.min(cutY, 80)),
            width: Math.max(80, Math.min(cutW, 190)),
            height: Math.max(60, Math.min(cutH, 160))
        });

        $('.ops-safe-rect').attr({
            x: Math.max(45, Math.min(safeX, 110)),
            y: Math.max(40, Math.min(safeY, 90)),
            width: Math.max(60, Math.min(safeW, 170)),
            height: Math.max(40, Math.min(safeH, 140))
        });
    },

    // Product Pages Management
    get_pages: function() {
        const pages_json = this.frm.doc.custom_size_info;
        if (!pages_json || pages_json === 'null') return [];
        try {
            const parsed = JSON.parse(pages_json);
            if (Array.isArray(parsed)) return parsed;
            return [];
        } catch (e) {
            return [];
        }
    },

    save_pages: function() {
        const pages = [];
        $('#ops-pages-table-container tbody tr').each(function(idx) {
            const $row = $(this);
            pages.push({
                name: $row.find('.page-name-input').val() || '',
                sort: parseInt($row.find('.page-sort-input').val()) || (idx + 1),
                active: $row.find('.page-active-input').is(':checked')
            });
        });

        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
    },

    render_pages_table: function() {
        const pages = this.get_pages();
        let html = '';

        if (pages.length === 0) {
            html = '<div class="ops-no-pages">No pages configured. Click "Add Page" to add one.</div>';
        } else {
            html = `
                <table class="ops-pages-table">
                    <thead>
                        <tr>
                            <th>Sr#</th>
                            <th>Page Name</th>
                            <th>Sort</th>
                            <th>Active</th>
                            <th>Delete</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            pages.forEach((page, idx) => {
                html += `
                    <tr>
                        <td>${idx + 1}</td>
                        <td><input type="text" class="ops-page-input page-name-input" value="${page.name || ''}" placeholder="e.g., Front"></td>
                        <td><input type="number" class="ops-page-input page-sort-input" value="${page.sort || (idx + 1)}" min="1"></td>
                        <td>
                            <label class="toggle-switch">
                                <input type="checkbox" class="ops-page-input page-active-input" ${page.active !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </td>
                        <td><button type="button" class="delete-btn ops-delete-page" data-idx="${idx}"><i class="fa fa-trash"></i></button></td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
        }

        $('#ops-pages-table-container').html(html);
    },

    add_page: function() {
        const pages = this.get_pages();
        pages.push({
            name: '',
            sort: pages.length + 1,
            active: true
        });
        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
        this.render_pages_table();
    },

    delete_page: function(idx) {
        const pages = this.get_pages();
        pages.splice(idx, 1);
        // Re-sort
        pages.forEach((p, i) => { p.sort = i + 1; });
        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
        this.render_pages_table();
    },

    refresh: function() {
        this.render_visualizer();
    }
};

// Form events
frappe.ui.form.on('OPS Product', {
    refresh: function(frm) {
        if (frm.doc.name) {
            ops_ziflow.margin_visualizer.init(frm);
        }
    },

    onload: function(frm) {
        // Delay initialization to ensure fields are loaded
        if (frm.doc.name) {
            setTimeout(() => {
                ops_ziflow.margin_visualizer.init(frm);
            }, 500);
        }
    },

    // Re-render if these fields change externally
    products_draw_area_margins: function(frm) {
        // Don't re-render to avoid loops
    },
    products_draw_cutting_margins: function(frm) {
        // Don't re-render to avoid loops
    }
});
'''

    # Check if exists
    existing = frappe.db.get_value("Client Script", {"dt": "OPS Product"}, "name")

    if existing:
        doc = frappe.get_doc("Client Script", existing)
        doc.script = script_content
        doc.enabled = 1
        doc.save()
        print(f"Updated existing Client Script: {existing}")
    else:
        doc = frappe.get_doc({
            "doctype": "Client Script",
            "name": "OPS Product - Margin Visualizer",
            "dt": "OPS Product",
            "view": "Form",
            "enabled": 1,
            "script": script_content
        })
        doc.insert()
        print(f"Created new Client Script: {doc.name}")

    frappe.db.commit()
    return "Client Script v2 created/updated successfully"
