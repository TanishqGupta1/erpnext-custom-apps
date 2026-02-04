"""
Script to create the OPS Product Margin Visualizer Client Script v3
With dual layout options - Classic (OnPrintShop style) and Modern
Run with: bench --site erp.visualgraphx.com execute ops_ziflow.create_margin_visualizer_v3.create_client_script
"""
import frappe

def create_client_script():
    """Create or update the margin visualizer client script"""

    script_content = '''/**
 * OPS Product Margin Visualizer v3
 * Dual layout: Classic (OnPrintShop style) & Modern (Panel style)
 * With Product Pages table management
 */

frappe.provide('ops_ziflow');
frappe.provide('ops_ziflow.margin_visualizer');

ops_ziflow.margin_visualizer = {
    frm: null,
    layout: 'classic', // 'classic' or 'modern'

    init: function(frm) {
        if (!frm || !frm.doc) return;
        this.frm = frm;

        // Get saved layout preference
        this.layout = localStorage.getItem('ops_margin_layout') || 'classic';

        setTimeout(() => {
            this.render();
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

    get_styles: function() {
        return `
<style>
/* Common Styles */
.ops-visualizer-wrapper {
    margin-bottom: 20px;
}
.ops-layout-toggle {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px;
    color: white;
}
.ops-layout-toggle label {
    font-size: 13px;
    font-weight: 500;
    margin: 0;
}
.ops-layout-toggle .toggle-btns {
    display: flex;
    background: rgba(255,255,255,0.2);
    border-radius: 6px;
    padding: 3px;
}
.ops-layout-toggle .toggle-btn {
    padding: 6px 16px;
    border: none;
    background: transparent;
    color: rgba(255,255,255,0.8);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s;
}
.ops-layout-toggle .toggle-btn.active {
    background: white;
    color: #667eea;
}
.ops-layout-toggle .toggle-btn:hover:not(.active) {
    background: rgba(255,255,255,0.1);
}

/* ========== CLASSIC LAYOUT (OnPrintShop Style) ========== */
.ops-classic-layout {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 24px;
}
.ops-classic-layout .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid #4299e1;
}
.ops-classic-layout .section-header i {
    color: #4299e1;
    font-size: 16px;
}
.ops-classic-layout .section-header h3 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: #2d3748;
}
.ops-classic-layout .info-text {
    font-size: 12px;
    color: #718096;
    margin-bottom: 20px;
    line-height: 1.6;
}
.ops-classic-layout .info-text .green { color: #38a169; font-weight: 600; }
.ops-classic-layout .info-text .red { color: #e53e3e; font-weight: 600; }

.ops-classic-main {
    display: flex;
    gap: 30px;
    align-items: flex-start;
}
.ops-classic-diagram {
    flex: 0 0 auto;
}
.ops-classic-inputs-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* Diagram with inputs around it */
.ops-diagram-container {
    position: relative;
    width: 320px;
    padding: 50px 60px;
}
.ops-diagram-label {
    position: absolute;
    font-size: 11px;
    font-weight: 600;
    color: #4a5568;
}
.ops-diagram-label.top { top: 8px; left: 50%; transform: translateX(-50%); }
.ops-diagram-label.bottom { bottom: 8px; left: 50%; transform: translateX(-50%); }
.ops-diagram-label.left { left: 8px; top: 50%; transform: translateY(-50%) rotate(-90deg); }
.ops-diagram-label.right { right: 8px; top: 50%; transform: translateY(-50%) rotate(90deg); }

.ops-diagram-svg-wrap {
    position: relative;
    width: 200px;
    height: 180px;
    background: #fff;
    border: 1px solid #e2e8f0;
}
.ops-diagram-svg-wrap svg {
    width: 100%;
    height: 100%;
}

/* Input boxes around diagram */
.ops-diagram-input-box {
    position: absolute;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.ops-diagram-input-box.top-inputs {
    top: 50px;
    left: 60px;
    right: 60px;
    flex-direction: row;
    justify-content: center;
    gap: 8px;
}
.ops-diagram-input-box.bottom-inputs {
    bottom: 50px;
    left: 60px;
    right: 60px;
    flex-direction: row;
    justify-content: center;
    gap: 8px;
}
.ops-diagram-input-box.left-inputs {
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 55px;
}
.ops-diagram-input-box.right-inputs {
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 55px;
}

.ops-mini-input {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.ops-mini-input input {
    width: 55px;
    padding: 4px 6px;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    font-size: 12px;
    text-align: center;
    background: #fff;
}
.ops-mini-input input.cut-input {
    border-color: #fed7d7;
    background: #fff5f5;
}
.ops-mini-input input.cut-input:focus {
    border-color: #e53e3e;
    outline: none;
    box-shadow: 0 0 0 2px rgba(229,62,62,0.2);
}
.ops-mini-input input.safe-input {
    border-color: #c6f6d5;
    background: #f0fff4;
}
.ops-mini-input input.safe-input:focus {
    border-color: #38a169;
    outline: none;
    box-shadow: 0 0 0 2px rgba(56,161,105,0.2);
}
.ops-mini-input .input-label {
    font-size: 9px;
    color: #a0aec0;
    margin-top: 2px;
}

/* Legend */
.ops-classic-legend {
    display: flex;
    gap: 20px;
    margin-top: 12px;
    justify-content: center;
}
.ops-legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 500;
}
.ops-legend-line {
    width: 20px;
    height: 2px;
    border-top: 2px dashed;
}
.ops-legend-line.cut { border-color: #e53e3e; }
.ops-legend-line.safe { border-color: #38a169; }
.ops-legend-item.cut { color: #e53e3e; }
.ops-legend-item.safe { color: #38a169; }

/* Right side panels in classic */
.ops-margin-panel {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    border-left: 4px solid;
}
.ops-margin-panel.cut-panel { border-left-color: #e53e3e; }
.ops-margin-panel.safe-panel { border-left-color: #38a169; }
.ops-margin-panel h4 {
    margin: 0 0 12px 0;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
}
.ops-margin-panel.cut-panel h4 { color: #e53e3e; }
.ops-margin-panel.safe-panel h4 { color: #38a169; }
.ops-margin-panel .panel-line {
    width: 20px;
    height: 3px;
    border-radius: 2px;
}
.ops-margin-panel.cut-panel .panel-line { background: #e53e3e; }
.ops-margin-panel.safe-panel .panel-line { background: #38a169; }

.ops-panel-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}
.ops-panel-input label {
    display: block;
    font-size: 11px;
    color: #718096;
    margin-bottom: 4px;
}
.ops-panel-input input {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    font-size: 13px;
}
.ops-panel-input input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}

/* ========== MODERN LAYOUT ========== */
.ops-modern-layout {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    border-radius: 12px;
    padding: 24px;
}
.ops-modern-header {
    text-align: center;
    margin-bottom: 20px;
}
.ops-modern-header h3 {
    margin: 0 0 8px 0;
    font-size: 18px;
    font-weight: 700;
    color: #2d3748;
}
.ops-modern-header p {
    margin: 0;
    font-size: 12px;
    color: #718096;
}

.ops-modern-main {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    align-items: start;
}

.ops-modern-svg-container {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.ops-modern-svg-wrap {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}
.ops-modern-svg-wrap svg {
    width: 220px;
    height: 200px;
}

.ops-modern-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}
.ops-modern-card.cut-card {
    border-top: 4px solid #e53e3e;
}
.ops-modern-card.safe-card {
    border-top: 4px solid #38a169;
}
.ops-modern-card h4 {
    margin: 0 0 16px 0;
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
}
.ops-modern-card.cut-card h4 { color: #e53e3e; }
.ops-modern-card.safe-card h4 { color: #38a169; }
.ops-modern-card .card-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.ops-modern-card.cut-card .card-icon { background: #fed7d7; color: #e53e3e; }
.ops-modern-card.safe-card .card-icon { background: #c6f6d5; color: #38a169; }

.ops-modern-inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.ops-modern-input label {
    display: block;
    font-size: 11px;
    color: #a0aec0;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.ops-modern-input input {
    width: 100%;
    padding: 10px 12px;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
}
.ops-modern-card.cut-card .ops-modern-input input:focus {
    border-color: #e53e3e;
    outline: none;
    box-shadow: 0 0 0 4px rgba(229,62,62,0.1);
}
.ops-modern-card.safe-card .ops-modern-input input:focus {
    border-color: #38a169;
    outline: none;
    box-shadow: 0 0 0 4px rgba(56,161,105,0.1);
}

/* ========== PRODUCT PAGES TABLE ========== */
.ops-pages-section {
    margin-top: 24px;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
}
.ops-pages-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
    color: white;
}
.ops-pages-header h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
}
.ops-add-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: rgba(255,255,255,0.2);
    color: white;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}
.ops-add-btn:hover {
    background: rgba(255,255,255,0.3);
}
.ops-pages-info {
    padding: 12px 20px;
    background: #f7fafc;
    font-size: 11px;
    color: #718096;
    border-bottom: 1px solid #e2e8f0;
}
.ops-pages-table {
    width: 100%;
    border-collapse: collapse;
}
.ops-pages-table th {
    background: #edf2f7;
    padding: 12px 16px;
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.ops-pages-table td {
    padding: 12px 16px;
    border-bottom: 1px solid #edf2f7;
    font-size: 13px;
}
.ops-pages-table tr:hover td {
    background: #f7fafc;
}
.ops-pages-table input[type="text"],
.ops-pages-table input[type="number"] {
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 13px;
    transition: border-color 0.2s;
}
.ops-pages-table input[type="text"] { width: 100%; }
.ops-pages-table input[type="number"] { width: 70px; text-align: center; }
.ops-pages-table input:focus {
    outline: none;
    border-color: #4299e1;
    box-shadow: 0 0 0 3px rgba(66,153,225,0.15);
}

/* Toggle Switch */
.ops-toggle {
    position: relative;
    width: 48px;
    height: 26px;
}
.ops-toggle input {
    opacity: 0;
    width: 0;
    height: 0;
}
.ops-toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: #cbd5e0;
    border-radius: 26px;
    transition: 0.3s;
}
.ops-toggle-slider:before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 3px;
    bottom: 3px;
    background: white;
    border-radius: 50%;
    transition: 0.3s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.ops-toggle input:checked + .ops-toggle-slider {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}
.ops-toggle input:checked + .ops-toggle-slider:before {
    transform: translateX(22px);
}

.ops-delete-btn {
    color: #e53e3e;
    background: #fed7d7;
    border: none;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
}
.ops-delete-btn:hover {
    background: #e53e3e;
    color: white;
}
.ops-no-pages {
    padding: 40px;
    text-align: center;
    color: #a0aec0;
}
.ops-no-pages i {
    font-size: 32px;
    margin-bottom: 12px;
    display: block;
}

/* Responsive */
@media (max-width: 992px) {
    .ops-modern-main {
        grid-template-columns: 1fr;
    }
    .ops-classic-main {
        flex-direction: column;
    }
}
</style>
        `;
    },

    get_classic_layout: function() {
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);

        return `
<div class="ops-classic-layout">
    <div class="section-header">
        <i class="fa fa-crop"></i>
        <h3>Setup Product Margin (Inch)</h3>
    </div>
    <div class="info-text">
        All margins i.e. top, right, bottom, and left are used to set the safe margin
        (<span class="green">Green Line</span>) and cut or trim margin
        (<span class="red">Red Line</span>) in the designer studio.
        <strong>Note:</strong> Margins are included in the product bleed size (width & height).
    </div>

    <div class="ops-classic-main">
        <div class="ops-classic-diagram">
            <div class="ops-diagram-container">
                <div class="ops-diagram-label top">Top</div>
                <div class="ops-diagram-label bottom">Bottom</div>
                <div class="ops-diagram-label left">Left</div>
                <div class="ops-diagram-label right">Right</div>

                <!-- Top inputs -->
                <div class="ops-diagram-input-box top-inputs">
                    <div class="ops-mini-input">
                        <input type="number" step="0.0001" class="cut-input ops-margin-input" data-type="cut" data-dir="top" value="${cut.top}">
                        <span class="input-label">Cut</span>
                    </div>
                    <div class="ops-mini-input">
                        <input type="number" step="0.0001" class="safe-input ops-margin-input" data-type="safe" data-dir="top" value="${safe.top}">
                        <span class="input-label">Safe</span>
                    </div>
                </div>

                <!-- Bottom inputs -->
                <div class="ops-diagram-input-box bottom-inputs">
                    <div class="ops-mini-input">
                        <input type="number" step="0.0001" class="safe-input ops-margin-input" data-type="safe" data-dir="bottom" value="${safe.bottom}">
                        <span class="input-label">Safe</span>
                    </div>
                    <div class="ops-mini-input">
                        <input type="number" step="0.0001" class="cut-input ops-margin-input" data-type="cut" data-dir="bottom" value="${cut.bottom}">
                        <span class="input-label">Cut</span>
                    </div>
                </div>

                <!-- Left inputs -->
                <div class="ops-diagram-input-box left-inputs">
                    <div class="ops-mini-input">
                        <input type="number" step="0.0001" class="cut-input ops-margin-input" data-type="cut" data-dir="left" value="${cut.left}">
                        <span class="input-label">Cut</span>
                    </div>
                    <div class="ops-mini-input">
                        <input type="number" step="0.0001" class="safe-input ops-margin-input" data-type="safe" data-dir="left" value="${safe.left}">
                        <span class="input-label">Safe</span>
                    </div>
                </div>

                <!-- Right inputs -->
                <div class="ops-diagram-input-box right-inputs">
                    <div class="ops-mini-input">
                        <input type="number" step="0.0001" class="safe-input ops-margin-input" data-type="safe" data-dir="right" value="${safe.right}">
                        <span class="input-label">Safe</span>
                    </div>
                    <div class="ops-mini-input">
                        <input type="number" step="0.0001" class="cut-input ops-margin-input" data-type="cut" data-dir="right" value="${cut.right}">
                        <span class="input-label">Cut</span>
                    </div>
                </div>

                <!-- SVG Diagram -->
                <div class="ops-diagram-svg-wrap">
                    <svg viewBox="0 0 200 180">
                        <rect x="10" y="10" width="180" height="160" fill="none" stroke="#e53e3e" stroke-width="2" stroke-dasharray="6,4" class="ops-cut-rect"/>
                        <rect x="25" y="25" width="150" height="130" fill="none" stroke="#38a169" stroke-width="2" stroke-dasharray="6,4" class="ops-safe-rect"/>
                    </svg>
                </div>
            </div>

            <div class="ops-classic-legend">
                <div class="ops-legend-item cut">
                    <span class="ops-legend-line cut"></span> Cut Margin
                </div>
                <div class="ops-legend-item safe">
                    <span class="ops-legend-line safe"></span> Safe Margin
                </div>
            </div>
        </div>

        <div class="ops-classic-inputs-panel">
            <div class="ops-margin-panel cut-panel">
                <h4><span class="panel-line"></span> Cut/Bleed Margin</h4>
                <div class="ops-panel-grid">
                    <div class="ops-panel-input">
                        <label>Top</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="top" value="${cut.top}">
                    </div>
                    <div class="ops-panel-input">
                        <label>Right</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="right" value="${cut.right}">
                    </div>
                    <div class="ops-panel-input">
                        <label>Bottom</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="bottom" value="${cut.bottom}">
                    </div>
                    <div class="ops-panel-input">
                        <label>Left</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="left" value="${cut.left}">
                    </div>
                </div>
            </div>

            <div class="ops-margin-panel safe-panel">
                <h4><span class="panel-line"></span> Safe/Draw Area Margin</h4>
                <div class="ops-panel-grid">
                    <div class="ops-panel-input">
                        <label>Top</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="top" value="${safe.top}">
                    </div>
                    <div class="ops-panel-input">
                        <label>Right</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="right" value="${safe.right}">
                    </div>
                    <div class="ops-panel-input">
                        <label>Bottom</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="bottom" value="${safe.bottom}">
                    </div>
                    <div class="ops-panel-input">
                        <label>Left</label>
                        <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="left" value="${safe.left}">
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
        `;
    },

    get_modern_layout: function() {
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);

        return `
<div class="ops-modern-layout">
    <div class="ops-modern-header">
        <h3>Setup Product Margin</h3>
        <p>Configure cut/bleed and safe margins for the designer studio (values in inches)</p>
    </div>

    <div class="ops-modern-main">
        <div class="ops-modern-card cut-card">
            <h4>
                <span class="card-icon"><i class="fa fa-scissors"></i></span>
                Cut/Bleed Margin
            </h4>
            <div class="ops-modern-inputs">
                <div class="ops-modern-input">
                    <label>Top</label>
                    <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="top" value="${cut.top}">
                </div>
                <div class="ops-modern-input">
                    <label>Right</label>
                    <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="right" value="${cut.right}">
                </div>
                <div class="ops-modern-input">
                    <label>Bottom</label>
                    <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="bottom" value="${cut.bottom}">
                </div>
                <div class="ops-modern-input">
                    <label>Left</label>
                    <input type="number" step="0.0001" class="ops-margin-input" data-type="cut" data-dir="left" value="${cut.left}">
                </div>
            </div>
        </div>

        <div class="ops-modern-svg-container">
            <div class="ops-modern-svg-wrap">
                <svg viewBox="0 0 220 200">
                    <text x="110" y="15" fill="#4a5568" font-size="11" font-weight="600" text-anchor="middle">Top</text>
                    <text x="110" y="195" fill="#4a5568" font-size="11" font-weight="600" text-anchor="middle">Bottom</text>
                    <text x="10" y="100" fill="#4a5568" font-size="11" font-weight="600" text-anchor="middle" transform="rotate(-90,10,100)">Left</text>
                    <text x="210" y="100" fill="#4a5568" font-size="11" font-weight="600" text-anchor="middle" transform="rotate(90,210,100)">Right</text>

                    <rect x="25" y="25" width="170" height="150" fill="#fff" stroke="#e2e8f0" stroke-width="1"/>
                    <rect x="35" y="35" width="150" height="130" fill="none" stroke="#e53e3e" stroke-width="2" stroke-dasharray="6,4" class="ops-cut-rect"/>
                    <rect x="50" y="50" width="120" height="100" fill="none" stroke="#38a169" stroke-width="2" stroke-dasharray="6,4" class="ops-safe-rect"/>

                    <!-- Legend -->
                    <line x1="50" y1="180" x2="70" y2="180" stroke="#e53e3e" stroke-width="2" stroke-dasharray="4,2"/>
                    <text x="75" y="183" fill="#e53e3e" font-size="9">Cut</text>
                    <line x1="110" y1="180" x2="130" y2="180" stroke="#38a169" stroke-width="2" stroke-dasharray="4,2"/>
                    <text x="135" y="183" fill="#38a169" font-size="9">Safe</text>
                </svg>
            </div>
        </div>

        <div class="ops-modern-card safe-card">
            <h4>
                <span class="card-icon"><i class="fa fa-shield"></i></span>
                Safe/Draw Area Margin
            </h4>
            <div class="ops-modern-inputs">
                <div class="ops-modern-input">
                    <label>Top</label>
                    <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="top" value="${safe.top}">
                </div>
                <div class="ops-modern-input">
                    <label>Right</label>
                    <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="right" value="${safe.right}">
                </div>
                <div class="ops-modern-input">
                    <label>Bottom</label>
                    <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="bottom" value="${safe.bottom}">
                </div>
                <div class="ops-modern-input">
                    <label>Left</label>
                    <input type="number" step="0.0001" class="ops-margin-input" data-type="safe" data-dir="left" value="${safe.left}">
                </div>
            </div>
        </div>
    </div>
</div>
        `;
    },

    get_pages_section: function() {
        const pages = this.get_pages();
        let rows = '';

        if (pages.length === 0) {
            rows = '<tr><td colspan="5" class="ops-no-pages"><i class="fa fa-file-o"></i>No pages configured. Click "Add Page" to add one.</td></tr>';
        } else {
            pages.forEach((page, idx) => {
                rows += `
                    <tr data-idx="${idx}">
                        <td style="width:50px; text-align:center; color:#718096;">${idx + 1}</td>
                        <td><input type="text" class="ops-page-input page-name" value="${page.name || ''}" placeholder="e.g., Front, Back"></td>
                        <td style="width:90px;"><input type="number" class="ops-page-input page-sort" value="${page.sort || idx + 1}" min="1"></td>
                        <td style="width:70px;">
                            <label class="ops-toggle">
                                <input type="checkbox" class="ops-page-input page-active" ${page.active !== false ? 'checked' : ''}>
                                <span class="ops-toggle-slider"></span>
                            </label>
                        </td>
                        <td style="width:60px;">
                            <button type="button" class="ops-delete-btn ops-delete-page" data-idx="${idx}">
                                <i class="fa fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            });
        }

        return `
<div class="ops-pages-section">
    <div class="ops-pages-header">
        <h4><i class="fa fa-files-o"></i> Setup Product Pages</h4>
        <button type="button" class="ops-add-btn" id="ops-add-page">
            <i class="fa fa-plus"></i> Add Page
        </button>
    </div>
    <div class="ops-pages-info">
        <i class="fa fa-info-circle"></i> Special characters like SPACE, &, ', ., /, <, >, COMMA(,) are not allowed. Page name should not start with a number.
    </div>
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
            ${rows}
        </tbody>
    </table>
</div>
        `;
    },

    render: function() {
        const me = this;
        const frm = this.frm;

        if (!frm.fields_dict.products_draw_area_margins) return;

        // Build HTML
        const html = `
            ${this.get_styles()}
            <div class="ops-visualizer-wrapper" id="ops-visualizer">
                <div class="ops-layout-toggle">
                    <label>Layout Style:</label>
                    <div class="toggle-btns">
                        <button type="button" class="toggle-btn ${this.layout === 'classic' ? 'active' : ''}" data-layout="classic">
                            <i class="fa fa-th-large"></i> Classic
                        </button>
                        <button type="button" class="toggle-btn ${this.layout === 'modern' ? 'active' : ''}" data-layout="modern">
                            <i class="fa fa-cube"></i> Modern
                        </button>
                    </div>
                </div>
                <div id="ops-layout-container">
                    ${this.layout === 'classic' ? this.get_classic_layout() : this.get_modern_layout()}
                </div>
                ${this.get_pages_section()}
            </div>
        `;

        // Remove existing and insert new
        $('#ops-visualizer').remove();
        $(frm.fields_dict.custom_size_section.wrapper).before(html);

        // Hide original fields
        $(frm.fields_dict.products_draw_area_margins.wrapper).hide();
        $(frm.fields_dict.products_draw_cutting_margins.wrapper).hide();
        $(frm.fields_dict.productpages.wrapper).hide();

        // Bind events
        this.bind_events();
    },

    bind_events: function() {
        const me = this;
        const frm = this.frm;
        const $wrapper = $('#ops-visualizer');

        // Layout toggle
        $wrapper.off('click', '.toggle-btn').on('click', '.toggle-btn', function() {
            const layout = $(this).data('layout');
            me.layout = layout;
            localStorage.setItem('ops_margin_layout', layout);

            $('.toggle-btn').removeClass('active');
            $(this).addClass('active');

            $('#ops-layout-container').html(
                layout === 'classic' ? me.get_classic_layout() : me.get_modern_layout()
            );
        });

        // Margin inputs
        $wrapper.off('input', '.ops-margin-input').on('input', '.ops-margin-input', function() {
            const $input = $(this);
            const type = $input.data('type');
            const dir = $input.data('dir');
            const value = parseFloat($input.val()) || 0;

            // Update all inputs with same type and direction
            $(`.ops-margin-input[data-type="${type}"][data-dir="${dir}"]`).val(value);

            const field = type === 'cut' ? 'products_draw_cutting_margins' : 'products_draw_area_margins';
            const current = me.parse_margins(frm.doc[field]);
            current[dir] = value;
            frm.set_value(field, me.to_json(current));

            me.update_svg();
        });

        // Add page
        $wrapper.off('click', '#ops-add-page').on('click', '#ops-add-page', function() {
            me.add_page();
        });

        // Delete page
        $wrapper.off('click', '.ops-delete-page').on('click', '.ops-delete-page', function() {
            me.delete_page($(this).data('idx'));
        });

        // Page inputs
        $wrapper.off('input change', '.ops-page-input').on('input change', '.ops-page-input', function() {
            me.save_pages();
        });
    },

    update_svg: function() {
        const safe = this.parse_margins(this.frm.doc.products_draw_area_margins);
        const cut = this.parse_margins(this.frm.doc.products_draw_cutting_margins);
        const scale = 50;

        // Update cut rect
        const cutX = 10 + Math.abs(cut.left) * scale;
        const cutY = 10 + Math.abs(cut.top) * scale;
        const cutW = 180 - (Math.abs(cut.left) + Math.abs(cut.right)) * scale;
        const cutH = 160 - (Math.abs(cut.top) + Math.abs(cut.bottom)) * scale;

        $('.ops-cut-rect').attr({
            x: Math.max(5, Math.min(cutX, 50)),
            y: Math.max(5, Math.min(cutY, 50)),
            width: Math.max(100, Math.min(cutW, 190)),
            height: Math.max(80, Math.min(cutH, 170))
        });

        // Update safe rect
        const safeX = cutX + safe.left * scale;
        const safeY = cutY + safe.top * scale;
        const safeW = cutW - (safe.left + safe.right) * scale;
        const safeH = cutH - (safe.top + safe.bottom) * scale;

        $('.ops-safe-rect').attr({
            x: Math.max(15, Math.min(safeX, 70)),
            y: Math.max(15, Math.min(safeY, 70)),
            width: Math.max(60, Math.min(safeW, 160)),
            height: Math.max(50, Math.min(safeH, 140))
        });
    },

    get_pages: function() {
        const json = this.frm.doc.custom_size_info;
        if (!json || json === 'null') return [];
        try {
            const arr = JSON.parse(json);
            return Array.isArray(arr) ? arr : [];
        } catch (e) { return []; }
    },

    save_pages: function() {
        const pages = [];
        $('.ops-pages-table tbody tr[data-idx]').each(function() {
            pages.push({
                name: $(this).find('.page-name').val() || '',
                sort: parseInt($(this).find('.page-sort').val()) || 1,
                active: $(this).find('.page-active').is(':checked')
            });
        });
        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
    },

    add_page: function() {
        const pages = this.get_pages();
        pages.push({ name: '', sort: pages.length + 1, active: true });
        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
        this.render();
    },

    delete_page: function(idx) {
        const pages = this.get_pages();
        pages.splice(idx, 1);
        pages.forEach((p, i) => p.sort = i + 1);
        this.frm.set_value('custom_size_info', JSON.stringify(pages));
        this.frm.set_value('productpages', pages.length);
        this.render();
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
        if (frm.doc.name) {
            setTimeout(() => ops_ziflow.margin_visualizer.init(frm), 300);
        }
    }
});
'''

    # Update or create
    existing = frappe.db.get_value("Client Script", {"dt": "OPS Product"}, "name")

    if existing:
        doc = frappe.get_doc("Client Script", existing)
        doc.script = script_content
        doc.enabled = 1
        doc.save()
        print(f"Updated Client Script: {existing}")
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
        print(f"Created Client Script: {doc.name}")

    frappe.db.commit()
    return "Done!"
