/**
 * OPS Order Redirect - Redirects form view to custom page view
 */
(function() {
    // Check if we're on an OPS Order form page
    frappe.router.on('change', function() {
        const route = frappe.get_route();
        if (route && route[0] === 'Form' && route[1] === 'OPS Order' && route[2]) {
            const orderName = route[2];
            // Redirect to the custom order view page
            setTimeout(function() {
                frappe.set_route('ops-order-view', orderName);
            }, 100);
        }
    });
})();
