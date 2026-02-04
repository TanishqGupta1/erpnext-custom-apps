/**
 * OPS Custom Sidebar & Branding
 */

(function() {
    'use strict';

    if (typeof frappe === 'undefined') return;

    // Rebrand app title to VisualGraphX
    function rebrandApp() {
        // Change sidebar app switcher title
        $('.app-title').text('VisualGraphX');

        // Change the app title in the dropdown menu for ERPNext
        $('.app-switcher-menu .app-item[data-app-name="erpnext"] .app-item-title').text('VisualGraphX');

        // Also update any "ERPNext" text in the switcher
        $('.app-switcher-menu .app-item').each(function() {
            var $title = $(this).find('.app-item-title');
            if ($title.text().trim() === 'ERPNext') {
                $title.text('VisualGraphX');
            }
        });
    }

    // Run rebrand on load and page changes
    $(document).ready(function() {
        rebrandApp(); setInterval(rebrandApp, 500);
    });

    $(document).on('page-change', function() {
        setTimeout(rebrandApp, 300);
    });

    const LINKS = [
        { section: 'DASHBOARDS' },
        { label: 'Cluster Dashboard', route: 'ops-cluster-dashboard', color: '#2490ef' },
        { label: 'Orders Dashboard', route: 'ops-orders-dashboard', color: '#29cd42' },
        { label: 'Quotes Dashboard', route: 'ops-quotes-dashboard', color: '#ffa00a' },
        { label: 'ZiFlow Dashboard', route: 'ziflow-dashboard', color: '#7c3aed' },
        { section: 'ORDERS & QUOTES' },
        { label: 'Orders', route: 'List/OPS Order/List', color: '#29cd42' },
        { label: 'Quotes', route: 'List/OPS Quote/List', color: '#ffa00a' },
        { label: 'Shipments', route: 'List/OPS Shipment/List', color: '#06b6d4' },
        { section: 'MASTERS' },
        { label: 'Products', route: 'List/OPS Product/List', color: '#2490ef' },
        { label: 'Categories', route: 'List/OPS Category/List', color: '#eab308' },
        { section: 'CUSTOMERS' },
        { label: 'OPS Customers', route: 'List/OPS Customer/List', color: '#2490ef' },
        { label: 'Contacts', route: 'List/Contact/List', color: '#ffa00a' },
        { section: 'ZIFLOW' },
        { label: 'ZiFlow Proofs', route: 'List/OPS ZiFlow Proof/List', color: '#7c3aed' },
        { label: 'ZiFlow Portal', url: 'https://app.ziflow.com/#/proofs/folders', color: '#29cd42', external: true },
        { section: 'SYSTEM' },
        { label: 'Error Logs', route: 'List/OPS Error Log/List', color: '#dc2626' },
        { label: 'API Settings', route: 'OPS API Settings', color: '#6b7280' },
    ];

    function injectStyles() {
        if ($('#ops-sidebar-fix').length) return;

        var css =
            /* Fix sidebar scrolling - target all possible parent containers */
            '.body-sidebar { overflow-y: scroll !important; overflow-x: hidden !important; height: calc(100vh - 60px) !important; max-height: calc(100vh - 60px) !important; }' +
            '.body-sidebar .sidebar-items { overflow-y: scroll !important; overflow-x: hidden !important; height: 100% !important; max-height: 100% !important; }' +
            '.layout-side-section { overflow-y: scroll !important; overflow-x: hidden !important; height: calc(100vh - 60px) !important; }' +
            '.desk-sidebar { overflow-y: scroll !important; overflow-x: hidden !important; height: calc(100vh - 60px) !important; }' +
            /* OPS sidebar styles */
            '#ops-sidebar * { visibility: visible !important; opacity: 1 !important; }' +
            '#ops-sidebar .ops-title { padding: 10px 16px 6px !important; font-size: 10px !important; font-weight: 700 !important; letter-spacing: 1px !important; color: #6b7280 !important; display: block !important; }' +
            '#ops-sidebar .ops-section-title { padding: 12px 16px 4px !important; font-size: 9px !important; font-weight: 600 !important; letter-spacing: 0.5px !important; color: #9ca3af !important; display: block !important; }' +
            '#ops-sidebar .ops-link-item { display: flex !important; align-items: center !important; padding: 8px 16px !important; text-decoration: none !important; cursor: pointer !important; border-radius: 6px !important; margin: 2px 8px !important; }' +
            '#ops-sidebar .ops-link-item:hover { background-color: #f3f4f6 !important; }' +
            '#ops-sidebar .ops-dot { width: 8px !important; height: 8px !important; min-width: 8px !important; min-height: 8px !important; border-radius: 50% !important; margin-right: 12px !important; display: inline-block !important; }' +
            '#ops-sidebar .ops-label { font-size: 13px !important; color: #374151 !important; font-weight: 400 !important; display: inline !important; visibility: visible !important; }' +
            '#ops-sidebar .ops-external { margin-left: auto !important; opacity: 0.4 !important; display: inline !important; }';

        $('<style id="ops-sidebar-fix">').text(css).appendTo('head');
    }

    function createSidebar() {
        var $sidebar = $('.body-sidebar .sidebar-items');
        if (!$sidebar.length || $('#ops-sidebar').length) return;

        injectStyles();

        var container = document.createElement('div');
        container.id = 'ops-sidebar';
        container.style.cssText = 'border-bottom: 1px solid #d1d5db !important; margin-bottom: 10px !important; padding-bottom: 10px !important; max-height: 300px !important; overflow-y: scroll !important;';

        var title = document.createElement('div');
        title.className = 'ops-title';
        title.textContent = 'OPS QUICK ACCESS';
        container.appendChild(title);

        LINKS.forEach(function(item) {
            if (item.section) {
                var section = document.createElement('div');
                section.className = 'ops-section-title';
                section.textContent = item.section;
                container.appendChild(section);
            } else {
                var link = document.createElement('a');
                link.className = 'ops-link-item';
                if (item.external) {
                    link.href = item.url;
                    link.target = '_blank';
                } else {
                    link.href = '#';
                    link.onclick = function(e) {
                        e.preventDefault();
                        frappe.set_route(item.route);
                    };
                }

                var dot = document.createElement('span');
                dot.className = 'ops-dot';
                dot.style.backgroundColor = item.color;
                link.appendChild(dot);

                var label = document.createElement('span');
                label.className = 'ops-label';
                label.textContent = item.label;
                link.appendChild(label);

                if (item.external) {
                    var ext = document.createElement('span');
                    ext.className = 'ops-external';
                    ext.textContent = '↗';
                    link.appendChild(ext);
                }

                container.appendChild(link);
            }
        });

        $sidebar.prepend(container);
        
        // Force styles directly on element
        container.setAttribute('style', 'max-height: 300px !important; overflow-y: scroll !important; overflow-x: hidden !important; border-bottom: 1px solid #d1d5db; margin-bottom: 10px; padding-bottom: 10px; display: block;');
        
        // Use setProperty for !important support
        container.style.setProperty('max-height', '300px', 'important');
        container.style.setProperty('overflow-y', 'scroll', 'important');
        container.style.setProperty('overflow-x', 'hidden', 'important');
        container.style.setProperty('display', 'block', 'important');
    }

    $(document).ready(function() {
        setTimeout(createSidebar, 800);
    });

    $(document).on('page-change', function() {
        setTimeout(function() {
            if (!$('#ops-sidebar').length) {
                createSidebar();
            }
        }, 400);
    });

    // Keep forcing styles
    setInterval(function() {
        var el = document.getElementById('ops-sidebar');
        if (el) {
            el.style.setProperty('max-height', '300px', 'important');
            el.style.setProperty('overflow-y', 'scroll', 'important');
            el.style.setProperty('overflow-x', 'hidden', 'important');
            el.style.setProperty('display', 'block', 'important');
        }
    }, 1000);

    frappe.ops_sidebar = {
        refresh: function() {
            $('#ops-sidebar').remove();
            createSidebar();
            rebrandApp();
        }
    };

})();
