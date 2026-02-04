/**
 * OPS Product Margin Visualizer
 * A visual editor for product cut/safe margins similar to OnPrintShop's designer
 */

frappe.provide('ops_ziflow.margin_visualizer');

ops_ziflow.margin_visualizer = {
    /**
     * Initialize the margin visualizer for OPS Product form
     * @param {Object} frm - Frappe form object
     */
    init: function(frm) {
        this.frm = frm;
        this.render_visualizer();
        this.bind_events();
    },

    /**
     * Parse JSON margin string to object
     * @param {string} json_str - JSON string like {"top":".125","bottom":".125",...}
     * @returns {Object} Parsed margin object with numeric values
     */
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

    /**
     * Convert margin object to JSON string
     * @param {Object} margins - Margin object {top, bottom, left, right}
     * @returns {string} JSON string
     */
    to_json: function(margins) {
        return JSON.stringify({
            top: margins.top.toString(),
            bottom: margins.bottom.toString(),
            left: margins.left.toString(),
            right: margins.right.toString()
        });
    },

    /**
     * Render the visual margin editor
     */
    render_visualizer: function() {
        const me = this;
        const frm = this.frm;

        // Get current margin values
        const safe_margins = this.parse_margins(frm.doc.products_draw_area_margins);
        const cut_margins = this.parse_margins(frm.doc.products_draw_cutting_margins);

        // Create the visualizer HTML
        const visualizer_html = `
            <div class="margin-visualizer-container" style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef;">
                <div class="row">
                    <!-- Left side: Visual diagram -->
                    <div class="col-md-6">
                        <h6 style="color: #333; margin-bottom: 15px; font-weight: 600;">
                            <i class="fa fa-th-large"></i> Setup Product Margin (Inch)
                        </h6>
                        <div class="margin-info" style="font-size: 12px; color: #666; margin-bottom: 15px; padding: 10px; background: #fff; border-radius: 4px; border-left: 3px solid #5e64ff;">
                            All margins i.e. top, right, bottom, and left are used to set the safe margin
                            (<span style="color: #28a745; font-weight: bold;">Green Line</span>) and cut or trim margin
                            (<span style="color: #dc3545; font-weight: bold;">Red Line</span>) in the designer studio.<br>
                            <strong>Note:</strong> Margins are included in the product bleed size (width & height).
                        </div>

                        <div class="margin-diagram" style="position: relative; width: 100%; max-width: 400px; margin: 0 auto;">
                            <!-- SVG Visualization -->
                            <svg viewBox="0 0 300 250" style="width: 100%; height: auto; display: block;">
                                <!-- Outer product area (white background) -->
                                <rect x="50" y="30" width="200" height="190" fill="white" stroke="#ccc" stroke-width="1"/>

                                <!-- Cut margin rectangle (red dashed) -->
                                <rect x="60" y="40" width="180" height="170" fill="none" stroke="#dc3545" stroke-width="2" stroke-dasharray="5,3" class="cut-margin-rect"/>

                                <!-- Safe margin rectangle (green dashed) -->
                                <rect x="80" y="60" width="140" height="130" fill="none" stroke="#28a745" stroke-width="2" stroke-dasharray="5,3" class="safe-margin-rect"/>

                                <!-- Labels -->
                                <text x="25" y="130" fill="#dc3545" font-size="10" font-weight="bold" text-anchor="end">Cut Margin</text>

                                <!-- Direction labels -->
                                <text x="150" y="20" fill="#333" font-size="11" font-weight="bold" text-anchor="middle">Top</text>
                                <text x="150" y="245" fill="#333" font-size="11" font-weight="bold" text-anchor="middle">Bottom</text>
                                <text x="15" y="130" fill="#333" font-size="11" font-weight="bold" text-anchor="middle" transform="rotate(-90, 15, 130)">Left</text>
                                <text x="285" y="130" fill="#333" font-size="11" font-weight="bold" text-anchor="middle" transform="rotate(90, 285, 130)">Right</text>
                            </svg>
                        </div>
                    </div>

                    <!-- Right side: Input fields -->
                    <div class="col-md-6">
                        <div class="margin-inputs" style="padding: 10px;">
                            <!-- Cut Margins Section -->
                            <div class="margin-section" style="margin-bottom: 20px; padding: 15px; background: #fff; border-radius: 6px; border: 1px solid #dc354533;">
                                <h6 style="color: #dc3545; margin-bottom: 12px; font-weight: 600; display: flex; align-items: center;">
                                    <span style="display: inline-block; width: 20px; height: 3px; background: #dc3545; margin-right: 8px; border-radius: 2px;"></span>
                                    Cut/Bleed Margin
                                </h6>
                                <div class="row">
                                    <div class="col-6">
                                        <div class="form-group">
                                            <label class="control-label" style="font-size: 11px; color: #666;">Top</label>
                                            <input type="number" step="0.0001" class="form-control margin-input"
                                                   data-type="cut" data-direction="top"
                                                   value="${cut_margins.top}"
                                                   style="border-color: #dc354566;">
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="form-group">
                                            <label class="control-label" style="font-size: 11px; color: #666;">Right</label>
                                            <input type="number" step="0.0001" class="form-control margin-input"
                                                   data-type="cut" data-direction="right"
                                                   value="${cut_margins.right}"
                                                   style="border-color: #dc354566;">
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="form-group">
                                            <label class="control-label" style="font-size: 11px; color: #666;">Bottom</label>
                                            <input type="number" step="0.0001" class="form-control margin-input"
                                                   data-type="cut" data-direction="bottom"
                                                   value="${cut_margins.bottom}"
                                                   style="border-color: #dc354566;">
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="form-group">
                                            <label class="control-label" style="font-size: 11px; color: #666;">Left</label>
                                            <input type="number" step="0.0001" class="form-control margin-input"
                                                   data-type="cut" data-direction="left"
                                                   value="${cut_margins.left}"
                                                   style="border-color: #dc354566;">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Safe Margins Section -->
                            <div class="margin-section" style="padding: 15px; background: #fff; border-radius: 6px; border: 1px solid #28a74533;">
                                <h6 style="color: #28a745; margin-bottom: 12px; font-weight: 600; display: flex; align-items: center;">
                                    <span style="display: inline-block; width: 20px; height: 3px; background: #28a745; margin-right: 8px; border-radius: 2px;"></span>
                                    Safe/Draw Area Margin
                                </h6>
                                <div class="row">
                                    <div class="col-6">
                                        <div class="form-group">
                                            <label class="control-label" style="font-size: 11px; color: #666;">Top</label>
                                            <input type="number" step="0.0001" class="form-control margin-input"
                                                   data-type="safe" data-direction="top"
                                                   value="${safe_margins.top}"
                                                   style="border-color: #28a74566;">
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="form-group">
                                            <label class="control-label" style="font-size: 11px; color: #666;">Right</label>
                                            <input type="number" step="0.0001" class="form-control margin-input"
                                                   data-type="safe" data-direction="right"
                                                   value="${safe_margins.right}"
                                                   style="border-color: #28a74566;">
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="form-group">
                                            <label class="control-label" style="font-size: 11px; color: #666;">Bottom</label>
                                            <input type="number" step="0.0001" class="form-control margin-input"
                                                   data-type="safe" data-direction="bottom"
                                                   value="${safe_margins.bottom}"
                                                   style="border-color: #28a74566;">
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="form-group">
                                            <label class="control-label" style="font-size: 11px; color: #666;">Left</label>
                                            <input type="number" step="0.0001" class="form-control margin-input"
                                                   data-type="safe" data-direction="left"
                                                   value="${safe_margins.left}"
                                                   style="border-color: #28a74566;">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Find the Design Settings section and inject the visualizer
        const $wrapper = $(frm.fields_dict.products_draw_area_margins.wrapper);

        // Remove any existing visualizer
        $('.margin-visualizer-container').remove();

        // Insert visualizer before the original fields
        $wrapper.closest('.frappe-control').before(visualizer_html);

        // Hide the original JSON fields (they'll be updated programmatically)
        $(frm.fields_dict.products_draw_area_margins.wrapper).hide();
        $(frm.fields_dict.products_draw_cutting_margins.wrapper).hide();
    },

    /**
     * Bind events to input fields
     */
    bind_events: function() {
        const me = this;
        const frm = this.frm;

        // Handle input changes
        $('.margin-visualizer-container').on('input change', '.margin-input', function() {
            const $input = $(this);
            const type = $input.data('type'); // 'cut' or 'safe'
            const direction = $input.data('direction'); // 'top', 'bottom', 'left', 'right'
            const value = parseFloat($input.val()) || 0;

            // Get current margins
            const field_name = type === 'cut' ? 'products_draw_cutting_margins' : 'products_draw_area_margins';
            const current_margins = me.parse_margins(frm.doc[field_name]);

            // Update the specific direction
            current_margins[direction] = value;

            // Update the form field
            frm.set_value(field_name, me.to_json(current_margins));

            // Update SVG visualization
            me.update_svg_visualization();
        });
    },

    /**
     * Update the SVG visualization based on current margin values
     */
    update_svg_visualization: function() {
        const safe_margins = this.parse_margins(this.frm.doc.products_draw_area_margins);
        const cut_margins = this.parse_margins(this.frm.doc.products_draw_cutting_margins);

        // Base dimensions
        const base_x = 50, base_y = 30;
        const base_width = 200, base_height = 190;

        // Scale factor for visualization (1 inch = ~80px for display)
        const scale = 80;

        // Calculate cut margin rectangle
        const cut_rect = {
            x: base_x + (Math.abs(cut_margins.left) * scale),
            y: base_y + (Math.abs(cut_margins.top) * scale),
            width: base_width - ((Math.abs(cut_margins.left) + Math.abs(cut_margins.right)) * scale),
            height: base_height - ((Math.abs(cut_margins.top) + Math.abs(cut_margins.bottom)) * scale)
        };

        // Calculate safe margin rectangle (inside cut margin)
        const safe_rect = {
            x: cut_rect.x + (safe_margins.left * scale),
            y: cut_rect.y + (safe_margins.top * scale),
            width: cut_rect.width - ((safe_margins.left + safe_margins.right) * scale),
            height: cut_rect.height - ((safe_margins.top + safe_margins.bottom) * scale)
        };

        // Ensure minimum sizes
        cut_rect.width = Math.max(cut_rect.width, 40);
        cut_rect.height = Math.max(cut_rect.height, 40);
        safe_rect.width = Math.max(safe_rect.width, 20);
        safe_rect.height = Math.max(safe_rect.height, 20);

        // Update SVG elements
        $('.cut-margin-rect').attr({
            x: Math.max(cut_rect.x, 55),
            y: Math.max(cut_rect.y, 35),
            width: Math.min(cut_rect.width, 190),
            height: Math.min(cut_rect.height, 180)
        });

        $('.safe-margin-rect').attr({
            x: Math.max(safe_rect.x, 60),
            y: Math.max(safe_rect.y, 40),
            width: Math.min(safe_rect.width, 180),
            height: Math.min(safe_rect.height, 170)
        });
    },

    /**
     * Refresh visualizer with current form values
     */
    refresh: function() {
        this.render_visualizer();
        this.bind_events();
    }
};
