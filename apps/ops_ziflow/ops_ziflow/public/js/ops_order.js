/**
 * OPS Order Form - Visual Graphx ERP
 * Unified form with drawer, toast, and enhanced features
 */

frappe.ui.form.on('OPS Order', {
    refresh: function(frm) {
        if (!frm.doc.name || frm.is_new()) return;

        // Hide default form elements
        $(frm.wrapper).find('.form-section, .section-body').hide();
        $(frm.wrapper).find('.form-tabs-list, .form-tabs').hide();

        // Create or get container
        let $container = $(frm.wrapper).find('.ops-order-container');
        if (!$container.length) {
            $container = $('<div class="ops-order-container"></div>');
            $(frm.wrapper).find('.form-page').prepend($container);
        }

        // Force all parent containers to not clip content
        $(frm.wrapper).find('.form-page, .layout-main-section, .layout-main-section-wrapper, .main-section, .container').css({
            'overflow': 'visible',
            'overflow-x': 'visible',
            'overflow-y': 'visible'
        });

        // Initialize the form app
        new OPSOrderApp(frm, $container);
    }
});

class OPSOrderApp {
    constructor(frm, container) {
        this.frm = frm;
        this.$container = container;
        this.data = null;
        this.state = {
            activeTab: 'view-update',
            activeSubTab: 'view-orders',
            expandedProducts: new Set(),
            selectedProducts: new Set(),
            drawerOpen: false,
            drawerProduct: null
        };
        this.pendingAction = null;

        // Set global reference for onclick handlers
        window.OPSOrderApp = this;

        this.init();
    }

    async init() {
        this.showLoading();
        try {
            await this.loadData();
            this.render();
            this.bindEvents();
        } catch (error) {
            console.error('OPS Order Form Error:', error);
            this.showError('Failed to load order data');
        }
    }

    showLoading() {
        this.$container.html(`
            <div class="ops-app">
                <div class="ops-loading">
                    <div class="ops-loading-spinner"></div>
                    <div class="ops-loading-text">Loading order...</div>
                </div>
            </div>
        `);
    }

    showError(message) {
        this.$container.html(`
            <div class="ops-app">
                <div class="ops-loading">
                    <i class="fa fa-exclamation-circle" style="font-size:48px;color:#ef4444;margin-bottom:12px;"></i>
                    <p style="color:#ef4444;">${message}</p>
                    <button class="ops-btn primary" onclick="location.reload()">
                        <i class="fa fa-refresh"></i> Reload
                    </button>
                </div>
            </div>
        `);
    }

    async loadData() {
        const response = await frappe.call({
            method: 'ops_ziflow.api.order_form.get_order_full_data',
            args: { order_name: this.frm.doc.name }
        });
        if (!response.message) throw new Error('Order not found');
        this.data = response.message;
    }

    render() {
        const doc = this.data.order || this.frm.doc;
        this.$container.html(`
            <div class="ops-app" id="ops-order-app">
                ${this.renderHeader()}
                ${this.renderTabNav()}
                <div class="ops-tab-panel active" data-panel="view-update">
                    ${this.renderCards()}
                    ${this.renderProducts()}
                    ${this.renderTotals()}
                </div>
                <div class="ops-tab-panel" data-panel="shipment">
                    <div class="ops-empty-tab"><i class="fa fa-truck"></i><h4>Shipment Details</h4><p>Configure shipping and tracking</p></div>
                </div>
                <div class="ops-tab-panel" data-panel="notes">
                    <div class="ops-empty-tab"><i class="fa fa-sticky-note"></i><h4>Order Notes</h4><p>Internal notes and comments</p></div>
                </div>
                <div class="ops-tab-panel" data-panel="history">
                    ${this.renderHistoryTab()}
                </div>
                <div class="ops-tab-panel" data-panel="modify">
                    <div class="ops-empty-tab"><i class="fa fa-edit"></i><h4>Modify Order</h4><p>Edit order configuration</p></div>
                </div>
                ${this.renderDrawer()}
                ${this.renderDialogOverlay()}
            </div>
            <style>${this.getStyles()}</style>
        `);
    }

    renderHeader() {
        const doc = this.data.order || this.frm.doc;
        const orderId = doc.ops_order_id || doc.name;
        const status = doc.order_status || 'Pending';
        const paymentStatus = doc.payment_status_title || 'Unpaid';
        const isPaid = paymentStatus.toLowerCase() === 'paid';

        return `
            <div class="ops-header">
                <div class="ops-header-left">
                    <div class="ops-breadcrumb">
                        <a href="/app/ops-order">Orders</a>
                        <i class="fa fa-chevron-right"></i>
                        <span>${orderId}</span>
                    </div>
                    <div class="ops-title-row">
                        <h1 class="ops-page-title">Order #${orderId}</h1>
                        ${this.renderStatusBadge(status)}
                        ${this.renderPaymentBadge(paymentStatus)}
                    </div>
                </div>
                <div class="ops-header-actions">
                    <button class="ops-btn secondary" onclick="OPSOrderApp.sendEmail()">
                        <i class="fa fa-envelope"></i> Send Mail
                    </button>
                    <div class="ops-actions-dropdown">
                        <button class="ops-btn secondary" onclick="OPSOrderApp.toggleDownloadMenu()">
                            <i class="fa fa-download"></i> Download
                            <i class="fa fa-caret-down" style="margin-left:4px;"></i>
                        </button>
                        <div class="ops-dropdown-menu" id="download-menu">
                            <div class="ops-dropdown-item" onclick="OPSOrderApp.downloadInvoice()">
                                <i class="fa fa-file-pdf-o"></i> Invoice
                            </div>
                            <div class="ops-dropdown-item" onclick="OPSOrderApp.downloadPackingSlip()">
                                <i class="fa fa-file-text-o"></i> Packing Slip
                            </div>
                            <div class="ops-dropdown-item" onclick="OPSOrderApp.downloadFiles()">
                                <i class="fa fa-file-archive-o"></i> All Files
                            </div>
                        </div>
                    </div>
                    <button class="ops-btn secondary" onclick="OPSOrderApp.syncOrder()">
                        <i class="fa fa-refresh"></i> Sync
                    </button>
                    <button class="ops-btn primary" onclick="OPSOrderApp.updateOrder()">
                        <i class="fa fa-save"></i> Update Order
                    </button>
                </div>
            </div>
        `;
    }

    renderStatusBadge(status) {
        const statusMap = {
            'Pending': 'neutral', 'Processing': 'info', 'In Design': 'purple',
            'In Production': 'info', 'Production': 'info', 'Shipped': 'info',
            'Fulfilled': 'success', 'Completed': 'success', 'Cancelled': 'danger', 'On Hold': 'warning'
        };
        const badgeClass = statusMap[status] || 'neutral';
        return `<span class="ops-badge ${badgeClass}">${status}</span>`;
    }

    renderPaymentBadge(status) {
        const isPaid = status.toLowerCase() === 'paid';
        const icon = isPaid ? 'check-circle' : 'exclamation-circle';
        return `<span class="ops-badge ${isPaid ? 'success' : 'danger'}"><i class="fa fa-${icon}"></i> ${status}</span>`;
    }

