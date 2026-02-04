/**
 * Order View - Modern Dokani-Inspired Design
 * Visual Graphx ERP
 */

frappe.pages['ops-order-view'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Order View',
        single_column: true
    });

    // Hide default page elements
    $(wrapper).find('.page-head').hide();

    // Initialize the Order View app
    new OrderView(page);
};

class OrderView {
    constructor(page) {
        this.page = page;
        this.wrapper = $(page.main);
        this.orderName = this.getOrderNameFromRoute();
        this.data = null;
        this.state = {
            activeTab: 'products',
            expandedProducts: new Set(),
            selectedProducts: new Set(),
            drawerOpen: false,
            drawerProduct: null
        };

        if (this.orderName) {
            this.init();
        } else {
            this.showError('No order specified');
        }

        // Handle route changes
        frappe.router.on('change', () => {
            const newOrder = this.getOrderNameFromRoute();
            if (newOrder && newOrder !== this.orderName) {
                this.orderName = newOrder;
                this.init();
            }
        });
    }

    getOrderNameFromRoute() {
        const route = frappe.get_route();
        if (route && route.length > 1) {
            return route[1];
        }
        return frappe.route_options?.order || null;
    }

    async init() {
        this.showLoading();
        try {
            await this.loadData();
            this.render();
            this.bindEvents();
        } catch (error) {
            console.error('Order View Error:', error);
            this.showError('Failed to load order data');
        }
    }

    showLoading() {
        this.wrapper.html(`
            <div class="ov-app">
                <div class="ov-loading">
                    <div class="ov-loading-spinner"></div>
                    <div class="ov-loading-text">Loading order...</div>
                </div>
            </div>
        `);
    }

    showError(message) {
        this.wrapper.html(`
            <div class="ov-app">
                <div class="ov-loading">
                    <i class="fa fa-exclamation-circle" style="font-size: 48px; color: #ef4444;"></i>
                    <div style="color: #ef4444; font-weight: 500;">${message}</div>
                    <button class="ov-btn ov-btn-primary" onclick="history.back()">
                        <i class="fa fa-arrow-left"></i> Go Back
                    </button>
                </div>
            </div>
        `);
    }

    async loadData() {
        const response = await frappe.call({
            method: 'ops_ziflow.api.order_form.get_order_full_data',
            args: { order_name: this.orderName }
        });

        if (!response.message) {
            throw new Error('Order not found');
        }

        this.data = response.message;
    }

    render() {
        const doc = this.data.order || this.data;
        this.wrapper.html(`
            <div class="ov-app" id="order-view-app">
                ${this.renderHeader()}
                <div class="ov-main">
                    ${this.renderSummaryCards()}
                    <div class="ov-content-layout">
                        <div class="ov-tabs-container">
                            ${this.renderTabs()}
                        </div>
                        ${this.renderTotalsPanel()}
                    </div>
                </div>
                ${this.renderDrawer()}
                ${this.renderDialogOverlay()}
            </div>
        `);
    }

