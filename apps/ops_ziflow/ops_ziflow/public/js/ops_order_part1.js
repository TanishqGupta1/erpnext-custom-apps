/**
 * OPS Order Form - Complete Redesign
 * Professional ERP-grade form with 8 functional tabs,
 * 6-column grid layout, interactive product table, and financial summary
 */

frappe.ui.form.on('OPS Order', {
    refresh: function(frm) {
        OPSOrderForm.init(frm);
    },
    onload: function(frm) {
        OPSOrderForm.applyStyles();
    }
});

const OPSOrderForm = {
    frm: null,
    data: null,

    TABS: [
        { id: 'view-update', label: 'View/Update', icon: 'fa-eye' },
        { id: 'shipment', label: 'Shipment', icon: 'fa-truck' },
        { id: 'notes', label: 'Notes', icon: 'fa-sticky-note' },
        { id: 'modify', label: 'Modify', icon: 'fa-edit' },
        { id: 'pickup-details', label: 'Pickup Details', icon: 'fa-map-marker' },
        { id: 'assign-job', label: 'Assign Job', icon: 'fa-user-plus' },
        { id: 'impose', label: 'Impose', icon: 'fa-th' },
        { id: 'payment-request', label: 'Payment Request', icon: 'fa-credit-card' }
    ],

    state: {
        activeTab: 'view-update',
        activeSubTab: 'view-orders',
        expandedProducts: new Set(),
        selectedProducts: new Set(),
        tabData: {}
    },

    init: function(frm) {
        this.frm = frm;
        this.state = {
            activeTab: 'view-update',
            activeSubTab: 'view-orders',
            expandedProducts: new Set(),
            selectedProducts: new Set(),
            tabData: {}
        };
        this.loadFullData().then(() => {
            this.render();
            this.bindEvents();
        });
    },

    loadFullData: async function() {
        if (!this.frm.doc.name) return;
        try {
            const response = await frappe.call({
                method: 'ops_ziflow.api.order_form.get_order_full_data',
                args: { order_name: this.frm.doc.name },
                async: true
            });
            this.data = response.message;
        } catch (e) {
            try {
                const fallback = await frappe.call({
                    method: 'ops_ziflow.api.order_form.get_order_enriched_data',
                    args: { order_name: this.frm.doc.name },
                    async: true
                });
                this.data = fallback.message;
            } catch (e2) {
                this.data = null;
            }
        }
    },

    applyStyles: function() {
        if (!document.getElementById('ops-order-dynamic-styles')) {
            const style = document.createElement('style');
            style.id = 'ops-order-dynamic-styles';
            style.textContent = '.ops-form-wrapper .frappe-control[data-fieldname="orders_info_tab"]{display:none!important}';
            document.head.appendChild(style);
        }
    },

    render: function() {
        const wrapper = this.frm.fields_dict.ops_form_wrapper_html?.$wrapper ||
                       this.frm.fields_dict.customer_panel_html?.$wrapper;
        if (!wrapper) {
            console.warn('OPS Order Form: No wrapper field found');
            return;
        }
        wrapper.html('<div class="ops-form-container">' + this.renderTabNavigation() + this.renderTabContent() + '</div>');
    },

    bindEvents: function() {
        const self = this;
        const wrapper = this.frm.fields_dict.ops_form_wrapper_html?.$wrapper ||
                       this.frm.fields_dict.customer_panel_html?.$wrapper;
        if (!wrapper) return;

        // Tab switching
        wrapper.on('click', '.ops-tab-btn', function() {
            const tabId = $(this).data('tab');
            self.state.activeTab = tabId;

            // Update button active state
            wrapper.find('.ops-tab-btn').removeClass('active');
            $(this).addClass('active');

            // Update content active state
            wrapper.find('.ops-tab-content').removeClass('active');
            wrapper.find('.ops-tab-content[data-tab-content="' + tabId + '"]').addClass('active');
        });

        // Sub-tab switching (for View Orders / View Invoices)
        wrapper.on('click', '.ops-sub-tab', function() {
            const subTabId = $(this).data('subtab');
            self.state.activeSubTab = subTabId;

            wrapper.find('.ops-sub-tab').removeClass('active');
            $(this).addClass('active');

            wrapper.find('.ops-sub-tab-content').removeClass('active');
            wrapper.find('.ops-sub-tab-content[data-subtab-content="' + subTabId + '"]').addClass('active');
        });

        // Product row expansion
        wrapper.on('click', '.ops-expand-btn', function(e) {
            e.stopPropagation();
            const productId = $(this).data('product');
            const row = wrapper.find('.ops-product-expanded-row[data-product="' + productId + '"]');

            if (self.state.expandedProducts.has(productId)) {
                self.state.expandedProducts.delete(productId);
                row.hide();
                $(this).find('i').removeClass('fa-chevron-up').addClass('fa-chevron-down');
            } else {
                self.state.expandedProducts.add(productId);
                row.show();
                $(this).find('i').removeClass('fa-chevron-down').addClass('fa-chevron-up');
            }
        });

        // Product checkbox selection
        wrapper.on('change', '.ops-product-checkbox', function() {
            const productId = $(this).data('product');
            if (this.checked) {
                self.state.selectedProducts.add(productId);
            } else {
                self.state.selectedProducts.delete(productId);
            }
        });

        // Select all products
        wrapper.on('change', '.ops-select-all-products', function() {
            const isChecked = this.checked;
            wrapper.find('.ops-product-checkbox').prop('checked', isChecked);
            if (isChecked) {
                wrapper.find('.ops-product-checkbox').each(function() {
                    self.state.selectedProducts.add($(this).data('product'));
                });
            } else {
                self.state.selectedProducts.clear();
            }
        });
    },

    renderTabNavigation: function() {
        const tabButtons = this.TABS.map(tab => 
            '<button class="ops-tab-btn ' + (this.state.activeTab === tab.id ? 'active' : '') + '" data-tab="' + tab.id + '">' +
            '<i class="fa ' + tab.icon + '"></i><span>' + tab.label + '</span></button>'
        ).join('');
        return '<div class="ops-tab-bar"><div class="ops-tabs-container">' + tabButtons + '</div>' +
            '<div class="ops-tab-actions">' +
            '<button class="ops-action-btn secondary" onclick="OPSOrderForm.sendEmail()"><i class="fa fa-envelope"></i> Send mail manually</button>' +
            '<button class="ops-action-btn primary" onclick="OPSOrderForm.updateOrder()"><i class="fa fa-save"></i> Update Order</button>' +
            '<button class="ops-action-btn secondary" onclick="OPSOrderForm.downloadOrder()"><i class="fa fa-download"></i> Download</button></div></div>';
    },

    renderTabContent: function() {
        const contents = {
            'view-update': this.renderViewUpdateTab(),
            'shipment': this.renderShipmentTab(),
            'notes': this.renderNotesTab(),
            'modify': this.renderModifyTab(),
            'pickup-details': this.renderPickupTab(),
            'assign-job': this.renderAssignJobTab(),
            'impose': this.renderImposeTab(),
            'payment-request': this.renderPaymentRequestTab()
        };
        return Object.entries(contents).map(([id, content]) => 
            '<div class="ops-tab-content ' + (this.state.activeTab === id ? 'active' : '') + '" data-tab-content="' + id + '">' + content + '</div>'
        ).join('');
    },

    renderViewUpdateTab: function() {
        return this.renderOrderHeader() + this.renderMainGrid() + this.renderProductsSection() + this.renderFinancialSummary();
    },

    renderOrderHeader: function() {
        const doc = this.frm.doc;
        const statusClass = this.getStatusClass(doc.order_status);
        return '<div class="ops-order-header"><div class="ops-order-title"><h2>Order: ' + doc.name + '</h2>' +
            '<span class="ops-status-badge ' + statusClass + '">' + (doc.order_status || 'Pending') + '</span></div></div>';
    },

    renderMainGrid: function() {
        return '<div class="ops-main-grid">' + this.renderOrderDetails() + this.renderCustomerDetails() +
            this.renderBillingAddress() + this.renderShippingAddress() + this.renderBlindShipping() + this.renderShippingInfo() + '</div>';
    },
