/**
 * OPS Vue Dashboard - Modern Vue 3 + Frappe UI Dashboard
 */

frappe.pages['ops-vue-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'OPS Dashboard (Vue)',
        single_column: true
    });

    // Store page reference
    wrapper.page = page;

    // Add navigation menu items
    page.add_menu_item(__('Classic Dashboard'), function() {
        frappe.set_route('ops-cluster-dashboard');
    });
    page.add_menu_item(__('Orders Dashboard'), function() {
        frappe.set_route('ops-orders-dashboard');
    });
    page.add_menu_item(__('Quotes Dashboard'), function() {
        frappe.set_route('ops-quotes-dashboard');
    });
    page.add_menu_item(__('ZiFlow Dashboard'), function() {
        frappe.set_route('ziflow-dashboard');
    });

    // Add the Vue mount point to the page
    $(page.main).html('<div id="ops-cluster-dashboard-vue" style="min-height: 400px;"><div style="display:flex;align-items:center;justify-content:center;height:400px;"><div>Loading Vue Dashboard...</div></div></div>');

    // Load the Vue bundle and CSS
    frappe.require([
        '/assets/ops_ziflow/frontend/style.css',
        '/assets/ops_ziflow/frontend/cluster-dashboard.bundle.js'
    ], function() {
        console.log('Vue assets loaded');
        // Trigger mount if the function exists
        if (window.mountOPSDashboard) {
            window.mountOPSDashboard();
        }
    });
};

frappe.pages['ops-vue-dashboard'].on_page_show = function(wrapper) {
    // Re-mount if needed when page is shown again
    if (window.mountOPSDashboard) {
        setTimeout(function() {
            window.mountOPSDashboard();
        }, 50);
    }
};