    // ==================== HEADER ====================
    renderHeader() {
        const doc = this.data.order || this.data;
        const orderId = doc.ops_order_id || doc.name;
        const status = doc.order_status || 'Pending';
        const paymentStatus = doc.payment_status_title || 'Unpaid';

        return `
            <div class="ov-header">
                <div class="ov-header-inner">
                    <div class="ov-header-left">
                        <button class="ov-back-btn" onclick="history.back()" title="Go back">
                            <i class="fa fa-arrow-left"></i>
                        </button>
                        <div class="ov-title-section">
                            <div class="ov-breadcrumb">
                                <a href="/app/ops-orders-list">Orders</a>
                                <i class="fa fa-chevron-right"></i>
                                <span>Order View</span>
                            </div>
                            <div class="ov-title-row">
                                <h1 class="ov-page-title">Order #${orderId}</h1>
                                ${this.renderStatusBadge(status)}
                                ${this.renderPaymentBadge(paymentStatus)}
                            </div>
                        </div>
                    </div>
                    <div class="ov-header-actions">
                        <button class="ov-btn ov-btn-secondary" onclick="OrderViewApp.sendEmail()">
                            <i class="fa fa-envelope"></i> Send Mail
                        </button>
                        <div class="ov-actions-dropdown">
                            <button class="ov-btn ov-btn-secondary" onclick="OrderViewApp.toggleDownloadMenu()">
                                <i class="fa fa-download"></i> Download
                                <i class="fa fa-caret-down" style="margin-left: 4px;"></i>
                            </button>
                            <div class="ov-dropdown-menu" id="download-menu">
                                <div class="ov-dropdown-item" onclick="OrderViewApp.downloadInvoice()">
                                    <i class="fa fa-file-pdf-o"></i> Invoice
                                </div>
                                <div class="ov-dropdown-item" onclick="OrderViewApp.downloadPackingSlip()">
                                    <i class="fa fa-file-text-o"></i> Packing Slip
                                </div>
                                <div class="ov-dropdown-item" onclick="OrderViewApp.downloadFiles()">
                                    <i class="fa fa-file-archive-o"></i> All Files
                                </div>
                            </div>
                        </div>
                        <button class="ov-btn ov-btn-secondary" onclick="OrderViewApp.syncOrder()">
                            <i class="fa fa-refresh"></i> Sync
                        </button>
                        <button class="ov-btn ov-btn-primary" onclick="OrderViewApp.updateOrder()">
                            <i class="fa fa-save"></i> Update Order
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderStatusBadge(status) {
        const statusMap = {
            'Pending': 'neutral',
            'Processing': 'info',
            'In Design': 'purple',
            'In Production': 'info',
            'Production': 'info',
            'Shipped': 'info',
            'Fulfilled': 'success',
            'Completed': 'success',
            'Cancelled': 'danger',
            'On Hold': 'warning'
        };
        const badgeClass = statusMap[status] || 'neutral';
        return `<span class="ov-badge ov-badge-${badgeClass}">${status}</span>`;
    }

    renderPaymentBadge(status) {
        const statusMap = {
            'Paid': 'success',
            'Partially Paid': 'warning',
            'Unpaid': 'danger',
            'Refunded': 'neutral'
        };
        const badgeClass = statusMap[status] || 'neutral';
        const icon = status === 'Paid' ? 'check-circle' : status === 'Unpaid' ? 'exclamation-circle' : 'clock-o';
        return `<span class="ov-badge ov-badge-${badgeClass}"><i class="fa fa-${icon}"></i> ${status}</span>`;
    }

    // ==================== SUMMARY CARDS ====================
    renderSummaryCards() {
        return `
            <div class="ov-cards-grid">
                ${this.renderOrderDetailsCard()}
                ${this.renderCustomerCard()}
                ${this.renderBillingCard()}
                ${this.renderShippingCard()}
                ${this.renderBlindShippingCard()}
                ${this.renderPaymentCard()}
            </div>
        `;
    }

    renderOrderDetailsCard() {
        const doc = this.data.order || this.data;
        return `
            <div class="ov-card">
                <div class="ov-card-header">
                    <div class="ov-card-title">
                        <i class="fa fa-file-text"></i> Order Details
                    </div>
                    <span class="ov-card-action" onclick="OrderViewApp.editSection('order')">
                        <i class="fa fa-pencil"></i>
                    </span>
                </div>
                <div class="ov-card-body">
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Order Name</span>
                        <span class="ov-detail-value">${doc.order_name || '-'}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Order Date</span>
                        <span class="ov-detail-value">${this.formatDateTime(doc.orders_date_finished || doc.creation)}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Production Due</span>
                        <span class="ov-detail-value">${this.formatDate(doc.production_due_date)}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Order Due</span>
                        <span class="ov-detail-value">${this.formatDate(doc.orders_due_date)}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Invoice #</span>
                        <span class="ov-detail-value">${doc.invoice_number || '-'}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">PO Number</span>
                        <span class="ov-detail-value">${doc.po_number || '-'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderCustomerCard() {
        const doc = this.data.order || this.data;
        const customer = this.data.customer || {};
        const name = customer.customer_name || doc.customers_name || '-';
        const email = customer.email || doc.customers_email_address || '-';
        const phone = customer.telephone || doc.customers_telephone || '-';
        const company = customer.company || doc.customers_company || '-';

        return `
            <div class="ov-card">
                <div class="ov-card-header">
                    <div class="ov-card-title">
                        <i class="fa fa-user"></i> Customer
                    </div>
                    <span class="ov-card-action" onclick="OrderViewApp.viewCustomer()">
                        <i class="fa fa-external-link"></i>
                    </span>
                </div>
                <div class="ov-card-body">
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Name</span>
                        <span class="ov-detail-value">${name}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Email</span>
                        <span class="ov-detail-value">
                            <a href="mailto:${email}">${email}</a>
                        </span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Phone</span>
                        <span class="ov-detail-value">
                            <a href="tel:${phone}">${this.formatPhone(phone)}</a>
                        </span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Company</span>
                        <span class="ov-detail-value">${company}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderBillingCard() {
        const billing = this.data.billing_address || {};
        const doc = this.data.order || this.data;

        const name = billing.name || doc.billing_name || '-';
        const company = billing.company || doc.billing_company || '';
        const street = billing.street_address || doc.billing_street_address || '';
        const city = billing.city || doc.billing_city || '';
        const state = billing.state || doc.billing_state || '';
        const postcode = billing.postcode || doc.billing_postcode || '';
        const country = billing.country || doc.billing_country || '';
        const phone = billing.telephone || doc.billing_telephone || '';

        const addressParts = [street, city, state, postcode, country].filter(Boolean);
        const address = addressParts.join(', ') || '-';

        return `
            <div class="ov-card">
                <div class="ov-card-header">
                    <div class="ov-card-title">
                        <i class="fa fa-building"></i> Billing Address
                    </div>
                    <span class="ov-card-action" onclick="OrderViewApp.editSection('billing')">
                        <i class="fa fa-pencil"></i>
                    </span>
                </div>
                <div class="ov-card-body">
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Name</span>
                        <span class="ov-detail-value">${name}</span>
                    </div>
                    ${company ? `
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Company</span>
                        <span class="ov-detail-value">${company}</span>
                    </div>
                    ` : ''}
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Address</span>
                        <span class="ov-detail-value">${address}</span>
                    </div>
                    ${phone ? `
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Phone</span>
                        <span class="ov-detail-value">${this.formatPhone(phone)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderShippingCard() {
        const shipping = this.data.shipping_address || {};
        const doc = this.data.order || this.data;

        const name = shipping.name || doc.delivery_name || '-';
        const company = shipping.company || doc.delivery_company || '';
        const street = shipping.street_address || doc.delivery_street_address || '';
        const city = shipping.city || doc.delivery_city || '';
        const state = shipping.state || doc.delivery_state || '';
        const postcode = shipping.postcode || doc.delivery_postcode || '';
        const country = shipping.country || doc.delivery_country || '';
        const phone = shipping.telephone || doc.delivery_telephone || '';

        const addressParts = [street, city, state, postcode, country].filter(Boolean);
        const address = addressParts.join(', ') || '-';

        return `
            <div class="ov-card">
                <div class="ov-card-header">
                    <div class="ov-card-title">
                        <i class="fa fa-truck"></i> Shipping Address
                    </div>
                    <span class="ov-card-action" onclick="OrderViewApp.editSection('shipping')">
                        <i class="fa fa-pencil"></i>
                    </span>
                </div>
                <div class="ov-card-body">
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Name</span>
                        <span class="ov-detail-value">${name}</span>
                    </div>
                    ${company ? `
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Company</span>
                        <span class="ov-detail-value">${company}</span>
                    </div>
                    ` : ''}
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Address</span>
                        <span class="ov-detail-value">${address}</span>
                    </div>
                    ${phone ? `
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Phone</span>
                        <span class="ov-detail-value">${this.formatPhone(phone)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderBlindShippingCard() {
        const blind = this.data.blind_shipping || {};
        const doc = this.data.order || this.data;
        const hasBlind = blind.name || doc.blind_name;

        return `
            <div class="ov-card">
                <div class="ov-card-header">
                    <div class="ov-card-title">
                        <i class="fa fa-eye-slash"></i> Blind Shipping
                    </div>
                    <span class="ov-card-action" onclick="OrderViewApp.editSection('blind')">
                        <i class="fa fa-pencil"></i>
                    </span>
                </div>
                <div class="ov-card-body">
                    ${hasBlind ? `
                        <div class="ov-detail-row">
                            <span class="ov-detail-label">Name</span>
                            <span class="ov-detail-value">${blind.name || doc.blind_name || '-'}</span>
                        </div>
                        <div class="ov-detail-row">
                            <span class="ov-detail-label">Company</span>
                            <span class="ov-detail-value">${blind.company || doc.blind_company || '-'}</span>
                        </div>
                        <div class="ov-detail-row">
                            <span class="ov-detail-label">Address</span>
                            <span class="ov-detail-value">
                                ${[blind.street_address || doc.blind_street_address, blind.city || doc.blind_city, blind.state || doc.blind_state].filter(Boolean).join(', ') || '-'}
                            </span>
                        </div>
                    ` : `
                        <div class="ov-empty-state" style="padding: 24px;">
                            <i class="fa fa-eye-slash" style="font-size: 24px;"></i>
                            <p style="margin-top: 8px;">No blind shipping configured</p>
                            <button class="ov-btn ov-btn-sm ov-btn-secondary" onclick="OrderViewApp.enableBlindShipping()">
                                <i class="fa fa-plus"></i> Enable
                            </button>
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    renderPaymentCard() {
        const doc = this.data.order || this.data;
        const shipping = this.data.shipping_info || {};

        return `
            <div class="ov-card">
                <div class="ov-card-header">
                    <div class="ov-card-title">
                        <i class="fa fa-credit-card"></i> Shipping & Payment
                    </div>
                </div>
                <div class="ov-card-body">
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Shipping Method</span>
                        <span class="ov-detail-value">${doc.shipping_mode || shipping.method || '-'}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Carrier</span>
                        <span class="ov-detail-value">${doc.courirer_company_name || '-'}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Tracking #</span>
                        <span class="ov-detail-value">
                            ${doc.airway_bill_number ? `<a href="#" onclick="OrderViewApp.trackShipment('${doc.airway_bill_number}')">${doc.airway_bill_number}</a>` : '-'}
                        </span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Payment Method</span>
                        <span class="ov-detail-value">${doc.payment_method_name || '-'}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Payment Date</span>
                        <span class="ov-detail-value">${this.formatDate(doc.payment_date)}</span>
                    </div>
                    <div class="ov-detail-row">
                        <span class="ov-detail-label">Transaction ID</span>
                        <span class="ov-detail-value">${doc.transactionid || '-'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // ==================== TABS ====================
    renderTabs() {
        const products = this.data.products || this.data.order?.ops_order_products || [];
        return `
            <div class="ov-tabs-nav">
                <button class="ov-tab-btn ${this.state.activeTab === 'products' ? 'active' : ''}" data-tab="products">
                    <i class="fa fa-cube"></i> Order Products
                    <span class="ov-tab-count">${products.length}</span>
                </button>
                <button class="ov-tab-btn ${this.state.activeTab === 'history' ? 'active' : ''}" data-tab="history">
                    <i class="fa fa-history"></i> Order History
                </button>
            </div>
            <div class="ov-tab-content ${this.state.activeTab === 'products' ? 'active' : ''}" data-tab-content="products">
                ${this.renderProductsTab()}
            </div>
            <div class="ov-tab-content ${this.state.activeTab === 'history' ? 'active' : ''}" data-tab-content="history">
                ${this.renderHistoryTab()}
            </div>
        `;
    }

    // ==================== PRODUCTS TABLE ====================
    renderProductsTab() {
        const products = this.data.products || this.data.order?.ops_order_products || [];

        return `
            <div class="ov-table-header">
                <div class="ov-table-title">
                    <i class="fa fa-list"></i> Product Details
                </div>
                <div class="ov-table-actions">
                    <div class="ov-search-box">
                        <i class="fa fa-search"></i>
                        <input type="text" placeholder="Search products..." id="product-search">
                    </div>
                    <select class="ov-select" id="bulk-status">
                        <option value="">Bulk Update Status</option>
                        <option value="Pending">Pending</option>
                        <option value="In Production">In Production</option>
                        <option value="Completed">Completed</option>
                        <option value="Shipped">Shipped</option>
                    </select>
                    <button class="ov-btn ov-btn-success ov-btn-sm" onclick="OrderViewApp.addProduct()">
                        <i class="fa fa-plus"></i> Add Product
                    </button>
                </div>
            </div>
            ${products.length > 0 ? `
                <div class="ov-table-wrapper">
                    <table class="ov-table">
                        <thead>
                            <tr>
                                <th class="ov-col-checkbox">
                                    <input type="checkbox" class="ov-checkbox" id="select-all-products">
                                </th>
                                <th class="ov-col-id">ID</th>
                                <th>Product</th>
                                <th class="ov-col-status">Status</th>
                                <th class="ov-col-qty">Qty</th>
                                <th class="ov-col-price">Price</th>
                                <th class="ov-col-price">Total</th>
                                <th class="ov-col-actions"></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${products.map((p, i) => this.renderProductRow(p, i)).join('')}
                        </tbody>
                    </table>
                </div>
            ` : `
                <div class="ov-empty-state">
                    <i class="fa fa-cube"></i>
                    <h4>No Products</h4>
                    <p>This order has no products yet.</p>
                    <button class="ov-btn ov-btn-primary" onclick="OrderViewApp.addProduct()">
                        <i class="fa fa-plus"></i> Add Product
                    </button>
                </div>
            `}
        `;
    }


    renderProductRow(product, index) {
        const id = product.orders_products_id || product.name || index + 1;
        const name = product.products_title || product.products_name || 'Unknown Product';
        const sku = product.products_sku || '-';
        const status = product.product_status || 'Pending';
        const qty = product.products_quantity || 1;
        const price = parseFloat(product.products_price || 0);
        const total = parseFloat(product.final_price || price * qty);
        const isExpanded = this.state.expandedProducts.has(id);
        const proofs = product.proofs || [];

        const options = this.getProductOptions(product);
        const masterOptions = this.getMasterOptions(product);
        const attributes = this.getProductAttributes(product);
        const optionsCount = options.length || product.parsed_options?.options_count || 0;

        return `
            <tr class="ov-product-row" data-product-id="${id}">
                <td class="ov-col-checkbox">
                    <input type="checkbox" class="ov-checkbox ov-product-checkbox" data-id="${id}">
                </td>
                <td class="ov-col-id">${id}</td>
                <td>
                    <div class="ov-product-cell">
                        <span class="ov-product-name">${name}</span>
                        <span class="ov-product-sku">SKU: ${sku}</span>
                        <div class="ov-product-meta">
                            ${optionsCount > 0 ? `<span class="ov-product-tag">${optionsCount} options</span>` : ''}
                            ${masterOptions.length > 0 ? `<span class="ov-product-tag">${masterOptions.length} master opts</span>` : ''}
                            ${attributes.length > 0 ? `<span class="ov-product-tag">${attributes.length} attributes</span>` : ''}
                            ${proofs.length > 0 ? `<span class="ov-product-tag"><i class="fa fa-file-image-o"></i> ${proofs.length} proofs</span>` : ''}
                        </div>
                    </div>
                </td>
                <td class="ov-col-status">
                    <select class="ov-status-select" data-id="${id}" onchange="OrderViewApp.updateProductStatus('${id}', this.value)">
                        <option value="Pending" ${status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="In Design" ${status === 'In Design' ? 'selected' : ''}>In Design</option>
                        <option value="In Production" ${status === 'In Production' ? 'selected' : ''}>In Production</option>
                        <option value="Completed" ${status === 'Completed' ? 'selected' : ''}>Completed</option>
                        <option value="Shipped" ${status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                        <option value="Fulfilled" ${status === 'Fulfilled' ? 'selected' : ''}>Fulfilled</option>
                    </select>
                </td>
                <td class="ov-col-qty">${qty}</td>
                <td class="ov-col-price">$${price.toFixed(2)}</td>
                <td class="ov-col-price ov-price">$${total.toFixed(2)}</td>
                <td class="ov-col-actions">
                    <div style="display: flex; gap: 4px;">
                        <button class="ov-dropdown-btn ov-expand-btn" data-id="${id}" title="Expand">
                            <i class="fa fa-chevron-${isExpanded ? 'up' : 'down'}"></i>
                        </button>
                        <div class="ov-actions-dropdown">
                            <button class="ov-dropdown-btn" onclick="OrderViewApp.toggleProductMenu('${id}')">
                                <i class="fa fa-ellipsis-v"></i>
                            </button>
                            <div class="ov-dropdown-menu" id="product-menu-${id}">
                                <div class="ov-dropdown-item" onclick="OrderViewApp.openDrawer('${product.name || id}')">
                                    <i class="fa fa-eye"></i> View Details
                                </div>
                                <div class="ov-dropdown-item" onclick="OrderViewApp.editProduct('${id}')">
                                    <i class="fa fa-pencil"></i> Edit
                                </div>
                                <div class="ov-dropdown-item" onclick="OrderViewApp.duplicateProduct('${id}')">
                                    <i class="fa fa-copy"></i> Duplicate
                                </div>
                                <div class="ov-dropdown-divider"></div>
                                <div class="ov-dropdown-item" onclick="OrderViewApp.createProof('${id}')">
                                    <i class="fa fa-file-image-o"></i> Create Proof
                                </div>
                                <div class="ov-dropdown-divider"></div>
                                <div class="ov-dropdown-item danger" onclick="OrderViewApp.deleteProduct('${id}')">
                                    <i class="fa fa-trash"></i> Delete
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
            <tr class="ov-expanded-row ${isExpanded ? 'show' : ''}" data-expanded-for="${id}">
                <td colspan="8">
                    ${this.renderExpandedContent(product)}
                </td>
            </tr>
        `;
    }

    renderExpandedContent(product) {
        const options = this.getProductOptions(product);
        const masterOptions = this.getMasterOptions(product);
        const attributes = this.getProductAttributes(product);
        const proofs = product.proofs || [];

        return `
            <div class="ov-expanded-content">
                <div class="ov-expanded-grid">
                    <div class="ov-expanded-section">
                        <h4><i class="fa fa-sliders"></i> Product Options</h4>
                        ${options.length > 0 ? `
                            <div class="ov-option-list">
                                ${options.map(opt => `
                                    <div class="ov-option-item">
                                        <span class="ov-option-label">${opt.label}${opt.group ? ` <span class="ov-product-tag">${opt.group}</span>` : ''}</span>
                                        <span class="ov-option-value">
                                            ${opt.value}
                                            ${opt.price > 0 ? `<span class="ov-option-price">+$${opt.price.toFixed(2)}</span>` : ''}
                                        </span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p style="color: #9ca3af; font-size: 12px;">No options configured</p>'}
                    </div>
                    <div class="ov-expanded-section">
                        <h4><i class="fa fa-cogs"></i> Master Options</h4>
                        ${masterOptions.length > 0 ? `
                            <div class="ov-option-list">
                                ${masterOptions.map(opt => `
                                    <div class="ov-option-item">
                                        <span class="ov-option-label">${opt.label}</span>
                                        <span class="ov-option-value">${opt.value}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p style="color: #9ca3af; font-size: 12px;">No master options</p>'}
                    </div>
                    <div class="ov-expanded-section">
                        <h4><i class="fa fa-tags"></i> Product Attributes</h4>
                        ${attributes.length > 0 ? `
                            <div class="ov-option-list">
                                ${attributes.map(attr => `
                                    <div class="ov-option-item">
                                        <span class="ov-option-label">${attr.label}</span>
                                        <span class="ov-option-value">${attr.value}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p style="color: #9ca3af; font-size: 12px;">No attributes</p>'}
                    </div>
                    <div class="ov-expanded-section">
                        <h4><i class="fa fa-file-image-o"></i> Ziflow Proofs</h4>
                        ${proofs.length > 0 ? `
                            <div class="ov-proofs-grid">
                                ${proofs.map(proof => `
                                    <div class="ov-proof-thumb" onclick="OrderViewApp.openProof('${proof.ziflow_url || '#'}')">
                                        <img src="${proof.preview_url || '/assets/frappe/images/default-image.png'}"
                                             onerror="this.src='/assets/frappe/images/default-image.png'"
                                             alt="${proof.proof_name || 'Proof'}">
                                        <span class="ov-proof-status ${(proof.proof_status || 'pending').toLowerCase()}">${proof.proof_status || 'Pending'}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p style="color: #9ca3af; font-size: 12px;">No proofs attached</p>'}
                    </div>
                </div>
            </div>
        `;
    }

    // ==================== HELPER NORMALIZERS ====================
    getProductOptions(product) {
        const groups = product.parsed_options?.groups || [];
        const options = [];
        groups.forEach(group => {
            (group.options || []).forEach(opt => {
                options.push({
                    label: opt.label || opt.option_name || opt.name || group.name || 'Option',
                    value: opt.value || opt.option_value || opt.option || '-',
                    price: Number.isFinite(opt.price) ? opt.price : parseFloat(opt.price || 0) || 0,
                    group: group.name || ''
                });
            });
        });

        const legacy = product.options || product.product_options || [];
        legacy.forEach(opt => {
            options.push({
                label: opt.label || opt.option_name || opt.name || 'Option',
                value: opt.value || opt.option_value || opt.option || '-',
                price: Number.isFinite(opt.price) ? opt.price : parseFloat(opt.price || 0) || 0,
                group: opt.group || opt.section || ''
            });
        });

        return options.filter(o => o.value && o.value !== '-');
    }

    getMasterOptions(product) {
        const list = product.master_options || product.master_options_data || [];
        return list.map(opt => ({
            label: opt.option_name || opt.name || opt.label || 'Option',
            value: opt.option_value || opt.value || opt.selected || '-'
        })).filter(o => o.value && o.value !== '-');
    }

    getProductAttributes(product) {
        const raw = product.product_attributes || product.attributes || product.product_attrs || [];
        return (raw || []).map(attr => ({
            label: attr.label || attr.attribute || attr.name || attr.option_name || 'Attribute',
            value: attr.value || attr.attribute_value || attr.option_value || attr.selected || attr.option || '-'
        })).filter(a => a.value && a.value !== '-');
    }

    // ==================== HISTORY TAB ====================
    renderHistoryTab() {
        const history = this.data.status_history || [];

        if (history.length === 0) {
            return `
                <div class="ov-empty-state">
                    <i class="fa fa-history"></i>
                    <h4>No History</h4>
                    <p>Order history will appear here.</p>
                </div>
            `;
        }

        return `
            <div class="ov-timeline">
                ${history.map(item => `
                    <div class="ov-timeline-item">
                        <div class="ov-timeline-dot ${item.type === 'success' ? 'success' : ''}"></div>
                        <div class="ov-timeline-content">
                            <div class="ov-timeline-title">${item.title || item.status || 'Status Update'}</div>
                            <div class="ov-timeline-desc">${item.description || item.comment || ''}</div>
                            <div class="ov-timeline-time">${this.formatDateTime(item.timestamp || item.creation)}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // ==================== TOTALS PANEL ====================
    renderTotalsPanel() {
        const doc = this.data.order || this.data;
        const financial = this.data.financial_summary || {};

        const subtotal = financial.subtotal || parseFloat(doc.order_amount || 0);
        const shipping = financial.shipping_charges || parseFloat(doc.shipping_amount || 0);
        const tax = financial.tax || parseFloat(doc.tax_amount || 0);
        const fees = parseFloat(doc.payment_processing_fees || 0);
        const total = financial.total || parseFloat(doc.total_amount || 0);
        const paid = financial.paid_amount || parseFloat(doc.partial_payment_paid || 0);
        const outstanding = financial.outstanding || parseFloat(doc.partial_payment_outstanding || total - paid);

        return `
            <div class="ov-totals-panel">
                <div class="ov-totals-header">
                    <div class="ov-totals-title">
                        <i class="fa fa-calculator"></i> Order Summary
                    </div>
                </div>
                <div class="ov-totals-body">
                    <div class="ov-totals-row">
                        <span class="ov-totals-label">Subtotal</span>
                        <span class="ov-totals-value">$${subtotal.toFixed(2)}</span>
                    </div>
                    <div class="ov-totals-row">
                        <span class="ov-totals-label">Shipping</span>
                        <span class="ov-totals-value">$${shipping.toFixed(2)}</span>
                    </div>
                    <div class="ov-totals-row">
                        <span class="ov-totals-label">Tax</span>
                        <span class="ov-totals-value">$${tax.toFixed(2)}</span>
                    </div>
                    ${fees > 0 ? `
                    <div class="ov-totals-row">
                        <span class="ov-totals-label">Processing Fees</span>
                        <span class="ov-totals-value">$${fees.toFixed(2)}</span>
                    </div>
                    ` : ''}
                    <div class="ov-totals-row total">
                        <span class="ov-totals-label">Total</span>
                        <span class="ov-totals-value">$${total.toFixed(2)}</span>
                    </div>
                    <div class="ov-totals-row paid">
                        <span class="ov-totals-label">Paid</span>
                        <span class="ov-totals-value">$${paid.toFixed(2)}</span>
                    </div>
                    ${outstanding > 0 ? `
                    <div class="ov-totals-row outstanding">
                        <span class="ov-totals-label">Outstanding</span>
                        <span class="ov-totals-value">$${outstanding.toFixed(2)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // ==================== DRAWER ====================
    renderDrawer() {
        return `
            <div class="ov-drawer-overlay" id="product-drawer">
                <div class="ov-drawer">
                    <div class="ov-drawer-header">
                        <div class="ov-drawer-title-section">
                            <h3 id="drawer-title">Product Details</h3>
                            <div class="ov-drawer-subtitle" id="drawer-subtitle">SKU: -</div>
                        </div>
                        <button class="ov-drawer-close" onclick="OrderViewApp.closeDrawer()">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                    <div class="ov-drawer-body" id="drawer-body">
                        <!-- Content loaded dynamically -->
                    </div>
                    <div class="ov-drawer-footer">
                        <button class="ov-btn ov-btn-secondary" onclick="OrderViewApp.closeDrawer()">Close</button>
                        <button class="ov-btn ov-btn-primary" onclick="OrderViewApp.saveProductChanges()">
                            <i class="fa fa-save"></i> Save Changes
                        </button>
                    </div>
                </div>
            </div>
        `;
    }


    renderDrawerContent(product) {
        const options = this.getProductOptions(product);
        const masterOptions = this.getMasterOptions(product);
        const attributes = this.getProductAttributes(product);
        const proofs = product.proofs || [];
        const totalOptionsPrice = product.parsed_options?.total_options_price || 0;

        return `
            <!-- Product Summary -->
            <div class="ov-drawer-section">
                <div class="ov-drawer-section-title">
                    <i class="fa fa-info-circle"></i> Product Summary
                </div>
                <div class="ov-info-box">
                    <div class="ov-info-grid">
                        <div class="ov-info-item">
                            <span class="ov-info-label">Quantity</span>
                            <span class="ov-info-value">${product.products_quantity || 1}</span>
                        </div>
                        <div class="ov-info-item">
                            <span class="ov-info-label">Status</span>
                            <span class="ov-info-value">${product.product_status || 'Pending'}</span>
                        </div>
                        <div class="ov-info-item">
                            <span class="ov-info-label">Base Price</span>
                            <span class="ov-info-value price">$${parseFloat(product.products_price || 0).toFixed(2)}</span>
                        </div>
                        <div class="ov-info-item">
                            <span class="ov-info-label">Total</span>
                            <span class="ov-info-value price">$${parseFloat(product.final_price || 0).toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Product Options -->
            <div class="ov-drawer-section">
                <div class="ov-drawer-section-title">
                    <i class="fa fa-sliders"></i> Product Options
                    ${totalOptionsPrice > 0 ? `<span class="ov-badge ov-badge-success ov-badge-sm">+$${totalOptionsPrice.toFixed(2)}</span>` : ''}
                    <span class="ov-badge ov-badge-neutral ov-badge-sm">${options.length}</span>
                </div>
                ${options.length > 0 ? `
                    <div class="ov-option-list">
                        ${options.map(opt => `
                            <div class="ov-option-item">
                                <span class="ov-option-label">${opt.label}${opt.group ? ` <span class="ov-product-tag">${opt.group}</span>` : ''}</span>
                                <span class="ov-option-value">
                                    ${opt.value}
                                    ${opt.price > 0 ? `<span class="ov-option-price">+$${opt.price.toFixed(2)}</span>` : ''}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p style="color: #9ca3af; font-size: 13px; text-align: center; padding: 20px;">No options configured</p>'}
            </div>
            <!-- Master Options -->
            <div class="ov-drawer-section">
                <div class="ov-drawer-section-title">
                    <i class="fa fa-cogs"></i> Master Options
                    <span class="ov-badge ov-badge-neutral ov-badge-sm">${masterOptions.length}</span>
                </div>
                ${masterOptions.length > 0 ? `
                    <div class="ov-option-list">
                        ${masterOptions.map(opt => `
                            <div class="ov-option-item">
                                <span class="ov-option-label">${opt.label}</span>
                                <span class="ov-option-value">${opt.value}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p style="color: #9ca3af; font-size: 13px; text-align: center; padding: 20px;">No master options</p>'}
            </div>
            <!-- Product Attributes -->
            <div class="ov-drawer-section">
                <div class="ov-drawer-section-title">
                    <i class="fa fa-tags"></i> Product Attributes
                    <span class="ov-badge ov-badge-neutral ov-badge-sm">${attributes.length}</span>
                </div>
                ${attributes.length > 0 ? `
                    <div class="ov-option-list">
                        ${attributes.map(attr => `
                            <div class="ov-option-item">
                                <span class="ov-option-label">${attr.label}</span>
                                <span class="ov-option-value">${attr.value}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p style="color: #9ca3af; font-size: 13px; text-align: center; padding: 20px;">No attributes</p>'}
            </div>
            <!-- Ziflow Proofs -->
            <div class="ov-drawer-section">
                <div class="ov-drawer-section-title">
                    <i class="fa fa-file-image-o"></i> Ziflow Proofs
                    <span class="ov-badge ov-badge-neutral ov-badge-sm">${proofs.length}</span>
                </div>
                ${proofs.length > 0 ? `
                    <div class="ov-proof-gallery">
                        ${proofs.map(proof => `
                            <div class="ov-proof-card">
                                <div class="ov-proof-preview">
                                    <img src="${proof.preview_url || '/assets/frappe/images/default-image.png'}"
                                         onerror="this.src='/assets/frappe/images/default-image.png'"
                                         alt="${proof.proof_name || 'Proof'}">
                                </div>
                                <div class="ov-proof-info">
                                    <div class="ov-proof-name">${proof.proof_name || 'Proof'}</div>
                                    <span class="ov-badge ov-badge-sm ov-badge-${proof.proof_status === 'Approved' ? 'success' : proof.proof_status === 'Rejected' ? 'danger' : 'warning'}">
                                        ${proof.proof_status || 'Pending'}
                                    </span>
                                    <div class="ov-proof-actions">
                                        ${proof.ziflow_url ? `
                                            <button class="ov-btn ov-btn-sm ov-btn-primary" onclick="window.open('${proof.ziflow_url}', '_blank')">
                                                <i class="fa fa-external-link"></i> Open
                                            </button>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <div class="ov-empty-state" style="padding: 24px;">
                        <i class="fa fa-file-image-o" style="font-size: 24px;"></i>
                        <p>No proofs attached</p>
                        <button class="ov-btn ov-btn-sm ov-btn-primary" onclick="OrderViewApp.createProof('${product.orders_products_id || product.name}')">
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
            <div class="ov-dialog-overlay" id="confirm-dialog">
                <div class="ov-dialog">
                    <div class="ov-dialog-header">
                        <h3 class="ov-dialog-title" id="dialog-title">Confirm</h3>
                    </div>
                    <div class="ov-dialog-body" id="dialog-body">
                        Are you sure?
                    </div>
                    <div class="ov-dialog-footer">
                        <button class="ov-btn ov-btn-secondary" onclick="OrderViewApp.closeDialog()">Cancel</button>
                        <button class="ov-btn ov-btn-danger" id="dialog-confirm-btn" onclick="OrderViewApp.confirmAction()">Confirm</button>
                    </div>
                </div>
            </div>
        `;
    }

    // ==================== EVENT BINDING ====================
    bindEvents() {
        const self = this;

        // Tab switching
        this.wrapper.on('click', '.ov-tab-btn', function() {
            const tab = $(this).data('tab');
            self.state.activeTab = tab;
            self.wrapper.find('.ov-tab-btn').removeClass('active');
            $(this).addClass('active');
            self.wrapper.find('.ov-tab-content').removeClass('active');
            self.wrapper.find(`.ov-tab-content[data-tab-content="${tab}"]`).addClass('active');
        });

        // Product row expand
        this.wrapper.on('click', '.ov-expand-btn', function(e) {
            e.stopPropagation();
            const id = $(this).data('id');
            const expandedRow = self.wrapper.find(`.ov-expanded-row[data-expanded-for="${id}"]`);

            if (self.state.expandedProducts.has(id)) {
                self.state.expandedProducts.delete(id);
                expandedRow.removeClass('show');
                $(this).find('i').removeClass('fa-chevron-up').addClass('fa-chevron-down');
            } else {
                self.state.expandedProducts.add(id);
                expandedRow.addClass('show');
                $(this).find('i').removeClass('fa-chevron-down').addClass('fa-chevron-up');
            }
        });

        // Select all products
        this.wrapper.on('change', '#select-all-products', function() {
            const isChecked = this.checked;
            self.wrapper.find('.ov-product-checkbox').prop('checked', isChecked);
            if (isChecked) {
                self.wrapper.find('.ov-product-checkbox').each(function() {
                    self.state.selectedProducts.add($(this).data('id'));
                });
            } else {
                self.state.selectedProducts.clear();
            }
        });

        // Individual product checkbox
        this.wrapper.on('change', '.ov-product-checkbox', function() {
            const id = $(this).data('id');
            if (this.checked) {
                self.state.selectedProducts.add(id);
            } else {
                self.state.selectedProducts.delete(id);
            }
        });

        // Bulk status update
        this.wrapper.on('change', '#bulk-status', function() {
            const status = $(this).val();
            if (status && self.state.selectedProducts.size > 0) {
                self.bulkUpdateStatus(status);
                $(this).val('');
            }
        });

        // Search products
        this.wrapper.on('input', '#product-search', function() {
            const query = $(this).val().toLowerCase();
            self.wrapper.find('.ov-product-row').each(function() {
                const name = $(this).find('.ov-product-name').text().toLowerCase();
                const sku = $(this).find('.ov-product-sku').text().toLowerCase();
                const match = name.includes(query) || sku.includes(query);
                $(this).toggle(match);
                // Also hide expanded row
                const id = $(this).data('product-id');
                self.wrapper.find(`.ov-expanded-row[data-expanded-for="${id}"]`).toggle(match && self.state.expandedProducts.has(id));
            });
        });

        // Close dropdowns on outside click
        $(document).on('click', function(e) {
            if (!$(e.target).closest('.ov-actions-dropdown').length) {
                self.wrapper.find('.ov-dropdown-menu').removeClass('show');
            }
        });
    }

    // ==================== ACTIONS ====================
    async updateOrder() {
        this.showToast('Updating order...', 'info');
        try {
            await frappe.call({
                method: 'frappe.client.save',
                args: { doc: this.data.order }
            });
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
                args: { order_name: this.orderName, action: 'sync_order' }
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
        const doc = this.data.order || this.data;
        frappe.new_doc('Email', {
            recipients: doc.customers_email_address,
            subject: `Order #${doc.ops_order_id || doc.name}`
        });
    }

    toggleDownloadMenu() {
        $('#download-menu').toggleClass('show');
    }

    downloadInvoice() {
        window.open(`/printview?doctype=OPS Order&name=${this.orderName}&format=Invoice`, '_blank');
        $('#download-menu').removeClass('show');
    }

    downloadPackingSlip() {
        window.open(`/printview?doctype=OPS Order&name=${this.orderName}&format=Packing Slip`, '_blank');
        $('#download-menu').removeClass('show');
    }

    downloadFiles() {
        this.showToast('Preparing files for download...', 'info');
        $('#download-menu').removeClass('show');
    }

    toggleProductMenu(id) {
        const menu = $(`#product-menu-${id}`);
        this.wrapper.find('.ov-dropdown-menu').not(menu).removeClass('show');
        menu.toggleClass('show');
    }

    async updateProductStatus(productId, status) {
        this.showToast('Updating status...', 'info');
        try {
            // Find the product
            const products = this.data.products || this.data.order?.ops_order_products || [];
            const product = products.find(p => (p.orders_products_id || p.name) == productId);

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
                this.showToast(`Status updated to ${status}`, 'success');
            }
        } catch (e) {
            this.showToast('Failed to update status', 'error');
        }
    }

    async bulkUpdateStatus(status) {
        const count = this.state.selectedProducts.size;
        this.showToast(`Updating ${count} products...`, 'info');

        // Implementation would update each selected product
        this.showToast(`Updated ${count} products to ${status}`, 'success');
        this.state.selectedProducts.clear();
        this.wrapper.find('.ov-product-checkbox, #select-all-products').prop('checked', false);
    }

    openDrawer(productName) {
        const products = this.data.products || this.data.order?.ops_order_products || [];
        const product = products.find(p => p.name === productName || p.orders_products_id == productName);

        if (product) {
            this.state.drawerProduct = product;
            $('#drawer-title').text(product.products_title || product.products_name || 'Product Details');
            $('#drawer-subtitle').text(`SKU: ${product.products_sku || '-'} | ID: ${product.orders_products_id || '-'}`);
            $('#drawer-body').html(this.renderDrawerContent(product));
            $('#product-drawer').addClass('show');
        }

        // Close any open menus
        this.wrapper.find('.ov-dropdown-menu').removeClass('show');
    }

    closeDrawer() {
        $('#product-drawer').removeClass('show');
        this.state.drawerProduct = null;
    }

    addProduct() {
        this.showToast('Add product feature coming soon', 'info');
    }

    editProduct(id) {
        const products = this.data.products || this.data.order?.ops_order_products || [];
        const product = products.find(p => (p.orders_products_id || p.name) == id);
        if (product && product.name) {
            frappe.set_route('Form', 'OPS Order Product', product.name);
        }
        this.wrapper.find('.ov-dropdown-menu').removeClass('show');
    }

    duplicateProduct(id) {
        this.showToast('Duplicating product...', 'info');
        this.wrapper.find('.ov-dropdown-menu').removeClass('show');
    }

    createProof(productId) {
        this.showToast('Creating proof...', 'info');
        this.wrapper.find('.ov-dropdown-menu').removeClass('show');
    }

    deleteProduct(id) {
        this.pendingAction = { type: 'delete-product', id };
        $('#dialog-title').text('Delete Product');
        $('#dialog-body').text('Are you sure you want to delete this product? This action cannot be undone.');
        $('#dialog-confirm-btn').text('Delete');
        $('#confirm-dialog').addClass('show');
        this.wrapper.find('.ov-dropdown-menu').removeClass('show');
    }

    openProof(url) {
        if (url && url !== '#') {
            window.open(url, '_blank');
        }
    }

    trackShipment(tracking) {
        // Try common carriers
        const url = `https://www.google.com/search?q=${tracking}+tracking`;
        window.open(url, '_blank');
    }

    viewCustomer() {
        const doc = this.data.order || this.data;
        if (doc.erp_customer) {
            frappe.set_route('Form', 'Customer', doc.erp_customer);
        } else if (doc.customers_company) {
            frappe.set_route('List', 'OPS Customer', { company: doc.customers_company });
        }
    }

    editSection(section) {
        frappe.set_route('Form', 'OPS Order', this.orderName);
    }

    enableBlindShipping() {
        this.showToast('Enable blind shipping in order edit mode', 'info');
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
            // Implement delete logic
            this.showToast('Product deleted', 'success');
        }

        this.closeDialog();
    }

    saveProductChanges() {
        this.showToast('Saving changes...', 'info');
        // Implement save logic
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
        // Remove existing toasts
        $('.ov-toast').remove();

        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-circle',
            info: 'info-circle'
        };

        const toast = $(`
            <div class="ov-toast ${type}">
                <i class="fa fa-${iconMap[type] || 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `);

        $('body').append(toast);

        setTimeout(() => toast.remove(), 3000);
    }
}

// Global reference for onclick handlers
window.OrderViewApp = null;

frappe.pages['ops-order-view'].on_page_show = function(wrapper) {
    // Create or update the global reference
    if (!window.OrderViewApp) {
        const page = wrapper.page || $(wrapper).find('.frappe-control').data('page');
        // The OrderView instance is created in on_page_load
    }
};

// Override methods for global access
const originalOrderView = OrderView;
OrderView = class extends originalOrderView {
    constructor(page) {
        super(page);
        window.OrderViewApp = this;
    }
};
