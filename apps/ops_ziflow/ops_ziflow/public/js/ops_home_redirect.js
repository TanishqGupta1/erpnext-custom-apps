/**
 * OPS Home Redirect
 * Redirects root and home routes to OPS Cluster Dashboard
 */

// Immediate redirect for root URL - runs before frappe loads
(function immediateRedirect() {
    var path = window.location.pathname;

    // If at root or /app without specific route, redirect immediately
    if (path === '/' || path === '' || path === '/app' || path === '/app/') {
        // Check if user appears logged in (has sid cookie that's not Guest)
        var cookies = document.cookie;
        if (cookies.indexOf('sid=') !== -1 && cookies.indexOf('sid=Guest') === -1) {
            window.location.replace('/app/ops-cluster-dashboard');
            return;
        }
    }

    // Handle /app/home routes
    if (path === '/app/home' || path === '/app/Home') {
        window.location.replace('/app/ops-cluster-dashboard');
        return;
    }
})();

(function() {
    'use strict';

    if (typeof frappe === 'undefined') return;

    const OPS_DASHBOARD_ROUTE = 'ops-cluster-dashboard';

    function redirect_to_dashboard(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
        }
        frappe.set_route(OPS_DASHBOARD_ROUTE);
        return false;
    }

    function setup_ops_home_redirect() {
        var $homeContainer = $('.sidebar-item-container[item-name="Home"]');
        if ($homeContainer.length) {
            var $homeAnchor = $homeContainer.find('.item-anchor');
            $homeAnchor.attr('href', '/app/' + OPS_DASHBOARD_ROUTE);
            $homeAnchor.off('click.opshome').on('click.opshome', redirect_to_dashboard);
            $homeContainer.off('click.opshome').on('click.opshome', '.standard-sidebar-item', redirect_to_dashboard);
        }

        $('.item-anchor[title="OPS Dashboard"], .item-anchor[title="Home"]').each(function() {
            $(this).attr('href', '/app/' + OPS_DASHBOARD_ROUTE);
            $(this).off('click.opshome').on('click.opshome', redirect_to_dashboard);
        });

        $('.navbar-brand, .navbar-home').each(function() {
            $(this).off('click.opshome').on('click.opshome', redirect_to_dashboard);
        });
    }

    $(document).ready(function() {
        setTimeout(setup_ops_home_redirect, 1000);

        var path = window.location.pathname;
        if (path === '/app' || path === '/app/' || path === '/app/home' || path === '/app/Home') {
            frappe.set_route(OPS_DASHBOARD_ROUTE);
        }
    });

    $(document).on('page-change', function() {
        setTimeout(setup_ops_home_redirect, 500);
    });

    $(document).ready(function() {
        if (frappe.set_route && !frappe._ops_route_override) {
            var original_set_route = frappe.set_route;
            frappe.set_route = function() {
                var args = Array.prototype.slice.call(arguments);
                var route = args[0];

                if (route === 'Home' || route === 'home' || route === '' ||
                    route === 'Workspaces/Home' || route === 'Workspaces') {
                    args[0] = OPS_DASHBOARD_ROUTE;
                }

                return original_set_route.apply(frappe, args);
            };
            frappe._ops_route_override = true;
        }
    });

    $(window).on('hashchange', function() {
        var route = frappe.get_route();
        if (route && route.length > 0) {
            if (route[0] === 'Workspaces' && (!route[1] || route[1] === 'Home')) {
                frappe.set_route(OPS_DASHBOARD_ROUTE);
            } else if (route[0] === 'Home' || route[0] === 'home') {
                frappe.set_route(OPS_DASHBOARD_ROUTE);
            }
        }
    });
})();
