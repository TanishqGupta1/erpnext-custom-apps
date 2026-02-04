"""
OPS Product Margin Visualizer - Final Version (Modern Layout Only)
"""
import frappe

def create_client_script():
    script_content = '''/**
 * OPS Product Margin Visualizer - Modern Layout
 * Visual editor for product margins and pages
 */

frappe.provide('ops_ziflow');
frappe.provide('ops_ziflow.margin_visualizer');

ops_ziflow.margin_visualizer = {
    frm: null,

    init: function(frm) {
        if (!frm || !frm.doc) return;
        this.frm = frm;
        setTimeout(() => this.render(), 150);
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

    getStyles: function() {
        return `
<style id="ops-visualizer-styles">
.ops-viz-wrapper { margin-bottom: 20px; }

/* Modern Layout */
.ops-modern {
    background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
    border-radius: 12px;
    padding: 28px;
}
.ops-modern-header {
    text-align: center;
    margin-bottom: 24px;
}
.ops-modern-header h3 {
    margin: 0 0 8px 0;
    font-size: 18px;
    font-weight: 700;
    color: #1a202c;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}
.ops-modern-header h3 i { color: #5a67d8; }
.ops-modern-header p {
    margin: 0;
    font-size: 13px;
    color: #718096;
    max-width: 500px;
    margin: 0 auto;
    line-height: 1.5;
}
.ops-modern-header p .txt-green { color: #38a169; font-weight: 600; }
.ops-modern-header p .txt-red { color: #e53e3e; font-weight: 600; }

.ops-modern-grid {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 24px;
    align-items: start;
}
@media (max-width: 900px) {
    .ops-modern-grid { grid-template-columns: 1fr; }
    .ops-modern-svg-wrap { order: -1; }
}

.ops-modern-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.ops-modern-card.mod-cut { border-top: 4px solid #e53e3e; }
.ops-modern-card.mod-safe { border-top: 4px solid #38a169; }
.ops-modern-card .mod-title {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 18px;
    font-size: 15px;
    font-weight: 600;
}
.ops-modern-card.mod-cut .mod-title { color: #c53030; }
.ops-modern-card.mod-safe .mod-title { color: #276749; }
.ops-mod-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}
.ops-modern-card.mod-cut .ops-mod-icon { background: #fed7d7; color: #c53030; }
.ops-modern-card.mod-safe .ops-mod-icon { background: #c6f6d5; color: #276749; }
.ops-mod-inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}
.ops-mod-input label {
    display: block;
    font-size: 10px;
    color: #a0aec0;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}
.ops-mod-input input {
    width: 100%;
    padding: 12px 14px;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    transition: all 0.2s;
}
.ops-modern-card.mod-cut .ops-mod-input input:focus {
    outline: none;
    border-color: #e53e3e;
    box-shadow: 0 0 0 4px rgba(229,62,62,0.1);
}
.ops-modern-card.mod-safe .ops-mod-input input:focus {
    outline: none;
    border-color: #38a169;
    box-shadow: 0 0 0 4px rgba(56,161,105,0.1);
}

.ops-modern-svg-wrap {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    display: flex;
    flex-direction: column;
    align-items: center;
}
.ops-modern-svg-wrap svg {
    width: 220px;
    height: 200px;
}
.ops-legend {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 14px;
}
.ops-legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 500;
}
.ops-legend-item.leg-cut { color: #e53e3e; }
.ops-legend-item.leg-safe { color: #38a169; }
.ops-legend-line {
    width: 24px;
    height: 0;
    border-top: 2px dashed;
}
.ops-legend-item.leg-cut .ops-legend-line { border-color: #e53e3e; }
.ops-legend-item.leg-safe .ops-legend-line { border-color: #38a169; }

/* Pages Section */
.ops-pages-box {
    margin-top: 24px;
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.ops-pages-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%);
    color: white;
}
.ops-pages-top h4 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
}
.ops-add-page-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 9px 18px;
    background: rgba(255,255,255,0.2);
    color: white;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}
.ops-add-page-btn:hover { background: rgba(255,255,255,0.3); }
.ops-pages-note {
    padding: 12px 20px;
    background: #ebf8ff;
    font-size: 11px;
    color: #2b6cb0;
    border-bottom: 1px solid #bee3f8;
}
.ops-pages-tbl {
    width: 100%;
    border-collapse: collapse;
}
.ops-pages-tbl th {
    background: #f7fafc;
    padding: 12px 16px;
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #e2e8f0;
}
.ops-pages-tbl td {
    padding: 14px 16px;
    border-bottom: 1px solid #f0f0f0;
    font-size: 14px;
    vertical-align: middle;
}
.ops-pages-tbl tr:hover td { background: #fafafa; }
.ops-pages-tbl input[type="text"] {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 14px;
}
.ops-pages-tbl input[type="number"] {
    width: 70px;
    padding: 10px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 14px;
    text-align: center;
}
.ops-pages-tbl input:focus {
    outline: none;
    border-color: #3182ce;
    box-shadow: 0 0 0 3px rgba(49,130,206,0.15);
}
.ops-toggle-wrap {
    position: relative;
    width: 50px;
    height: 28px;
}
.ops-toggle-wrap input { opacity: 0; width: 0; height: 0; }
.ops-toggle-track {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background: #cbd5e0;
    border-radius: 28px;
    transition: 0.3s;
}
.ops-toggle-track:before {
    position: absolute;
    content: "";
    height: 22px;
    width: 22px;
    left: 3px;
    bottom: 3px;
    background: white;
    border-radius: 50%;
    transition: 0.3s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.ops-toggle-wrap input:checked + .ops-toggle-track { background: #38a169; }
.ops-toggle-wrap input:checked + .ops-toggle-track:before { transform: translateX(22px); }
.ops-del-btn {
    width: 34px;
    height: 34px;
    border: none;
    background: #fed7d7;
    color: #c53030;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}
.ops-del-btn:hover { background: #e53e3e; color: white; }
.ops-empty-pages {
    padding: 48px 20px;
    text-align: center;
    color: #a0aec0;
}
.ops-empty-pages i { font-size: 36px; margin-bottom: 12px; display: block; opacity: 0.5; }
</style>
        `;
    },

    renderMargins: function() {
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);

        return `
<div class="ops-modern">
    <div class="ops-modern-header">
        <h3><i class="fa fa-crop"></i> Setup Product Margin</h3>
        <p>Configure margins for the designer studio. Set the <span class="txt-red">Cut/Bleed margin</span> (trim area) and <span class="txt-green">Safe margin</span> (content safe zone). Values in inches.</p>
    </div>

    <div class="ops-modern-grid">
        <div class="ops-modern-card mod-cut">
            <div class="mod-title">
                <span class="ops-mod-icon"><i class="fa fa-scissors"></i></span>
                Cut/Bleed Margin
            </div>
            <div class="ops-mod-inputs">
                <div class="ops-mod-input"><label>Top</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="cut" data-d="top" value="${cut.top}"></div>
                <div class="ops-mod-input"><label>Right</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="cut" data-d="right" value="${cut.right}"></div>
                <div class="ops-mod-input"><label>Bottom</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="cut" data-d="bottom" value="${cut.bottom}"></div>
                <div class="ops-mod-input"><label>Left</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="cut" data-d="left" value="${cut.left}"></div>
            </div>
        </div>

        <div class="ops-modern-svg-wrap">
            <svg viewBox="0 0 220 200" class="ops-svg-main">
                <text x="110" y="14" fill="#4a5568" font-size="11" font-weight="600" text-anchor="middle">Top</text>
                <text x="110" y="196" fill="#4a5568" font-size="11" font-weight="600" text-anchor="middle">Bottom</text>
                <text x="10" y="100" fill="#4a5568" font-size="11" font-weight="600" text-anchor="middle" transform="rotate(-90,10,100)">Left</text>
                <text x="210" y="100" fill="#4a5568" font-size="11" font-weight="600" text-anchor="middle" transform="rotate(90,210,100)">Right</text>
                <rect x="25" y="25" width="170" height="150" fill="#fff" stroke="#e2e8f0" stroke-width="1"/>
                <rect x="35" y="35" width="150" height="130" fill="none" stroke="#e53e3e" stroke-width="2" stroke-dasharray="6,4" class="svg-cut-rect"/>
                <rect x="50" y="50" width="120" height="100" fill="none" stroke="#38a169" stroke-width="2" stroke-dasharray="6,4" class="svg-safe-rect"/>
            </svg>
            <div class="ops-legend">
                <div class="ops-legend-item leg-cut"><span class="ops-legend-line"></span> Cut/Bleed</div>
                <div class="ops-legend-item leg-safe"><span class="ops-legend-line"></span> Safe Area</div>
            </div>
        </div>

        <div class="ops-modern-card mod-safe">
            <div class="mod-title">
                <span class="ops-mod-icon"><i class="fa fa-shield"></i></span>
                Safe/Draw Margin
            </div>
            <div class="ops-mod-inputs">
                <div class="ops-mod-input"><label>Top</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="safe" data-d="top" value="${safe.top}"></div>
                <div class="ops-mod-input"><label>Right</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="safe" data-d="right" value="${safe.right}"></div>
                <div class="ops-mod-input"><label>Bottom</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="safe" data-d="bottom" value="${safe.bottom}"></div>
                <div class="ops-mod-input"><label>Left</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="safe" data-d="left" value="${safe.left}"></div>
            </div>
        </div>
    </div>
</div>
        `;
    },

    renderPages: function() {
        const pages = this.getPages();
        let rows = '';

        if (pages.length === 0) {
            rows = `<tr><td colspan="5" class="ops-empty-pages"><i class="fa fa-file-o"></i>No pages configured. Click "Add Page" to create one.</td></tr>`;
        } else {
            pages.forEach((p, i) => {
                rows += `
                <tr data-row="${i}">
                    <td style="width:60px;text-align:center;color:#718096;font-weight:500;">${i + 1}</td>
                    <td><input type="text" class="ops-pg-inp pg-name" value="${p.name || ''}" placeholder="e.g., Front, Back, Inside"></td>
                    <td style="width:100px;"><input type="number" class="ops-pg-inp pg-sort" value="${p.sort || i+1}" min="1"></td>
                    <td style="width:80px;">
                        <label class="ops-toggle-wrap">
                            <input type="checkbox" class="ops-pg-inp pg-active" ${p.active !== false ? 'checked' : ''}>
                            <span class="ops-toggle-track"></span>
                        </label>
                    </td>
                    <td style="width:70px;"><button type="button" class="ops-del-btn ops-del-page" data-row="${i}"><i class="fa fa-trash"></i></button></td>
                </tr>`;
            });
        }

        return `
<div class="ops-pages-box">
    <div class="ops-pages-top">
        <h4><i class="fa fa-files-o"></i> Setup Product Pages</h4>
        <button type="button" class="ops-add-page-btn" id="ops-btn-add-page"><i class="fa fa-plus"></i> Add Page</button>
    </div>
    <div class="ops-pages-note">
        <i class="fa fa-info-circle"></i> Special characters like SPACE, &, ', ., /, <, >, COMMA(,) are not allowed. Name should not start with a number.
    </div>
    <table class="ops-pages-tbl">
        <thead><tr><th>Sr#</th><th>Page Name</th><th>Sort</th><th>Active</th><th>Delete</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>
</div>
        `;
    },

    render: function() {
        const frm = this.frm;
        if (!frm.fields_dict.products_draw_area_margins) return;

        $('#ops-viz-wrapper').remove();
        $('#ops-visualizer-styles').remove();

        const html = `
            ${this.getStyles()}
            <div class="ops-viz-wrapper" id="ops-viz-wrapper">
                ${this.renderMargins()}
                ${this.renderPages()}
            </div>
        `;

        $(frm.fields_dict.custom_size_section.wrapper).before(html);

        $(frm.fields_dict.products_draw_area_margins.wrapper).hide();
        $(frm.fields_dict.products_draw_cutting_margins.wrapper).hide();
        $(frm.fields_dict.productpages.wrapper).hide();

        this.bindEvents();
        this.updateSvg();
    },

    bindEvents: function() {
        const me = this;
        const frm = this.frm;
        const $w = $('#ops-viz-wrapper');

        $w.off('input', '.ops-m-inp').on('input', '.ops-m-inp', function() {
            const $inp = $(this);
            const t = $inp.data('t');
            const d = $inp.data('d');
            const val = parseFloat($inp.val()) || 0;

            const fld = t === 'cut' ? 'products_draw_cutting_margins' : 'products_draw_area_margins';
            const margins = me.parse_margins(frm.doc[fld]);
            margins[d] = val;
            frm.set_value(fld, me.to_json(margins));
            me.updateSvg();
        });

        $w.off('click', '#ops-btn-add-page').on('click', '#ops-btn-add-page', function() {
            me.addPage();
        });

        $w.off('click', '.ops-del-page').on('click', '.ops-del-page', function() {
            me.deletePage($(this).data('row'));
        });

        $w.off('input change', '.ops-pg-inp').on('input change', '.ops-pg-inp', function() {
            me.savePages();
        });
    },

    updateSvg: function() {
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);
        const scale = 40;

        // Cut rect: base at 35,35 size 150x130
        const cX = 35 + Math.abs(cut.left) * scale;
        const cY = 35 + Math.abs(cut.top) * scale;
        const cW = 150 - (Math.abs(cut.left) + Math.abs(cut.right)) * scale;
        const cH = 130 - (Math.abs(cut.top) + Math.abs(cut.bottom)) * scale;

        $('.svg-cut-rect').attr({
            x: Math.max(30, cX),
            y: Math.max(30, cY),
            width: Math.max(60, Math.min(cW, 160)),
            height: Math.max(50, Math.min(cH, 140))
        });

        // Safe rect: inside cut
        const sX = cX + safe.left * scale;
        const sY = cY + safe.top * scale;
        const sW = cW - (safe.left + safe.right) * scale;
        const sH = cH - (safe.top + safe.bottom) * scale;

        $('.svg-safe-rect').attr({
            x: Math.max(40, sX),
            y: Math.max(40, sY),
            width: Math.max(40, Math.min(sW, 140)),
            height: Math.max(30, Math.min(sH, 120))
        });
    },

    getPages: function() {
        const json = this.frm.doc.custom_size_info;
        if (!json || json === 'null') return [];
        try {
            const arr = JSON.parse(json);
            return Array.isArray(arr) ? arr : [];
        } catch (e) { return []; }
    },

    savePages: function() {
        const pages = [];
        $('.ops-pages-tbl tbody tr[data-row]').each(function() {
            pages.push({
                name: $(this).find('.pg-name').val() || '',
                sort: parseInt($(this).find('.pg-sort').val()) || 1,
                active: $(this).find('.pg-active').is(':checked')
            });
        });
        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
    },

    addPage: function() {
        const pages = this.getPages();
        pages.push({ name: '', sort: pages.length + 1, active: true });
        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
        $('.ops-pages-box').replaceWith(this.renderPages());
        this.bindEvents();
    },

    deletePage: function(idx) {
        const pages = this.getPages();
        pages.splice(idx, 1);
        pages.forEach((p, i) => p.sort = i + 1);
        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
        $('.ops-pages-box').replaceWith(this.renderPages());
        this.bindEvents();
    }
};

frappe.ui.form.on('OPS Product', {
    refresh: function(frm) {
        if (frm.doc.name) ops_ziflow.margin_visualizer.init(frm);
    },
    onload: function(frm) {
        if (frm.doc.name) setTimeout(() => ops_ziflow.margin_visualizer.init(frm), 200);
    }
});
'''

    existing = frappe.db.get_value("Client Script", {"dt": "OPS Product"}, "name")
    if existing:
        doc = frappe.get_doc("Client Script", existing)
        doc.script = script_content
        doc.enabled = 1
        doc.save()
        print(f"Updated: {existing}")
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
        print(f"Created: {doc.name}")

    frappe.db.commit()
    return "Final version deployed!"
