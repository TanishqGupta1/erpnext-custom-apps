"""
OPS Product Margin Visualizer v4 - Fixed version
Fixes: Layout toggle, decimal inputs, SVG updates
"""
import frappe

def create_client_script():
    script_content = '''/**
 * OPS Product Margin Visualizer v4
 * Fixed: Layout toggle, decimal inputs, SVG updates
 */

frappe.provide('ops_ziflow');
frappe.provide('ops_ziflow.margin_visualizer');

ops_ziflow.margin_visualizer = {
    frm: null,
    current_layout: 'classic',

    init: function(frm) {
        if (!frm || !frm.doc) return;
        this.frm = frm;
        this.current_layout = localStorage.getItem('ops_margin_layout') || 'classic';

        setTimeout(() => {
            this.render();
        }, 150);
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

/* Layout Toggle */
.ops-layout-switch {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    padding: 14px 20px;
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    border-radius: 10px;
    color: white;
}
.ops-layout-switch .switch-label {
    font-size: 13px;
    font-weight: 500;
}
.ops-switch-btns {
    display: flex;
    background: rgba(255,255,255,0.15);
    border-radius: 8px;
    padding: 4px;
}
.ops-switch-btn {
    padding: 8px 20px;
    border: none;
    background: transparent;
    color: rgba(255,255,255,0.7);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.25s ease;
    display: flex;
    align-items: center;
    gap: 6px;
}
.ops-switch-btn:hover { color: white; background: rgba(255,255,255,0.1); }
.ops-switch-btn.active {
    background: white;
    color: #5a67d8;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* ============ CLASSIC LAYOUT ============ */
.ops-classic {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 24px;
}
.ops-classic-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}
.ops-classic-header i { color: #5a67d8; font-size: 18px; }
.ops-classic-header h3 { margin: 0; font-size: 16px; font-weight: 600; color: #1a202c; }
.ops-classic-info {
    background: #f7fafc;
    border-left: 4px solid #5a67d8;
    padding: 12px 16px;
    font-size: 12px;
    color: #4a5568;
    margin-bottom: 24px;
    border-radius: 0 6px 6px 0;
    line-height: 1.6;
}
.ops-classic-info .txt-green { color: #38a169; font-weight: 600; }
.ops-classic-info .txt-red { color: #e53e3e; font-weight: 600; }

.ops-classic-content {
    display: flex;
    gap: 40px;
    flex-wrap: wrap;
}
.ops-classic-left { flex: 0 0 auto; }
.ops-classic-right { flex: 1; min-width: 280px; display: flex; flex-direction: column; gap: 16px; }

/* Diagram with inputs */
.ops-diagram-box {
    position: relative;
    width: 340px;
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.ops-diagram-svg {
    width: 180px;
    height: 160px;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
}
.ops-dir-label {
    position: absolute;
    font-size: 12px;
    font-weight: 600;
    color: #2d3748;
}
.ops-dir-label.lbl-top { top: 10px; left: 50%; transform: translateX(-50%); }
.ops-dir-label.lbl-bottom { bottom: 10px; left: 50%; transform: translateX(-50%); }
.ops-dir-label.lbl-left { left: 10px; top: 50%; transform: translateY(-50%) rotate(-90deg); }
.ops-dir-label.lbl-right { right: 10px; top: 50%; transform: translateY(-50%) rotate(90deg); }

/* Input pairs around diagram */
.ops-input-pair {
    position: absolute;
    display: flex;
    gap: 6px;
}
.ops-input-pair.pair-top { top: 30px; left: 50%; transform: translateX(-50%); }
.ops-input-pair.pair-bottom { bottom: 30px; left: 50%; transform: translateX(-50%); }
.ops-input-pair.pair-left { left: 30px; top: 50%; transform: translateY(-50%); flex-direction: column; }
.ops-input-pair.pair-right { right: 30px; top: 50%; transform: translateY(-50%); flex-direction: column; }

.ops-tiny-input {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.ops-tiny-input input {
    width: 58px;
    padding: 6px 4px;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    font-size: 12px;
    text-align: center;
}
.ops-tiny-input input.inp-cut {
    background: #fff5f5;
    border-color: #feb2b2;
}
.ops-tiny-input input.inp-cut:focus {
    outline: none;
    border-color: #e53e3e;
    box-shadow: 0 0 0 3px rgba(229,62,62,0.15);
}
.ops-tiny-input input.inp-safe {
    background: #f0fff4;
    border-color: #9ae6b4;
}
.ops-tiny-input input.inp-safe:focus {
    outline: none;
    border-color: #38a169;
    box-shadow: 0 0 0 3px rgba(56,161,105,0.15);
}
.ops-tiny-input .inp-lbl {
    font-size: 9px;
    color: #a0aec0;
    margin-top: 3px;
    text-transform: uppercase;
}

/* Legend */
.ops-legend {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-top: 16px;
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

/* Margin panels */
.ops-margin-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
}
.ops-margin-card.card-cut { border-left: 4px solid #e53e3e; }
.ops-margin-card.card-safe { border-left: 4px solid #38a169; }
.ops-margin-card .card-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
    font-size: 14px;
    font-weight: 600;
}
.ops-margin-card.card-cut .card-title { color: #e53e3e; }
.ops-margin-card.card-safe .card-title { color: #38a169; }
.ops-margin-card .title-bar {
    width: 24px;
    height: 4px;
    border-radius: 2px;
}
.ops-margin-card.card-cut .title-bar { background: #e53e3e; }
.ops-margin-card.card-safe .title-bar { background: #38a169; }
.ops-card-inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.ops-card-input label {
    display: block;
    font-size: 11px;
    color: #718096;
    margin-bottom: 4px;
    font-weight: 500;
}
.ops-card-input input {
    width: 100%;
    padding: 9px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 14px;
}
.ops-card-input input:focus {
    outline: none;
    border-color: #5a67d8;
    box-shadow: 0 0 0 3px rgba(90,103,216,0.1);
}

/* ============ MODERN LAYOUT ============ */
.ops-modern {
    background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
    border-radius: 12px;
    padding: 28px;
}
.ops-modern-header {
    text-align: center;
    margin-bottom: 28px;
}
.ops-modern-header h3 {
    margin: 0 0 6px 0;
    font-size: 20px;
    font-weight: 700;
    color: #1a202c;
}
.ops-modern-header p {
    margin: 0;
    font-size: 13px;
    color: #718096;
}
.ops-modern-grid {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 24px;
    align-items: start;
}
@media (max-width: 900px) {
    .ops-modern-grid { grid-template-columns: 1fr; }
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
    width: 200px;
    height: 180px;
}

/* ============ PAGES SECTION ============ */
.ops-pages-box {
    margin-top: 28px;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
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
    padding: 10px 20px;
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

    renderClassic: function() {
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);

        return `
<div class="ops-classic">
    <div class="ops-classic-header">
        <i class="fa fa-crop"></i>
        <h3>Setup Product Margin (Inch)</h3>
    </div>
    <div class="ops-classic-info">
        All margins i.e. top, right, bottom, and left are used to set the safe margin
        (<span class="txt-green">Green Line</span>) and cut or trim margin
        (<span class="txt-red">Red Line</span>) in the designer studio.
        <strong>Note:</strong> Margins are included in the product bleed size (width & height).
    </div>

    <div class="ops-classic-content">
        <div class="ops-classic-left">
            <div class="ops-diagram-box">
                <span class="ops-dir-label lbl-top">Top</span>
                <span class="ops-dir-label lbl-bottom">Bottom</span>
                <span class="ops-dir-label lbl-left">Left</span>
                <span class="ops-dir-label lbl-right">Right</span>

                <div class="ops-input-pair pair-top">
                    <div class="ops-tiny-input">
                        <input type="text" inputmode="decimal" class="inp-cut ops-m-inp" data-t="cut" data-d="top" value="${cut.top}">
                        <span class="inp-lbl">Cut</span>
                    </div>
                    <div class="ops-tiny-input">
                        <input type="text" inputmode="decimal" class="inp-safe ops-m-inp" data-t="safe" data-d="top" value="${safe.top}">
                        <span class="inp-lbl">Safe</span>
                    </div>
                </div>

                <div class="ops-input-pair pair-bottom">
                    <div class="ops-tiny-input">
                        <input type="text" inputmode="decimal" class="inp-safe ops-m-inp" data-t="safe" data-d="bottom" value="${safe.bottom}">
                        <span class="inp-lbl">Safe</span>
                    </div>
                    <div class="ops-tiny-input">
                        <input type="text" inputmode="decimal" class="inp-cut ops-m-inp" data-t="cut" data-d="bottom" value="${cut.bottom}">
                        <span class="inp-lbl">Cut</span>
                    </div>
                </div>

                <div class="ops-input-pair pair-left">
                    <div class="ops-tiny-input">
                        <input type="text" inputmode="decimal" class="inp-cut ops-m-inp" data-t="cut" data-d="left" value="${cut.left}">
                        <span class="inp-lbl">Cut</span>
                    </div>
                    <div class="ops-tiny-input">
                        <input type="text" inputmode="decimal" class="inp-safe ops-m-inp" data-t="safe" data-d="left" value="${safe.left}">
                        <span class="inp-lbl">Safe</span>
                    </div>
                </div>

                <div class="ops-input-pair pair-right">
                    <div class="ops-tiny-input">
                        <input type="text" inputmode="decimal" class="inp-safe ops-m-inp" data-t="safe" data-d="right" value="${safe.right}">
                        <span class="inp-lbl">Safe</span>
                    </div>
                    <div class="ops-tiny-input">
                        <input type="text" inputmode="decimal" class="inp-cut ops-m-inp" data-t="cut" data-d="right" value="${cut.right}">
                        <span class="inp-lbl">Cut</span>
                    </div>
                </div>

                <div class="ops-diagram-svg">
                    <svg viewBox="0 0 180 160" class="ops-svg-main">
                        <rect x="10" y="10" width="160" height="140" fill="none" stroke="#e53e3e" stroke-width="2" stroke-dasharray="5,3" class="svg-cut-rect"/>
                        <rect x="25" y="25" width="130" height="110" fill="none" stroke="#38a169" stroke-width="2" stroke-dasharray="5,3" class="svg-safe-rect"/>
                    </svg>
                </div>
            </div>

            <div class="ops-legend">
                <div class="ops-legend-item leg-cut"><span class="ops-legend-line"></span> Cut Margin</div>
                <div class="ops-legend-item leg-safe"><span class="ops-legend-line"></span> Safe Margin</div>
            </div>
        </div>

        <div class="ops-classic-right">
            <div class="ops-margin-card card-cut">
                <div class="card-title"><span class="title-bar"></span> Cut/Bleed Margin</div>
                <div class="ops-card-inputs">
                    <div class="ops-card-input"><label>Top</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="cut" data-d="top" value="${cut.top}"></div>
                    <div class="ops-card-input"><label>Right</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="cut" data-d="right" value="${cut.right}"></div>
                    <div class="ops-card-input"><label>Bottom</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="cut" data-d="bottom" value="${cut.bottom}"></div>
                    <div class="ops-card-input"><label>Left</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="cut" data-d="left" value="${cut.left}"></div>
                </div>
            </div>

            <div class="ops-margin-card card-safe">
                <div class="card-title"><span class="title-bar"></span> Safe/Draw Area Margin</div>
                <div class="ops-card-inputs">
                    <div class="ops-card-input"><label>Top</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="safe" data-d="top" value="${safe.top}"></div>
                    <div class="ops-card-input"><label>Right</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="safe" data-d="right" value="${safe.right}"></div>
                    <div class="ops-card-input"><label>Bottom</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="safe" data-d="bottom" value="${safe.bottom}"></div>
                    <div class="ops-card-input"><label>Left</label><input type="text" inputmode="decimal" class="ops-m-inp" data-t="safe" data-d="left" value="${safe.left}"></div>
                </div>
            </div>
        </div>
    </div>
</div>
        `;
    },

    renderModern: function() {
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);

        return `
<div class="ops-modern">
    <div class="ops-modern-header">
        <h3>Setup Product Margin</h3>
        <p>Configure cut/bleed and safe margins for the designer (values in inches)</p>
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
            <svg viewBox="0 0 200 180" class="ops-svg-main">
                <text x="100" y="12" fill="#4a5568" font-size="10" font-weight="600" text-anchor="middle">Top</text>
                <text x="100" y="175" fill="#4a5568" font-size="10" font-weight="600" text-anchor="middle">Bottom</text>
                <text x="8" y="90" fill="#4a5568" font-size="10" font-weight="600" text-anchor="middle" transform="rotate(-90,8,90)">Left</text>
                <text x="192" y="90" fill="#4a5568" font-size="10" font-weight="600" text-anchor="middle" transform="rotate(90,192,90)">Right</text>
                <rect x="20" y="20" width="160" height="140" fill="#fff" stroke="#e2e8f0" stroke-width="1"/>
                <rect x="30" y="30" width="140" height="120" fill="none" stroke="#e53e3e" stroke-width="2" stroke-dasharray="5,3" class="svg-cut-rect"/>
                <rect x="45" y="45" width="110" height="90" fill="none" stroke="#38a169" stroke-width="2" stroke-dasharray="5,3" class="svg-safe-rect"/>
            </svg>
            <div class="ops-legend" style="margin-top:12px;">
                <div class="ops-legend-item leg-cut"><span class="ops-legend-line"></span> Cut</div>
                <div class="ops-legend-item leg-safe"><span class="ops-legend-line"></span> Safe</div>
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
            rows = `<tr><td colspan="5" class="ops-empty-pages"><i class="fa fa-file-o"></i>No pages yet. Click "Add Page" to create one.</td></tr>`;
        } else {
            pages.forEach((p, i) => {
                rows += `
                <tr data-row="${i}">
                    <td style="width:60px;text-align:center;color:#718096;">${i + 1}</td>
                    <td><input type="text" class="ops-pg-inp pg-name" value="${p.name || ''}" placeholder="e.g., Front"></td>
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
        if (!frm.fields_dict.products_draw_area_margins) {
            console.log('Fields not ready');
            return;
        }

        // Remove old
        $('#ops-viz-wrapper').remove();
        $('#ops-visualizer-styles').remove();

        const layoutHtml = this.current_layout === 'classic' ? this.renderClassic() : this.renderModern();

        const html = `
            ${this.getStyles()}
            <div class="ops-viz-wrapper" id="ops-viz-wrapper">
                <div class="ops-layout-switch">
                    <span class="switch-label">Layout:</span>
                    <div class="ops-switch-btns">
                        <button type="button" class="ops-switch-btn ${this.current_layout === 'classic' ? 'active' : ''}" data-lay="classic">
                            <i class="fa fa-th-large"></i> Classic
                        </button>
                        <button type="button" class="ops-switch-btn ${this.current_layout === 'modern' ? 'active' : ''}" data-lay="modern">
                            <i class="fa fa-cube"></i> Modern
                        </button>
                    </div>
                </div>
                <div id="ops-layout-area">${layoutHtml}</div>
                ${this.renderPages()}
            </div>
        `;

        $(frm.fields_dict.custom_size_section.wrapper).before(html);

        // Hide original fields
        $(frm.fields_dict.products_draw_area_margins.wrapper).hide();
        $(frm.fields_dict.products_draw_cutting_margins.wrapper).hide();
        $(frm.fields_dict.productpages.wrapper).hide();

        this.bindEvents();
        this.updateSvg();
    },

    bindEvents: function() {
        const me = this;
        const frm = this.frm;

        // Layout switch
        $('#ops-viz-wrapper').off('click', '.ops-switch-btn').on('click', '.ops-switch-btn', function() {
            const lay = $(this).data('lay');
            me.current_layout = lay;
            localStorage.setItem('ops_margin_layout', lay);

            $('.ops-switch-btn').removeClass('active');
            $(this).addClass('active');

            const newHtml = lay === 'classic' ? me.renderClassic() : me.renderModern();
            $('#ops-layout-area').html(newHtml);
            me.updateSvg();
        });

        // Margin inputs - use event delegation
        $('#ops-viz-wrapper').off('input', '.ops-m-inp').on('input', '.ops-m-inp', function() {
            const $inp = $(this);
            const t = $inp.data('t'); // cut or safe
            const d = $inp.data('d'); // top, right, bottom, left
            const val = parseFloat($inp.val()) || 0;

            // Sync all inputs with same t and d
            $(`.ops-m-inp[data-t="${t}"][data-d="${d}"]`).not(this).val(val);

            // Update frm
            const fld = t === 'cut' ? 'products_draw_cutting_margins' : 'products_draw_area_margins';
            const margins = me.parse_margins(frm.doc[fld]);
            margins[d] = val;
            frm.set_value(fld, me.to_json(margins));

            me.updateSvg();
        });

        // Add page
        $('#ops-viz-wrapper').off('click', '#ops-btn-add-page').on('click', '#ops-btn-add-page', function() {
            me.addPage();
        });

        // Delete page
        $('#ops-viz-wrapper').off('click', '.ops-del-page').on('click', '.ops-del-page', function() {
            me.deletePage($(this).data('row'));
        });

        // Page inputs
        $('#ops-viz-wrapper').off('input change', '.ops-pg-inp').on('input change', '.ops-pg-inp', function() {
            me.savePages();
        });
    },

    updateSvg: function() {
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);

        // For Classic: viewBox 180x160, base cut at 10,10 160x140
        // For Modern: viewBox 200x180, base cut at 30,30 140x120

        const scale = 40; // pixels per inch

        // Classic SVG (if present)
        if ($('.ops-classic .svg-cut-rect').length) {
            const cX = 10 + Math.abs(cut.left) * scale;
            const cY = 10 + Math.abs(cut.top) * scale;
            const cW = 160 - (Math.abs(cut.left) + Math.abs(cut.right)) * scale;
            const cH = 140 - (Math.abs(cut.top) + Math.abs(cut.bottom)) * scale;

            $('.ops-classic .svg-cut-rect').attr({
                x: Math.max(5, cX),
                y: Math.max(5, cY),
                width: Math.max(60, Math.min(cW, 170)),
                height: Math.max(50, Math.min(cH, 150))
            });

            const sX = cX + safe.left * scale;
            const sY = cY + safe.top * scale;
            const sW = cW - (safe.left + safe.right) * scale;
            const sH = cH - (safe.top + safe.bottom) * scale;

            $('.ops-classic .svg-safe-rect').attr({
                x: Math.max(15, sX),
                y: Math.max(15, sY),
                width: Math.max(40, Math.min(sW, 150)),
                height: Math.max(30, Math.min(sH, 130))
            });
        }

        // Modern SVG (if present)
        if ($('.ops-modern .svg-cut-rect').length) {
            const cX = 30 + Math.abs(cut.left) * scale;
            const cY = 30 + Math.abs(cut.top) * scale;
            const cW = 140 - (Math.abs(cut.left) + Math.abs(cut.right)) * scale;
            const cH = 120 - (Math.abs(cut.top) + Math.abs(cut.bottom)) * scale;

            $('.ops-modern .svg-cut-rect').attr({
                x: Math.max(25, cX),
                y: Math.max(25, cY),
                width: Math.max(60, Math.min(cW, 150)),
                height: Math.max(50, Math.min(cH, 130))
            });

            const sX = cX + safe.left * scale;
            const sY = cY + safe.top * scale;
            const sW = cW - (safe.left + safe.right) * scale;
            const sH = cH - (safe.top + safe.bottom) * scale;

            $('.ops-modern .svg-safe-rect').attr({
                x: Math.max(35, sX),
                y: Math.max(35, sY),
                width: Math.max(40, Math.min(sW, 130)),
                height: Math.max(30, Math.min(sH, 110))
            });
        }
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
        // Re-render pages section
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
        if (frm.doc.name) {
            ops_ziflow.margin_visualizer.init(frm);
        }
    },
    onload: function(frm) {
        if (frm.doc.name) {
            setTimeout(() => ops_ziflow.margin_visualizer.init(frm), 200);
        }
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
    return "v4 Done!"