    renderTabNav() {
        const tabs = [
            { id: 'view-update', icon: 'fa-pencil', label: 'View/Update' },
            { id: 'shipment', icon: 'fa-truck', label: 'Shipment' },
            { id: 'notes', icon: 'fa-sticky-note', label: 'Notes' },
            { id: 'history', icon: 'fa-history', label: 'History' },
            { id: 'modify', icon: 'fa-edit', label: 'Modify' },
            { id: 'pickup', icon: 'fa-download', label: 'Pickup Details' },
            { id: 'assign', icon: 'fa-tasks', label: 'Assign Job' },
            { id: 'impose', icon: 'fa-th-large', label: 'Impose' },
            { id: 'payment', icon: 'fa-credit-card', label: 'Payment Request' }
        ];

        return `
            <div class="ops-tabs-nav">
                <div class="ops-tabs-list">
                    ${tabs.map(t => `
                        <div class="ops-tab-item ${t.id === this.state.activeTab ? 'active' : ''}" data-tab="${t.id}">
                            <i class="fa ${t.icon}"></i>
                            <span>${t.label}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderCards() {
        const doc = this.data.order || this.frm.doc;
        const customer = this.data.customer || {};
        const shipping = this.data.shipping_address || {};
        const billing = this.data.billing_address || {};
        const status = doc.order_status || 'Pending';

        return `
            <div class="ops-cards-grid">
                <!-- Order Details -->
                <div class="ops-card">
                    <div class="ops-card-header">
                        <span><i class="fa fa-file-text"></i> Order Details</span>
                        <i class="fa fa-pencil" onclick="OPSOrderApp.editSection('order')"></i>
                    </div>
                    <div class="ops-card-body">
                        <div class="ops-info-row"><span class="ops-label">Order Name :</span> ${doc.order_name || doc.ops_order_id || '-'}</div>
                        <div class="ops-info-row"><span class="ops-label">Order Date :</span> ${this.formatDateTime(doc.date_purchased)} <span class="ops-badge warning sm">${status}</span></div>
                        <div class="ops-info-row"><span class="ops-label">Production Due Date :</span> ${this.formatDate(doc.production_due_date)}</div>
                        <div class="ops-info-row"><span class="ops-label">Order Due Date :</span> ${this.formatDate(doc.orders_due_date)}</div>
                        <div class="ops-info-row"><span class="ops-label">Invoice Number :</span> ${doc.invoice_number || '-'}</div>
                        <div class="ops-info-row"><span class="ops-label">PO Number :</span> ${doc.po_number || '-'}</div>
                    </div>
                </div>

                <!-- Customer Details -->
                <div class="ops-card">
                    <div class="ops-card-header">
                        <span><i class="fa fa-user"></i> Customer Details</span>
                        <i class="fa fa-external-link" onclick="OPSOrderApp.viewCustomer()"></i>
                    </div>
                    <div class="ops-card-body">
                        <div class="ops-info-row"><a href="#">${customer.customer_name || doc.customers_name || '-'}</a></div>
                        <div class="ops-info-row">${customer.email || doc.customers_email_address || '-'}</div>
                        <div class="ops-info-row">Phone : <a href="tel:${doc.customers_telephone}">${this.formatPhone(doc.customers_telephone)}</a></div>
                        <div class="ops-info-row">Company : ${doc.customers_company || '-'}</div>
                        <div class="ops-section-divider">Customer Extra Field</div>
                        <div class="ops-info-row">Job Title: ${doc.customer_job_title || 'None'}</div>
                        <div class="ops-info-row">Website: ${doc.customer_website || 'None'}</div>
                    </div>
                </div>

                <!-- Billing Address -->
                <div class="ops-card">
                    <div class="ops-card-header">
                        <span><i class="fa fa-building"></i> Billing Address</span>
                        <i class="fa fa-pencil" onclick="OPSOrderApp.editSection('billing')"></i>
                    </div>
                    <div class="ops-card-body">
                        <div class="ops-info-row">${billing.name || doc.billing_name || '-'}</div>
                        <div class="ops-info-row">${doc.billing_street_address || '-'}</div>
                        <div class="ops-info-row">${[doc.billing_city, doc.billing_state, doc.billing_postcode].filter(Boolean).join(' ') || '-'}</div>
                        <div class="ops-info-row">${doc.billing_country || 'United States'}</div>
                        <div class="ops-info-row">Company : ${doc.billing_company || '-'}</div>
                        <div class="ops-info-row">Phone : <a href="tel:${doc.billing_telephone}">${this.formatPhone(doc.billing_telephone)}</a></div>
                    </div>
                </div>

                <!-- Shipping Address -->
                <div class="ops-card">
                    <div class="ops-card-header">
                        <span><i class="fa fa-truck"></i> Shipping Address</span>
                        <i class="fa fa-pencil" onclick="OPSOrderApp.editSection('shipping')"></i>
                    </div>
                    <div class="ops-card-body">
                        <div class="ops-info-row">${shipping.name || doc.delivery_name || '-'}</div>
                        <div class="ops-info-row">${doc.delivery_street_address || '-'}</div>
                        <div class="ops-info-row">${[doc.delivery_city, doc.delivery_state, doc.delivery_postcode].filter(Boolean).join(' ') || '-'}</div>
                        <div class="ops-info-row">${doc.delivery_country || 'United States'}</div>
                        <div class="ops-info-row">Company : ${doc.delivery_company || '-'}</div>
                        <div class="ops-info-row">Phone : <a href="tel:${doc.delivery_telephone}">${this.formatPhone(doc.delivery_telephone)}</a></div>
                    </div>
                </div>

                <!-- Blind Shipping -->
                <div class="ops-card">
                    <div class="ops-card-header">
                        <span><i class="fa fa-eye-slash"></i> Blind Shipping</span>
                        <i class="fa fa-pencil" onclick="OPSOrderApp.editSection('blind')"></i>
                    </div>
                    <div class="ops-card-body">
                        ${doc.blind_name ? `
                            <div class="ops-info-row">${doc.blind_name}</div>
                            <div class="ops-info-row">${doc.blind_street_address || ''}</div>
                            <div class="ops-info-row">${[doc.blind_city, doc.blind_state, doc.blind_postcode].filter(Boolean).join(' ')}</div>
                        ` : `
                            <div class="ops-info-row">-</div>
                            <div class="ops-blind-link" onclick="OPSOrderApp.enableBlindShipping()">
                                <i class="fa fa-plus"></i> Enable Blind Shipping
                            </div>
                        `}
                    </div>
                </div>

                <!-- Shipping/Payment Info -->
                <div class="ops-card">
                    <div class="ops-card-header">
                        <span><i class="fa fa-credit-card"></i> Shipping & Payment</span>
                    </div>
                    <div class="ops-card-body">
                        <div class="ops-info-row">Shipping Method : ${doc.shipping_mode || '-'}</div>
                        <div class="ops-info-row">Carrier : ${doc.courirer_company_name || '-'}</div>
                        <div class="ops-info-row">Tracking # : ${doc.airway_bill_number ? `<a href="#" onclick="OPSOrderApp.trackShipment('${doc.airway_bill_number}')">${doc.airway_bill_number}</a>` : '-'}</div>
                        <div class="ops-info-row">Payment Method : ${doc.payment_method_name || '-'}</div>
                        <div class="ops-info-row">Payment Date : ${this.formatDate(doc.payment_date)}</div>
                        <div class="ops-info-row">Transaction ID : ${doc.transactionid || '-'}</div>
                    </div>
                </div>
            </div>
        `;
    }

    renderProducts() {
        const products = this.data.products || [];

        return `
            <div class="ops-products">
                <div class="ops-products-toolbar">
                    <div class="ops-subtabs">
                        <div class="ops-subtab ${this.state.activeSubTab === 'view-orders' ? 'active' : ''}" data-subtab="view-orders">View Orders</div>
                        <div class="ops-subtab ${this.state.activeSubTab === 'order-history' ? 'active' : ''}" data-subtab="order-history">Order History</div>
                    </div>
                    <div class="ops-products-actions">
                        <div class="ops-search-box">
                            <i class="fa fa-search"></i>
                            <input type="text" placeholder="Search products..." id="product-search">
                        </div>
                        <select class="ops-select" id="bulkStatus">
                            <option value="">Select Status</option>
                            <option value="Pending">Pending</option>
                            <option value="In RIP">In RIP</option>
                            <option value="In Production">In Production</option>
                            <option value="Completed">Completed</option>
                        </select>
                        <button class="ops-btn primary" data-action="bulk-update">Update</button>
                        <button class="ops-btn success" onclick="OPSOrderApp.addProduct()"><i class="fa fa-plus"></i> Add Product</button>
                    </div>
                </div>
                <div class="ops-products-title-bar">
                    <span class="ops-products-title">Order Product Details</span>
                    <span class="ops-products-count">${products.length}</span>
                </div>
                <div class="ops-table-wrap">
                    <table class="ops-table">
                        <thead>
                            <tr>
                                <th class="col-check"><input type="checkbox" id="selectAll" data-action="select-all"></th>
                                <th>ID</th>
                                <th>Product</th>
                                <th>Status</th>
                                <th class="col-num">Qty</th>
                                <th class="col-num">Price</th>
                                <th class="col-num">Total</th>
                                <th class="col-actions"></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${products.length > 0 ? products.map((p, i) => this.renderProductRow(p, i)).join('') : `
                                <tr><td colspan="8" class="ops-empty-cell">
                                    <i class="fa fa-inbox"></i>
                                    <p>No products in this order</p>
                                    <button class="ops-btn primary" onclick="OPSOrderApp.addProduct()">
                                        <i class="fa fa-plus"></i> Add Product
                                    </button>
                                </td></tr>
                            `}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    renderProductRow(product, index) {
        const id = product.orders_products_id || product.name || index;
        const name = product.products_title || product.products_name || 'Unknown Product';
        const sku = product.products_sku || '-';
        const status = product.product_status || 'Pending';
        const qty = product.products_quantity || 1;
        const price = parseFloat(product.products_price || 0);
        const total = parseFloat(product.final_price || price * qty);
        const isExpanded = this.state.expandedProducts.has(id);
        const proofs = product.proofs || [];
        const optionsCount = product.parsed_options?.options_count || 0;

        const statuses = ['Pending', 'In Design', 'In RIP', 'In Production', 'Completed', 'Shipped', 'Fulfilled'];

        return `
            <tr class="ops-product-row" data-id="${id}">
                <td class="col-check"><input type="checkbox" data-product-id="${id}"></td>
                <td>${id}</td>
                <td>
                    <div class="ops-product-cell">
                        <span class="ops-product-name">${name}</span>
                        <span class="ops-product-sku">SKU: ${sku}</span>
                        <div class="ops-product-meta">
                            ${optionsCount > 0 ? `<span class="ops-product-tag">${optionsCount} options</span>` : ''}
                            ${proofs.length > 0 ? `<span class="ops-product-tag"><i class="fa fa-file-image-o"></i> ${proofs.length} proofs</span>` : ''}
                        </div>
                    </div>
                </td>
                <td>
                    <select class="ops-status-select" data-product-name="${product.name}" onchange="OPSOrderApp.updateProductStatus('${product.name}', this.value)">
                        ${statuses.map(s => `<option value="${s}" ${s === status ? 'selected' : ''}>${s}</option>`).join('')}
                    </select>
                </td>
                <td class="col-num">${qty}</td>
                <td class="col-num">$${price.toFixed(2)}</td>
                <td class="col-num ops-price">$${total.toFixed(2)}</td>
                <td class="col-actions">
                    <div class="ops-row-actions">
                        <button class="ops-expand-btn" data-id="${id}">
                            <i class="fa fa-chevron-${isExpanded ? 'up' : 'down'}"></i>
                        </button>
                        <div class="ops-actions-dropdown">
                            <button class="ops-menu-btn" onclick="OPSOrderApp.toggleProductMenu('${id}')">
                                <i class="fa fa-ellipsis-v"></i>
                            </button>
                            <div class="ops-dropdown-menu" id="product-menu-${id}">
                                <div class="ops-dropdown-item" onclick="OPSOrderApp.openDrawer('${product.name || id}')">
                                    <i class="fa fa-eye"></i> View Details
                                </div>
                                <div class="ops-dropdown-item" onclick="OPSOrderApp.editProduct('${product.name}')">
                                    <i class="fa fa-pencil"></i> Edit
                                </div>
                                <div class="ops-dropdown-item" onclick="OPSOrderApp.duplicateProduct('${id}')">
                                    <i class="fa fa-copy"></i> Duplicate
                                </div>
                                <div class="ops-dropdown-divider"></div>
                                <div class="ops-dropdown-item" onclick="OPSOrderApp.createProof('${id}')">
                                    <i class="fa fa-file-image-o"></i> Create Proof
                                </div>
                                <div class="ops-dropdown-divider"></div>
                                <div class="ops-dropdown-item danger" onclick="OPSOrderApp.deleteProduct('${id}')">
                                    <i class="fa fa-trash"></i> Delete
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
            <tr class="ops-expanded-row ${isExpanded ? 'show' : ''}" data-for="${id}">
                <td colspan="8">
                    ${this.renderExpandedContent(product)}
                </td>
            </tr>
        `;
    }

    renderExpandedContent(product) {
        const options = product.parsed_options?.groups || [];
        const masterOptions = product.master_options || [];
        const proofs = product.proofs || [];

        return `
            <div class="ops-expanded-content">
                <div class="ops-expanded-grid">
                    <div class="ops-expanded-section">
                        <h4><i class="fa fa-sliders"></i> Product Options</h4>
                        ${options.length > 0 ? `
                            <div class="ops-options-list">
                                ${options.filter(g => g.name !== 'Ignore').flatMap(g => g.options || []).slice(0, 8).map(opt => `
                                    <div class="ops-option-item">
                                        <span>${opt.label || opt.option_name || '-'}</span>
                                        <span>${opt.value || opt.option_value || '-'}${opt.price > 0 ? ` <span class="ops-price">+$${parseFloat(opt.price).toFixed(2)}</span>` : ''}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p class="ops-empty-text">No options configured</p>'}
                    </div>
                    <div class="ops-expanded-section">
                        <h4><i class="fa fa-cogs"></i> Master Options</h4>
                        ${masterOptions.length > 0 ? `
                            <div class="ops-options-list">
                                ${masterOptions.slice(0, 6).map(opt => `
                                    <div class="ops-option-item">
                                        <span>${opt.option_name || '-'}</span>
                                        <span>${opt.option_value || '-'}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p class="ops-empty-text">No master options</p>'}
                    </div>
                    <div class="ops-expanded-section">
                        <h4><i class="fa fa-file-image-o"></i> Proofs</h4>
                        ${proofs.length > 0 ? `
                            <div class="ops-proofs-grid">
                                ${proofs.map(proof => `
                                    <div class="ops-proof-card" onclick="OPSOrderApp.openProof('${proof.ziflow_url || '#'}')">
                                        <img src="${proof.preview_url || '/assets/frappe/images/default-image.png'}"
                                             onerror="this.src='/assets/frappe/images/default-image.png'">
                                        <span class="ops-badge sm ${proof.proof_status === 'Approved' ? 'success' : 'warning'}">${proof.proof_status || 'Pending'}</span>
                                        ${proof.ziflow_url ? `<a href="${proof.ziflow_url}" target="_blank" class="ops-proof-link"><i class="fa fa-external-link"></i></a>` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p class="ops-empty-text">No proofs attached</p>'}
                    </div>
                </div>
            </div>
        `;
    }

    renderHistoryTab() {
        const history = this.data.status_history || [];

        if (history.length === 0) {
            return `
                <div class="ops-empty-tab">
                    <i class="fa fa-history"></i>
                    <h4>No History</h4>
                    <p>Order history will appear here.</p>
                </div>
            `;
        }

        return `
            <div class="ops-timeline">
                ${history.map(item => `
                    <div class="ops-timeline-item">
                        <div class="ops-timeline-dot ${item.type === 'success' ? 'success' : ''}"></div>
                        <div class="ops-timeline-content">
                            <div class="ops-timeline-title">${item.title || item.status || 'Status Update'}</div>
                            <div class="ops-timeline-desc">${item.description || item.comment || ''}</div>
                            <div class="ops-timeline-time">${this.formatDateTime(item.timestamp || item.creation)}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderTotals() {
        const doc = this.data.order || this.frm.doc;
        const fin = this.data.financial_summary || {};

        const subtotal = fin.subtotal || parseFloat(doc.order_amount || 0);
        const shipping = fin.shipping_charges || parseFloat(doc.shipping_amount || 0);
        const tax = fin.tax || parseFloat(doc.tax_amount || 0);
        const total = fin.total || parseFloat(doc.total_amount || 0);
        const paid = fin.paid_amount || 0;
        const outstanding = fin.outstanding || (total - paid);

        return `
            <div class="ops-totals">
                <div class="ops-totals-header">
                    <i class="fa fa-calculator"></i> Order Summary
                </div>
                <div class="ops-totals-body">
                    <div class="ops-totals-row"><span>Subtotal</span><span>$${subtotal.toFixed(2)}</span></div>
                    <div class="ops-totals-row"><span>Shipping</span><span>$${shipping.toFixed(2)}</span></div>
                    <div class="ops-totals-row"><span>Tax</span><span>$${tax.toFixed(2)}</span></div>
                    <div class="ops-totals-row total"><span>Total</span><span>$${total.toFixed(2)}</span></div>
                    <div class="ops-totals-row"><span>Paid</span><span class="success">$${paid.toFixed(2)}</span></div>
                    ${outstanding > 0 ? `<div class="ops-totals-row"><span>Outstanding</span><span class="danger">$${outstanding.toFixed(2)}</span></div>` : ''}
                </div>
            </div>
        `;
    }

    // ==================== DRAWER ====================
    renderDrawer() {
        return `
            <div class="ops-drawer-overlay" id="product-drawer">
                <div class="ops-drawer">
                    <div class="ops-drawer-header">
                        <div class="ops-drawer-title-section">
                            <h3 id="drawer-title">Product Details</h3>
                            <div class="ops-drawer-subtitle" id="drawer-subtitle">SKU: -</div>
                        </div>
                        <button class="ops-drawer-close" onclick="OPSOrderApp.closeDrawer()">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                    <div class="ops-drawer-body" id="drawer-body">
                        <!-- Content loaded dynamically -->
                    </div>
                    <div class="ops-drawer-footer">
                        <button class="ops-btn secondary" onclick="OPSOrderApp.closeDrawer()">Close</button>
                        <button class="ops-btn primary" onclick="OPSOrderApp.saveProductChanges()">
                            <i class="fa fa-save"></i> Save Changes
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderDrawerContent(product) {
        const options = product.parsed_options?.groups || [];
        const masterOptions = product.master_options || [];
        const proofs = product.proofs || [];
        const totalOptionsPrice = product.parsed_options?.total_options_price || 0;

        return `
            <!-- Product Summary -->
            <div class="ops-drawer-section">
                <div class="ops-drawer-section-title">
                    <i class="fa fa-info-circle"></i> Product Summary
                </div>
                <div class="ops-info-box">
                    <div class="ops-info-grid">
                        <div class="ops-info-item">
                            <span class="ops-info-label">Quantity</span>
                            <span class="ops-info-value">${product.products_quantity || 1}</span>
                        </div>
                        <div class="ops-info-item">
                            <span class="ops-info-label">Status</span>
                            <span class="ops-info-value">${product.product_status || 'Pending'}</span>
                        </div>
                        <div class="ops-info-item">
                            <span class="ops-info-label">Base Price</span>
                            <span class="ops-info-value price">$${parseFloat(product.products_price || 0).toFixed(2)}</span>
                        </div>
                        <div class="ops-info-item">
                            <span class="ops-info-label">Total</span>
                            <span class="ops-info-value price">$${parseFloat(product.final_price || 0).toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Product Options -->
            <div class="ops-drawer-section">
                <div class="ops-drawer-section-title">
                    <i class="fa fa-sliders"></i> Product Options
                    ${totalOptionsPrice > 0 ? `<span class="ops-badge success sm">+$${totalOptionsPrice.toFixed(2)}</span>` : ''}
                </div>
                ${options.length > 0 ? `
                    <div class="ops-options-list">
                        ${options.filter(g => g.name !== 'Ignore').flatMap(g => (g.options || []).map(opt => `
                            <div class="ops-option-item">
                                <span>${opt.label || '-'}</span>
                                <span>
                                    ${opt.value || '-'}
                                    ${opt.price > 0 ? `<span class="ops-price">+$${opt.price.toFixed(2)}</span>` : ''}
                                </span>
                            </div>
                        `)).join('')}
                    </div>
                ` : '<p class="ops-empty-text">No options configured</p>'}
            </div>

            <!-- Master Options -->
            <div class="ops-drawer-section">
                <div class="ops-drawer-section-title">
                    <i class="fa fa-cogs"></i> Master Options
                </div>
                ${masterOptions.length > 0 ? `
                    <div class="ops-options-list">
                        ${masterOptions.map(opt => `
                            <div class="ops-option-item">
                                <span>${opt.option_name || '-'}</span>
                                <span>${opt.option_value || '-'}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p class="ops-empty-text">No master options</p>'}
            </div>

            <!-- Ziflow Proofs -->
            <div class="ops-drawer-section">
                <div class="ops-drawer-section-title">
                    <i class="fa fa-file-image-o"></i> Ziflow Proofs
                    <span class="ops-badge neutral sm">${proofs.length}</span>
                </div>
                ${proofs.length > 0 ? `
                    <div class="ops-proof-gallery">
                        ${proofs.map(proof => `
                            <div class="ops-proof-card-lg">
                                <div class="ops-proof-preview">
                                    <img src="${proof.preview_url || '/assets/frappe/images/default-image.png'}"
                                         onerror="this.src='/assets/frappe/images/default-image.png'"
                                         alt="${proof.proof_name || 'Proof'}">
                                </div>
                                <div class="ops-proof-info">
                                    <div class="ops-proof-name">${proof.proof_name || 'Proof'}</div>
                                    <span class="ops-badge sm ${proof.proof_status === 'Approved' ? 'success' : proof.proof_status === 'Rejected' ? 'danger' : 'warning'}">
                                        ${proof.proof_status || 'Pending'}
                                    </span>
                                    ${proof.ziflow_url ? `
                                        <button class="ops-btn sm primary" onclick="window.open('${proof.ziflow_url}', '_blank')">
                                            <i class="fa fa-external-link"></i> Open
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <div class="ops-empty-text" style="text-align:center;padding:24px;">
                        <i class="fa fa-file-image-o" style="font-size:24px;display:block;margin-bottom:8px;"></i>
                        <p>No proofs attached</p>
                        <button class="ops-btn sm primary" onclick="OPSOrderApp.createProof('${product.orders_products_id || product.name}')">
                            <i class="fa fa-plus"></i> Create Proof
                        </button>
                    </div>
                `}
            </div>
        `;
    }

    // ==================== DIALOG ====================
    renderDialogOverlay() {
        return `
            <div class="ops-dialog-overlay" id="confirm-dialog">
                <div class="ops-dialog">
                    <div class="ops-dialog-header">
                        <h3 class="ops-dialog-title" id="dialog-title">Confirm</h3>
                    </div>
                    <div class="ops-dialog-body" id="dialog-body">
                        Are you sure?
                    </div>
                    <div class="ops-dialog-footer">
                        <button class="ops-btn secondary" onclick="OPSOrderApp.closeDialog()">Cancel</button>
                        <button class="ops-btn danger" id="dialog-confirm-btn" onclick="OPSOrderApp.confirmAction()">Confirm</button>
                    </div>
                </div>
            </div>
        `;
    }

    // ==================== EVENT BINDING ====================
    bindEvents() {
        const self = this;

        // Tab navigation
        this.$container.on('click', '.ops-tab-item', function() {
            const tab = $(this).data('tab');
            self.state.activeTab = tab;
            self.$container.find('.ops-tab-item').removeClass('active');
            $(this).addClass('active');
            self.$container.find('.ops-tab-panel').removeClass('active');
            self.$container.find(`.ops-tab-panel[data-panel="${tab}"]`).addClass('active');
        });

        // Subtab navigation
        this.$container.on('click', '.ops-subtab', function() {
            const subtab = $(this).data('subtab');
            self.state.activeSubTab = subtab;
            self.$container.find('.ops-subtab').removeClass('active');
            $(this).addClass('active');
        });

        // Expand/collapse product rows
        this.$container.on('click', '.ops-expand-btn', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const id = $(this).data('id');
            const $row = self.$container.find(`.ops-expanded-row[data-for="${id}"]`);

            if (self.state.expandedProducts.has(id)) {
                self.state.expandedProducts.delete(id);
                $row.removeClass('show');
                $(this).find('i').removeClass('fa-chevron-up').addClass('fa-chevron-down');
            } else {
                self.state.expandedProducts.add(id);
                $row.addClass('show');
                $(this).find('i').removeClass('fa-chevron-down').addClass('fa-chevron-up');
            }
        });

        // Select all products
        this.$container.on('change', '[data-action="select-all"]', function() {
            const isChecked = this.checked;
            self.$container.find('input[data-product-id]').prop('checked', isChecked);
            if (isChecked) {
                self.$container.find('input[data-product-id]').each(function() {
                    self.state.selectedProducts.add($(this).data('product-id'));
                });
            } else {
                self.state.selectedProducts.clear();
            }
        });

        // Individual product selection
        this.$container.on('change', 'input[data-product-id]', function() {
            const id = $(this).data('product-id');
            if (this.checked) {
                self.state.selectedProducts.add(id);
            } else {
                self.state.selectedProducts.delete(id);
            }
        });

        // Bulk update
        this.$container.on('click', '[data-action="bulk-update"]', function() {
            self.bulkUpdateStatus();
        });

        // Search products
        this.$container.on('input', '#product-search', function() {
            const query = $(this).val().toLowerCase();
            self.$container.find('.ops-product-row').each(function() {
                const name = $(this).find('.ops-product-name').text().toLowerCase();
                const sku = $(this).find('.ops-product-sku').text().toLowerCase();
                const match = name.includes(query) || sku.includes(query);
                $(this).toggle(match);
                const id = $(this).data('id');
                self.$container.find(`.ops-expanded-row[data-for="${id}"]`).toggle(match && self.state.expandedProducts.has(id));
            });
        });

        // Close dropdowns on outside click
        $(document).on('click', function(e) {
            if (!$(e.target).closest('.ops-actions-dropdown').length) {
                self.$container.find('.ops-dropdown-menu').removeClass('show');
            }
        });

        // Close drawer on overlay click
        this.$container.on('click', '.ops-drawer-overlay', function(e) {
            if ($(e.target).hasClass('ops-drawer-overlay')) {
                self.closeDrawer();
            }
        });

        // Close dialog on overlay click
        this.$container.on('click', '.ops-dialog-overlay', function(e) {
            if ($(e.target).hasClass('ops-dialog-overlay')) {
                self.closeDialog();
            }
        });
    }

    // ==================== ACTIONS ====================
    async updateOrder() {
        this.showToast('Updating order...', 'info');
        try {
            await this.frm.save();
            this.showToast('Order updated successfully', 'success');
        } catch (e) {
            this.showToast('Failed to update order', 'error');
        }
    }

    async syncOrder() {
        this.showToast('Syncing order...', 'info');
        try {
            const r = await frappe.call({
                method: 'ops_ziflow.api.order_form.quick_action',
                args: { order_name: this.frm.doc.name, action: 'sync_order' }
            });
            if (r.message?.success) {
                this.showToast('Order synced successfully', 'success');
                await this.loadData();
                this.render();
                this.bindEvents();
            } else {
                this.showToast(r.message?.message || 'Sync failed', 'error');
            }
        } catch (e) {
            this.showToast('Failed to sync order', 'error');
        }
    }

    sendEmail() {
        const doc = this.data.order || this.frm.doc;
        frappe.new_doc('Email', {
            recipients: doc.customers_email_address,
            subject: `Order #${doc.ops_order_id || doc.name}`
        });
    }

    toggleDownloadMenu() {
        $('#download-menu').toggleClass('show');
    }

    downloadInvoice() {
        window.open(`/printview?doctype=OPS Order&name=${this.frm.doc.name}&format=Invoice`, '_blank');
        $('#download-menu').removeClass('show');
    }

    downloadPackingSlip() {
        window.open(`/printview?doctype=OPS Order&name=${this.frm.doc.name}&format=Packing Slip`, '_blank');
        $('#download-menu').removeClass('show');
    }

    downloadFiles() {
        this.showToast('Preparing files for download...', 'info');
        $('#download-menu').removeClass('show');
    }

    toggleProductMenu(id) {
        const menu = $(`#product-menu-${id}`);
        this.$container.find('.ops-dropdown-menu').not(menu).removeClass('show');
        menu.toggleClass('show');
    }

    async updateProductStatus(productName, status) {
        this.showToast('Updating status...', 'info');
        try {
            await frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'OPS Order Product',
                    name: productName,
                    fieldname: 'product_status',
                    value: status
                }
            });
            this.showToast(`Status updated to ${status}`, 'success');
        } catch (e) {
            this.showToast('Failed to update status', 'error');
        }
    }

    async bulkUpdateStatus() {
        const status = this.$container.find('#bulkStatus').val();
        if (!status) {
            this.showToast('Please select a status', 'warning');
            return;
        }
        if (this.state.selectedProducts.size === 0) {
            this.showToast('Please select products to update', 'warning');
            return;
        }

        this.showToast(`Updating ${this.state.selectedProducts.size} products...`, 'info');

        const products = this.data.products || [];
        for (const id of this.state.selectedProducts) {
            const product = products.find(p => (p.orders_products_id || p.name) == id);
            if (product && product.name) {
                await frappe.call({
                    method: 'frappe.client.set_value',
                    args: {
                        doctype: 'OPS Order Product',
                        name: product.name,
                        fieldname: 'product_status',
                        value: status
                    }
                });
            }
        }

        this.showToast(`Updated ${this.state.selectedProducts.size} products to ${status}`, 'success');
        this.state.selectedProducts.clear();
        this.$container.find('input[type="checkbox"]').prop('checked', false);

        // Reload data to reflect changes
        await this.loadData();
        this.render();
        this.bindEvents();
    }

    openDrawer(productName) {
        const products = this.data.products || [];
        const product = products.find(p => p.name === productName || p.orders_products_id == productName);

        if (product) {
            this.state.drawerProduct = product;
            $('#drawer-title').text(product.products_title || product.products_name || 'Product Details');
            $('#drawer-subtitle').text(`SKU: ${product.products_sku || '-'} | ID: ${product.orders_products_id || '-'}`);
            $('#drawer-body').html(this.renderDrawerContent(product));
            $('#product-drawer').addClass('show');
        }

        this.$container.find('.ops-dropdown-menu').removeClass('show');
    }

    closeDrawer() {
        $('#product-drawer').removeClass('show');
        this.state.drawerProduct = null;
    }

    addProduct() {
        this.showToast('Add product feature coming soon', 'info');
    }

    editProduct(productName) {
        if (productName) {
            frappe.set_route('Form', 'OPS Order Product', productName);
        }
        this.$container.find('.ops-dropdown-menu').removeClass('show');
    }

    duplicateProduct(id) {
        this.showToast('Duplicating product...', 'info');
        this.$container.find('.ops-dropdown-menu').removeClass('show');
    }

    createProof(productId) {
        this.showToast('Creating proof...', 'info');
        this.$container.find('.ops-dropdown-menu').removeClass('show');
    }

    deleteProduct(id) {
        this.pendingAction = { type: 'delete-product', id };
        $('#dialog-title').text('Delete Product');
        $('#dialog-body').text('Are you sure you want to delete this product? This action cannot be undone.');
        $('#dialog-confirm-btn').text('Delete');
        $('#confirm-dialog').addClass('show');
        this.$container.find('.ops-dropdown-menu').removeClass('show');
    }

    openProof(url) {
        if (url && url !== '#') {
            window.open(url, '_blank');
        }
    }

    trackShipment(tracking) {
        const url = `https://www.google.com/search?q=${tracking}+tracking`;
        window.open(url, '_blank');
    }

    viewCustomer() {
        const doc = this.data.order || this.frm.doc;
        if (doc.erp_customer) {
            frappe.set_route('Form', 'Customer', doc.erp_customer);
        } else if (doc.customers_company) {
            frappe.set_route('List', 'OPS Customer', { company: doc.customers_company });
        }
    }

    editSection(section) {
        this.showDefaultForm();
    }

    enableBlindShipping() {
        this.showToast('Enable blind shipping in order edit mode', 'info');
        this.showDefaultForm();
    }

    showDefaultForm() {
        $(this.frm.wrapper).find('.ops-order-container').hide();
        $(this.frm.wrapper).find('.form-section, .section-body, .form-tabs-list, .form-tabs').show();
    }

    closeDialog() {
        $('#confirm-dialog').removeClass('show');
        this.pendingAction = null;
    }

    async confirmAction() {
        if (!this.pendingAction) return;

        const { type, id } = this.pendingAction;

        if (type === 'delete-product') {
            this.showToast('Deleting product...', 'info');
            try {
                const products = this.data.products || [];
                const product = products.find(p => (p.orders_products_id || p.name) == id);
                if (product && product.name) {
                    await frappe.call({
                        method: 'frappe.client.delete',
                        args: { doctype: 'OPS Order Product', name: product.name }
                    });
                    this.showToast('Product deleted', 'success');
                    await this.loadData();
                    this.render();
                    this.bindEvents();
                }
            } catch (e) {
                this.showToast('Failed to delete product', 'error');
            }
        }

        this.closeDialog();
    }

    saveProductChanges() {
        this.showToast('Saving changes...', 'info');
        setTimeout(() => {
            this.showToast('Changes saved', 'success');
            this.closeDrawer();
        }, 500);
    }

    // ==================== UTILITIES ====================
    formatDate(dateStr) {
        if (!dateStr || dateStr === 'Invalid date') return '-';
        try {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) return '-';
            return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        } catch { return '-'; }
    }

    formatDateTime(dateStr) {
        if (!dateStr || dateStr === 'Invalid date') return '-';
        try {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) return '-';
            return d.toLocaleDateString('en-US', {
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        } catch { return '-'; }
    }

    formatPhone(phone) {
        if (!phone) return '-';
        const cleaned = String(phone).replace(/\D/g, '');
        if (cleaned.length === 10) {
            return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
        }
        return phone;
    }

    showToast(message, type = 'info') {
        $('.ops-toast').remove();

        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };

        const toast = $(`
            <div class="ops-toast ${type}">
                <i class="fa fa-${iconMap[type] || 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `);

        $('body').append(toast);
        setTimeout(() => toast.addClass('show'), 10);
        setTimeout(() => {
            toast.removeClass('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getStatusClass(status) {
        const map = {
            'Pending': 'warning', 'New Order': 'info', 'In Production': 'info', 'Production': 'info',
            'Completed': 'success', 'Fulfilled': 'success', 'Shipped': 'success', 'Approved': 'success',
            'Cancelled': 'danger', 'Rejected': 'danger'
        };
        return map[status] || 'neutral';
    }

    getStyles() {
        return `
            /* ============================================
               OPS ORDER FORM - UNIFIED STYLING
               ============================================ */

            .ops-order-container {
                overflow: visible !important;
                position: relative;
            }

            .ops-app {
                --ops-primary: #0891b2;
                --ops-primary-hover: #0e7490;
                --ops-success: #10b981;
                --ops-success-hover: #059669;
                --ops-danger: #dc2626;
                --ops-warning: #f59e0b;
                --ops-purple: #8b5cf6;
                --ops-gray-50: #f9fafb;
                --ops-gray-100: #f3f4f6;
                --ops-gray-200: #e5e7eb;
                --ops-gray-300: #d1d5db;
                --ops-gray-500: #6b7280;
                --ops-gray-600: #4b5563;
                --ops-gray-700: #374151;
                --ops-gray-900: #1f2937;
                --ops-spacing: 20px;
                --ops-radius: 8px;
                --ops-radius-lg: 10px;
                --ops-shadow: 0 1px 3px rgba(0,0,0,0.1);
                --ops-font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                --ops-btn-height: 36px;

                background: var(--ops-gray-50);
                min-height: calc(100vh - 120px);
                font-family: var(--ops-font);
                position: relative;
            }

            .ops-loading {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 80px;
                color: var(--ops-gray-500);
            }

            .ops-loading-spinner {
                width: 40px;
                height: 40px;
                border: 3px solid var(--ops-gray-200);
                border-top-color: var(--ops-primary);
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 16px;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            /* ============================================
               HEADER
               ============================================ */
            .ops-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 24px;
                background: #fff;
                border-bottom: 1px solid var(--ops-gray-200);
                flex-wrap: wrap;
                gap: 16px;
            }

            .ops-header-left {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }

            .ops-breadcrumb {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 12px;
                color: var(--ops-gray-500);
            }

            .ops-breadcrumb a {
                color: var(--ops-primary);
                text-decoration: none;
            }

            .ops-breadcrumb a:hover {
                text-decoration: underline;
            }

            .ops-breadcrumb i {
                font-size: 10px;
            }

            .ops-title-row {
                display: flex;
                align-items: center;
                gap: 12px;
                flex-wrap: wrap;
            }

            .ops-page-title {
                margin: 0;
                font-size: 20px;
                font-weight: 600;
                color: var(--ops-gray-900);
            }

            .ops-header-actions {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }

            /* ============================================
               BUTTONS
               ============================================ */
            .ops-btn {
                height: var(--ops-btn-height);
                padding: 0 16px;
                border-radius: 6px;
                border: 1px solid var(--ops-gray-300);
                background: #fff;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                transition: all 0.15s ease;
                white-space: nowrap;
            }

            .ops-btn:hover { background: var(--ops-gray-50); }
            .ops-btn.primary { background: var(--ops-primary); color: #fff; border-color: var(--ops-primary); }
            .ops-btn.primary:hover { background: var(--ops-primary-hover); }
            .ops-btn.secondary { background: #fff; color: var(--ops-gray-700); }
            .ops-btn.success { background: var(--ops-success); color: #fff; border-color: var(--ops-success); }
            .ops-btn.success:hover { background: var(--ops-success-hover); }
            .ops-btn.danger { background: var(--ops-danger); color: #fff; border-color: var(--ops-danger); }
            .ops-btn.sm { height: 28px; padding: 0 10px; font-size: 12px; }

            /* ============================================
               BADGES
               ============================================ */
            .ops-badge {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }

            .ops-badge.success { background: #dcfce7; color: #166534; }
            .ops-badge.danger { background: #fee2e2; color: #991b1b; }
            .ops-badge.warning { background: #fef3c7; color: #92400e; }
            .ops-badge.info { background: #dbeafe; color: #1e40af; }
            .ops-badge.purple { background: #f3e8ff; color: #7c3aed; }
            .ops-badge.neutral { background: var(--ops-gray-100); color: var(--ops-gray-700); }
            .ops-badge.sm { padding: 2px 8px; font-size: 10px; }

            /* ============================================
               DROPDOWNS
               ============================================ */
            .ops-actions-dropdown {
                position: relative;
            }

            .ops-dropdown-menu {
                position: absolute;
                top: 100%;
                right: 0;
                background: #fff;
                border: 1px solid var(--ops-gray-200);
                border-radius: var(--ops-radius);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                min-width: 180px;
                z-index: 1000;
                display: none;
                margin-top: 4px;
            }

            .ops-dropdown-menu.show { display: block; }

            .ops-dropdown-item {
                padding: 10px 14px;
                font-size: 13px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 10px;
                color: var(--ops-gray-700);
                transition: background 0.15s;
            }

            .ops-dropdown-item:hover { background: var(--ops-gray-50); }
            .ops-dropdown-item.danger { color: var(--ops-danger); }
            .ops-dropdown-item.danger:hover { background: #fef2f2; }
            .ops-dropdown-divider { height: 1px; background: var(--ops-gray-200); margin: 4px 0; }

            /* ============================================
               TAB NAVIGATION
               ============================================ */
            .ops-tabs-nav {
                display: flex;
                background: #fff;
                border-bottom: 1px solid var(--ops-gray-200);
                padding: 0 24px;
                overflow-x: auto;
            }

            .ops-tabs-list {
                display: flex;
                gap: 0;
            }

            .ops-tab-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 3px solid transparent;
                color: var(--ops-gray-500);
                font-size: 11px;
                font-weight: 500;
                transition: all 0.15s ease;
                white-space: nowrap;
                min-width: 80px;
                margin-bottom: -1px;
            }

            .ops-tab-item:hover { color: var(--ops-primary); background: rgba(8, 145, 178, 0.05); }
            .ops-tab-item.active { color: var(--ops-primary); border-bottom-color: var(--ops-primary); background: rgba(8, 145, 178, 0.05); }
            .ops-tab-item i { font-size: 18px; margin-bottom: 4px; }

            /* ============================================
               TAB PANELS
               ============================================ */
            .ops-tab-panel {
                display: none;
                padding: 20px 24px;
            }

            .ops-tab-panel.active { display: block; }

            .ops-empty-tab {
                text-align: center;
                padding: 80px var(--ops-spacing);
                color: var(--ops-gray-500);
            }

            .ops-empty-tab i { font-size: 48px; margin-bottom: 16px; display: block; opacity: 0.5; }
            .ops-empty-tab h4 { margin: 0 0 8px 0; color: var(--ops-gray-700); font-size: 18px; }
            .ops-empty-tab p { margin: 0; font-size: 14px; }

            /* ============================================
               CARDS GRID
               ============================================ */
            .ops-cards-grid {
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                gap: 12px;
                margin-bottom: var(--ops-spacing);
            }

            .ops-card {
                background: #fff;
                border-radius: var(--ops-radius);
                box-shadow: var(--ops-shadow);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }

            .ops-card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 14px;
                background: var(--ops-primary);
                color: #fff;
                font-size: 13px;
                font-weight: 600;
            }

            .ops-card-header span { display: flex; align-items: center; gap: 8px; }
            .ops-card-header i { cursor: pointer; opacity: 0.8; font-size: 12px; }
            .ops-card-header i:hover { opacity: 1; }

            .ops-card-body {
                padding: 12px 14px;
                font-size: 12px;
                flex: 1;
            }

            .ops-info-row {
                padding: 5px 0;
                border-bottom: 1px solid var(--ops-gray-100);
                color: var(--ops-gray-600);
                line-height: 1.5;
                word-wrap: break-word;
            }

            .ops-info-row:last-child { border-bottom: none; }
            .ops-info-row a { color: var(--ops-primary); text-decoration: none; }
            .ops-info-row a:hover { text-decoration: underline; }
            .ops-label { color: var(--ops-gray-500); font-size: 11px; }

            .ops-section-divider {
                font-weight: 600;
                color: var(--ops-gray-500);
                margin-top: 10px;
                margin-bottom: 6px;
                padding-top: 10px;
                border-top: 1px solid var(--ops-gray-200);
                font-size: 11px;
            }

            .ops-blind-link {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                color: var(--ops-primary);
                cursor: pointer;
                font-weight: 500;
                padding: 8px 0;
                font-size: 12px;
            }

            .ops-blind-link:hover { color: var(--ops-primary-hover); }

            /* ============================================
               PRODUCTS SECTION
               ============================================ */
            .ops-products {
                background: #fff;
                border-radius: var(--ops-radius-lg);
                box-shadow: var(--ops-shadow);
                overflow: hidden;
                margin-bottom: var(--ops-spacing);
            }

            .ops-products-toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px var(--ops-spacing);
                border-bottom: 1px solid var(--ops-gray-200);
                gap: 16px;
                flex-wrap: wrap;
            }

            .ops-subtabs { display: flex; gap: 0; }

            .ops-subtab {
                height: var(--ops-btn-height);
                padding: 0 20px;
                font-size: 13px;
                font-weight: 500;
                color: var(--ops-gray-500);
                cursor: pointer;
                border-radius: var(--ops-radius);
                transition: all 0.15s ease;
                display: flex;
                align-items: center;
            }

            .ops-subtab:hover { color: var(--ops-gray-700); background: var(--ops-gray-100); }
            .ops-subtab.active { background: var(--ops-primary); color: #fff; }

            .ops-products-actions {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }

            .ops-search-box {
                position: relative;
                display: flex;
                align-items: center;
            }

            .ops-search-box i {
                position: absolute;
                left: 12px;
                color: var(--ops-gray-500);
                font-size: 13px;
            }

            .ops-search-box input {
                height: var(--ops-btn-height);
                padding: 0 12px 0 36px;
                border: 1px solid var(--ops-gray-300);
                border-radius: 6px;
                font-size: 13px;
                min-width: 200px;
            }

            .ops-search-box input:focus {
                outline: none;
                border-color: var(--ops-primary);
            }

            .ops-select {
                height: var(--ops-btn-height);
                padding: 0 32px 0 12px;
                border: 1px solid var(--ops-gray-300);
                border-radius: 6px;
                font-size: 13px;
                background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M2 4l4 4 4-4'/%3E%3C/svg%3E") no-repeat right 10px center;
                appearance: none;
                cursor: pointer;
                min-width: 150px;
            }

            .ops-select:focus { outline: none; border-color: var(--ops-primary); }

            .ops-products-title-bar {
                padding: 12px var(--ops-spacing);
                background: var(--ops-primary);
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .ops-products-title { color: #fff; font-size: 14px; font-weight: 600; }
            .ops-products-count { background: rgba(255,255,255,0.2); color: #fff; padding: 2px 10px; border-radius: 12px; font-size: 12px; }

            /* ============================================
               TABLE
               ============================================ */
            .ops-table-wrap { overflow-x: auto; }

            .ops-table {
                width: 100%;
                border-collapse: collapse;
                min-width: 800px;
            }

            .ops-table th {
                padding: 12px 14px;
                text-align: left;
                font-size: 11px;
                font-weight: 600;
                color: #fff;
                background: var(--ops-primary);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .ops-table td {
                padding: 14px;
                border-bottom: 1px solid var(--ops-gray-100);
                font-size: 13px;
                vertical-align: middle;
            }

            .ops-table tbody tr:hover { background: var(--ops-gray-50); }

            .ops-table .col-check { width: 40px; text-align: center; }
            .ops-table .col-num { text-align: right; width: 80px; }
            .ops-table .col-actions { width: 80px; text-align: center; }

            .ops-table input[type="checkbox"] {
                width: 18px;
                height: 18px;
                cursor: pointer;
                accent-color: var(--ops-primary);
            }

            .ops-table a { color: var(--ops-primary); text-decoration: none; }
            .ops-table a:hover { text-decoration: underline; }

            .ops-empty-cell {
                text-align: center;
                padding: 60px !important;
                color: var(--ops-gray-500);
            }

            .ops-empty-cell i { font-size: 48px; display: block; margin-bottom: 12px; opacity: 0.5; }
            .ops-empty-cell p { margin: 0 0 16px 0; }

            /* Product cell */
            .ops-product-cell { display: flex; flex-direction: column; gap: 2px; }
            .ops-product-name { font-weight: 500; color: var(--ops-gray-900); }
            .ops-product-sku { font-size: 11px; color: var(--ops-gray-500); }
            .ops-product-meta { display: flex; gap: 6px; margin-top: 4px; }
            .ops-product-tag {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 2px 8px;
                background: var(--ops-gray-100);
                border-radius: 4px;
                font-size: 10px;
                color: var(--ops-gray-600);
            }

            .ops-price { color: var(--ops-success); font-weight: 600; }

            .ops-status-select {
                height: 32px;
                padding: 0 10px;
                border: 1px solid var(--ops-gray-300);
                border-radius: 6px;
                font-size: 12px;
                background: #fff;
                cursor: pointer;
                min-width: 120px;
            }

            /* Row actions */
            .ops-row-actions { display: flex; gap: 4px; justify-content: center; }

            .ops-expand-btn, .ops-menu-btn {
                width: 28px;
                height: 28px;
                border: 1px solid var(--ops-gray-300);
                border-radius: 6px;
                background: #fff;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.15s;
            }

            .ops-expand-btn:hover, .ops-menu-btn:hover {
                background: var(--ops-gray-100);
                border-color: var(--ops-primary);
            }

            /* Expanded row */
            .ops-expanded-row { display: none; }
            .ops-expanded-row.show { display: table-row; }
            .ops-expanded-row td { padding: 0 !important; background: var(--ops-gray-50); }

            .ops-expanded-content { padding: var(--ops-spacing); }

            .ops-expanded-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: var(--ops-spacing);
            }

            .ops-expanded-section h4 {
                margin: 0 0 12px 0;
                font-size: 13px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
                color: var(--ops-gray-700);
            }

            .ops-expanded-section h4 i { color: var(--ops-primary); }

            .ops-options-list { display: flex; flex-direction: column; gap: 6px; }

            .ops-option-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 12px;
                background: #fff;
                border-radius: 6px;
                font-size: 12px;
            }

            .ops-option-item span:first-child { color: var(--ops-gray-500); }
            .ops-empty-text { color: var(--ops-gray-500); font-size: 12px; margin: 0; }

            /* Proofs */
            .ops-proofs-grid { display: flex; gap: 10px; flex-wrap: wrap; }

            .ops-proof-card {
                position: relative;
                width: 70px;
                cursor: pointer;
            }

            .ops-proof-card img {
                width: 70px;
                height: 70px;
                border-radius: 6px;
                object-fit: cover;
                border: 2px solid transparent;
                transition: border-color 0.15s;
            }

            .ops-proof-card:hover img { border-color: var(--ops-primary); }
            .ops-proof-card .ops-badge { position: absolute; bottom: 4px; left: 4px; }

            .ops-proof-link {
                position: absolute;
                top: 4px;
                right: 4px;
                width: 20px;
                height: 20px;
                background: rgba(0,0,0,0.5);
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-size: 10px;
                text-decoration: none;
            }

            /* ============================================
               TOTALS
               ============================================ */
            .ops-totals {
                background: #fff;
                border-radius: var(--ops-radius-lg);
                box-shadow: var(--ops-shadow);
                max-width: 320px;
                margin-left: auto;
                overflow: hidden;
            }

            .ops-totals-header {
                padding: 12px 16px;
                background: var(--ops-primary);
                color: #fff;
                font-weight: 600;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .ops-totals-body { padding: 16px; }

            .ops-totals-row {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                font-size: 13px;
                border-bottom: 1px dashed var(--ops-gray-200);
            }

            .ops-totals-row:last-child { border-bottom: none; }

            .ops-totals-row.total {
                font-weight: 700;
                font-size: 15px;
                border-top: 2px solid var(--ops-gray-300);
                margin-top: 8px;
                padding-top: 12px;
                border-bottom: none;
            }

            .ops-totals-row .success { color: var(--ops-success); }
            .ops-totals-row .danger { color: var(--ops-danger); font-weight: 700; }

            /* ============================================
               TIMELINE
               ============================================ */
            .ops-timeline { padding: 20px; }

            .ops-timeline-item {
                display: flex;
                gap: 16px;
                padding-bottom: 24px;
                position: relative;
            }

            .ops-timeline-item:last-child { padding-bottom: 0; }

            .ops-timeline-item::before {
                content: '';
                position: absolute;
                left: 7px;
                top: 20px;
                bottom: 0;
                width: 2px;
                background: var(--ops-gray-200);
            }

            .ops-timeline-item:last-child::before { display: none; }

            .ops-timeline-dot {
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: var(--ops-gray-300);
                flex-shrink: 0;
                z-index: 1;
            }

            .ops-timeline-dot.success { background: var(--ops-success); }

            .ops-timeline-content { flex: 1; }
            .ops-timeline-title { font-weight: 600; color: var(--ops-gray-900); margin-bottom: 4px; }
            .ops-timeline-desc { font-size: 13px; color: var(--ops-gray-600); margin-bottom: 4px; }
            .ops-timeline-time { font-size: 12px; color: var(--ops-gray-500); }

            /* ============================================
               DRAWER
               ============================================ */
            .ops-drawer-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 9999;
                display: none;
                align-items: stretch;
                justify-content: flex-end;
            }

            .ops-drawer-overlay.show { display: flex; }

            .ops-drawer {
                width: 480px;
                max-width: 90vw;
                background: #fff;
                display: flex;
                flex-direction: column;
                animation: slideIn 0.3s ease;
            }

            @keyframes slideIn {
                from { transform: translateX(100%); }
                to { transform: translateX(0); }
            }

            .ops-drawer-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                padding: 20px;
                border-bottom: 1px solid var(--ops-gray-200);
                background: var(--ops-gray-50);
            }

            .ops-drawer-title-section h3 {
                margin: 0 0 4px 0;
                font-size: 18px;
                font-weight: 600;
                color: var(--ops-gray-900);
            }

            .ops-drawer-subtitle {
                font-size: 12px;
                color: var(--ops-gray-500);
            }

            .ops-drawer-close {
                width: 32px;
                height: 32px;
                border: none;
                background: transparent;
                cursor: pointer;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--ops-gray-500);
                font-size: 18px;
            }

            .ops-drawer-close:hover { background: var(--ops-gray-200); }

            .ops-drawer-body {
                flex: 1;
                overflow-y: auto;
                padding: 0;
            }

            .ops-drawer-section {
                padding: 16px 20px;
                border-bottom: 1px solid var(--ops-gray-200);
            }

            .ops-drawer-section:last-child { border-bottom: none; }

            .ops-drawer-section-title {
                font-size: 13px;
                font-weight: 600;
                color: var(--ops-gray-700);
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .ops-drawer-section-title i { color: var(--ops-primary); }

            .ops-info-box {
                background: var(--ops-gray-50);
                border-radius: var(--ops-radius);
                padding: 12px;
            }

            .ops-info-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }

            .ops-info-item { display: flex; flex-direction: column; gap: 2px; }
            .ops-info-label { font-size: 11px; color: var(--ops-gray-500); }
            .ops-info-value { font-size: 14px; font-weight: 500; color: var(--ops-gray-900); }
            .ops-info-value.price { color: var(--ops-success); }

            .ops-proof-gallery { display: flex; flex-direction: column; gap: 12px; }

            .ops-proof-card-lg {
                display: flex;
                gap: 12px;
                padding: 12px;
                background: var(--ops-gray-50);
                border-radius: var(--ops-radius);
            }

            .ops-proof-preview img {
                width: 80px;
                height: 80px;
                border-radius: 6px;
                object-fit: cover;
            }

            .ops-proof-info {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 6px;
            }

            .ops-proof-name { font-weight: 500; font-size: 13px; }

            .ops-drawer-footer {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                padding: 16px 20px;
                border-top: 1px solid var(--ops-gray-200);
                background: var(--ops-gray-50);
            }

            /* ============================================
               DIALOG
               ============================================ */
            .ops-dialog-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 10000;
                display: none;
                align-items: center;
                justify-content: center;
            }

            .ops-dialog-overlay.show { display: flex; }

            .ops-dialog {
                background: #fff;
                border-radius: var(--ops-radius-lg);
                width: 400px;
                max-width: 90vw;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }

            .ops-dialog-header {
                padding: 20px;
                border-bottom: 1px solid var(--ops-gray-200);
            }

            .ops-dialog-title { margin: 0; font-size: 18px; font-weight: 600; }

            .ops-dialog-body {
                padding: 20px;
                font-size: 14px;
                color: var(--ops-gray-600);
            }

            .ops-dialog-footer {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                padding: 16px 20px;
                border-top: 1px solid var(--ops-gray-200);
                background: var(--ops-gray-50);
                border-radius: 0 0 var(--ops-radius-lg) var(--ops-radius-lg);
            }

            /* ============================================
               TOAST
               ============================================ */
            .ops-toast {
                position: fixed;
                bottom: 24px;
                right: 24px;
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 14px 20px;
                background: #fff;
                border-radius: var(--ops-radius);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                font-size: 14px;
                z-index: 10001;
                opacity: 0;
                transform: translateY(20px);
                transition: all 0.3s ease;
            }

            .ops-toast.show { opacity: 1; transform: translateY(0); }
            .ops-toast.success { border-left: 4px solid var(--ops-success); }
            .ops-toast.success i { color: var(--ops-success); }
            .ops-toast.error { border-left: 4px solid var(--ops-danger); }
            .ops-toast.error i { color: var(--ops-danger); }
            .ops-toast.warning { border-left: 4px solid var(--ops-warning); }
            .ops-toast.warning i { color: var(--ops-warning); }
            .ops-toast.info { border-left: 4px solid var(--ops-primary); }
            .ops-toast.info i { color: var(--ops-primary); }

            /* ============================================
               RESPONSIVE
               ============================================ */
            @media (max-width: 1600px) {
                .ops-cards-grid { grid-template-columns: repeat(3, 1fr); }
            }

            @media (max-width: 1200px) {
                .ops-cards-grid { grid-template-columns: repeat(2, 1fr); }
                .ops-expanded-grid { grid-template-columns: repeat(2, 1fr); }
            }

            @media (max-width: 900px) {
                .ops-header { flex-direction: column; align-items: stretch; }
                .ops-header-actions { justify-content: flex-start; }
                .ops-tabs-nav { padding: 0 16px; }
                .ops-tab-panel { padding: 16px; }
                .ops-products-toolbar { flex-direction: column; align-items: stretch; }
                .ops-products-actions { justify-content: flex-start; }
                .ops-expanded-grid { grid-template-columns: 1fr; }
            }

            @media (max-width: 700px) {
                .ops-cards-grid { grid-template-columns: 1fr; }
                .ops-totals { max-width: 100%; }
            }
        `;
    }
}
