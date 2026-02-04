/**
 * OPS Product Form Client Script
 * Handles margin visualizer and other form enhancements
 */

frappe.ui.form.on('OPS Product', {
    refresh: function(frm) {
        // Initialize margin visualizer when Design Settings tab is shown
        if (frm.doc.name) {
            ops_ziflow.margin_visualizer.init(frm);
        }
    },

    onload: function(frm) {
        // Ensure visualizer is ready when form loads
        if (frm.doc.name) {
            setTimeout(() => {
                ops_ziflow.margin_visualizer.init(frm);
            }, 500);
        }
    },

    products_draw_area_margins: function(frm) {
        // Re-render visualizer when field changes externally
        if (frm.doc.name && !frm._skip_visualizer_update) {
            ops_ziflow.margin_visualizer.refresh();
        }
    },

    products_draw_cutting_margins: function(frm) {
        // Re-render visualizer when field changes externally
        if (frm.doc.name && !frm._skip_visualizer_update) {
            ops_ziflow.margin_visualizer.refresh();
        }
    }
});
