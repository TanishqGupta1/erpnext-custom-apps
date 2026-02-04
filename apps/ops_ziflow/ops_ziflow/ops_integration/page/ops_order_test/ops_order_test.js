/**
 * Order Test - Frappe UI + Bootstrap Version
 * Clean, minimal, uses built-in Frappe/Bootstrap components
 * Now with configurable card layout from OPS Order View Settings
 */

frappe.pages['ops-order-test'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Order View',
        single_column: true
    });

    new OrderTest(page);
};

class OrderTest {
    constructor(page) {
        this.page = page;
        this.wrapper = $(page.main);
        this.orderName = this.getOrderName();
        this.data = null;
        this.settings = null;  // Will hold dynamic configuration

        if (this.orderName) {
            this.init();
        } else {
            this.showError('No order specified. Use: /app/ops-order-test/ORDER-NAME');
        }

        frappe.router.on('change', () => {
            const newOrder = this.getOrderName();
            if (newOrder && newOrder !== this.orderName) {
                this.orderName = newOrder;
                this.init();
            }
        });
    }

    getOrderName() {
        const route = frappe.get_route();
        return route && route.length > 1 ? route[1] : null;
    }

    async init() {
        this.wrapper.html('<div class="text-center p-5"><div class="spinner-border text-primary"></div><p class="mt-3 text-muted">Loading order...</p></div>');

        try {
            // Load settings and order data in parallel
            const [settingsResult, orderResult] = await Promise.all([
                frappe.call({
                    method: 'ops_ziflow.ops_integration.doctype.ops_order_view_settings.ops_order_view_settings.get_view_settings'
                }),
                frappe.call({
                    method: 'ops_ziflow.api.order_form.get_order_full_data',
                    args: { order_name: this.orderName }
                })
            ]);

            this.settings = settingsResult.message;
            this.data = orderResult.message;
            this.render();
            this.bindEvents();
        } catch (e) {
            console.error('Error loading order:', e);
            this.showError('Failed to load order');
        }
    }

    showError(msg) {
        this.wrapper.html(`
            <div class="text-center p-5">
                <div class="text-danger mb-3"><i class="fa fa-exclamation-circle fa-3x"></i></div>
                <h5>${msg}</h5>
                <button class="btn btn-primary mt-3" onclick="history.back()">
                    <i class="fa fa-arrow-left"></i> Go Back
                </button>
            </div>
        `);
    }

    render() {
        const doc = this.data.order || this.data;
        const settings = this.settings || {};

        // Update page title using template
        let pageTitle = settings.page_title || 'Order #{ops_order_id}';
        pageTitle = pageTitle.replace(/{(\w+)}/g, (match, field) => doc[field] || match);
        this.page.set_title(pageTitle);

        // Add primary action
        this.page.set_primary_action('Update Order', () => this.updateOrder(), 'save');
        this.page.add_menu_item('Sync Order', () => this.syncOrder());
        this.page.add_menu_item('Send Email', () => this.sendEmail());
        this.page.add_menu_item('Download Invoice', () => this.downloadInvoice());

        // Add settings icon for admin users
        if (frappe.user_roles.includes('System Manager')) {
            this.page.add_menu_item('Configure View', () => this.openSettings(), 'fa-cog');
        }

        // Calculate grid class based on cards_per_row setting
        const cardsPerRow = settings.cards_per_row || 3;
        const colClass = cardsPerRow === 4 ? 'col-md-6 col-lg-3' :
                        cardsPerRow === 2 ? 'col-md-6' : 'col-md-6 col-lg-4';

        this.wrapper.html(`
            <div class="order-test-page">
                ${settings.show_breadcrumb !== false ? this.renderHeader() : ''}
                ${this.renderDynamicCards(colClass)}
                ${settings.show_products_table !== false ? `
                    <div class="row mt-4">
                        <div class="${settings.totals_position === 'Below Products' ? 'col-12' : 'col-lg-8'}">
                            ${this.renderProductsCard()}
                        </div>
                        ${settings.show_totals_panel !== false && settings.totals_position !== 'Below Products' ? `
                            <div class="col-lg-4">
                                ${this.renderTotalsCard()}
                            </div>
                        ` : ''}
                    </div>
                    ${settings.show_totals_panel !== false && settings.totals_position === 'Below Products' ? `
                        <div class="row mt-4">
                            <div class="col-12">
                                ${this.renderTotalsCard()}
                            </div>
                        </div>
                    ` : ''}
                ` : ''}
            </div>
            ${this.renderDrawer()}
            <div class="drawer-overlay" id="drawer-overlay"></div>
        `);
    }

    renderHeader() {
        const doc = this.data.order || this.data;
        const status = doc.order_status || 'Pending';
        const payment = doc.payment_status_title || 'Unpaid';

        const statusColor = {
            'Pending': 'orange', 'Processing': 'blue', 'In Production': 'blue',
            'Shipped': 'purple', 'Fulfilled': 'green', 'Completed': 'green',
            'Cancelled': 'red', 'On Hold': 'yellow'
        }[status] || 'gray';

        const paymentColor = payment === 'Paid' ? 'green' : payment === 'Unpaid' ? 'red' : 'orange';

        return `
            <div class="d-flex flex-wrap align-items-center gap-3 mb-4">
                <div>
                    <div class="text-muted small">
                        <a href="/app/ops-orders-list">Orders</a> / Order View
                    </div>
                    <h3 class="mb-0">${doc.order_name || 'Order'}</h3>
                </div>
                <div class="d-flex gap-2 ms-auto flex-wrap">
                    <span class="indicator-pill ${statusColor}">${status}</span>
                    <span class="indicator-pill ${paymentColor}">${payment}</span>
                </div>
            </div>
        `;
    }

    // Render cards dynamically based on settings
    renderDynamicCards(colClass) {
        const settings = this.settings || {};
        const cards = settings.cards || [];

        if (cards.length === 0) {
            // Fallback to hardcoded cards if no config
            return `
                <div class="row g-3">
                    ${this.renderOrderCard()}
                    ${this.renderCustomerCard()}
                    ${this.renderBillingCard()}
                    ${this.renderShippingCard()}
                    ${this.renderBlindCard()}
                    ${this.renderPaymentCard()}
                </div>
            `;
        }

        return `
            <div class="row g-3">
                ${cards.map(card => this.renderConfigCard(card, colClass)).join('')}
            </div>
        `;
    }

    // Render a single card based on configuration
    renderConfigCard(cardConfig, colClass) {
        const fields = cardConfig.fields || [];

        return `
            <div class="${colClass}">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center gap-2">
                        <div class="card-icon ${cardConfig.color || 'blue'}"><i class="fa ${cardConfig.icon || 'fa-file-text-o'}"></i></div>
                        <span class="fw-semibold">${cardConfig.title || 'Card'}</span>
                    </div>
                    <div class="card-body">
                        ${fields.map(field => this.renderConfigField(field)).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    // Render a single field based on configuration
    renderConfigField(fieldConfig) {
        const value = this.getFieldValue(fieldConfig.source, fieldConfig.field);
        const formattedValue = this.formatFieldValue(value, fieldConfig.type, fieldConfig);

        return `
            <div class="detail-row">
                <span class="detail-label">${fieldConfig.label}</span>
                <span class="detail-value">${formattedValue}</span>
            </div>
        `;
    }

    // Get field value from the appropriate data source
    getFieldValue(source, field) {
        const doc = this.data.order || this.data;

        switch(source) {
            case 'order':
                return doc[field];
            case 'customer':
                return this.data.customer?.[field] || doc[field];
            case 'billing_address':
                return this.data.billing_address?.[field] || doc[`billing_${field}`];
            case 'shipping_address':
                return this.data.shipping_address?.[field] || doc[`delivery_${field}`];
            case 'blind_shipping':
                return this.data.blind_shipping?.[field] || doc[`blind_${field}`];
            case 'shipping_info':
                return this.data.shipping_info?.[field] || doc[field];
            case 'financial_summary':
                return this.data.financial_summary?.[field] || doc[field];
            default:
                return doc[field];
        }
    }

    // Format field value based on type
    formatFieldValue(value, type, config) {
        if (value === null || value === undefined || value === '') {
            return '-';
        }

        switch(type) {
            case 'Date':
                return this.formatDate(value);
            case 'Datetime':
                return this.formatDateTime(value);
            case 'Currency':
                return '$' + parseFloat(value).toFixed(2);
            case 'Phone':
                const formatted = this.formatPhone(value);
                return config.is_link ? `<a href="${(config.link_template || 'tel:{value}').replace('{value}', value)}">${formatted}</a>` : formatted;
            case 'Email':
                return config.is_link ? `<a href="${(config.link_template || 'mailto:{value}').replace('{value}', value)}">${value}</a>` : value;
            case 'Link':
                return config.is_link ? `<a href="${(config.link_template || '{value}').replace('{value}', value)}">${value}</a>` : value;
            default:
                return config.is_link ? `<a href="${(config.link_template || '{value}').replace('{value}', value)}">${value}</a>` : value;
        }
    }

    // Fallback card renderers (used when no dynamic config)
    renderOrderCard() {
        const doc = this.data.order || this.data;
        return `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center gap-2">
                        <div class="card-icon blue"><i class="fa fa-file-text-o"></i></div>
                        <span class="fw-semibold">Order Details</span>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <span class="detail-label">Order ID</span>
                            <span class="detail-value">#${doc.ops_order_id || doc.name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Order Date</span>
                            <span class="detail-value">${this.formatDate(doc.orders_date_finished)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Production Due</span>
                            <span class="detail-value">${this.formatDate(doc.production_due_date)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Order Due</span>
                            <span class="detail-value">${this.formatDate(doc.orders_due_date)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Invoice #</span>
                            <span class="detail-value">${doc.invoice_number || '-'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderCustomerCard() {
        const doc = this.data.order || this.data;
        const c = this.data.customer || {};
        return `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center gap-2">
                        <div class="card-icon green"><i class="fa fa-user"></i></div>
                        <span class="fw-semibold">Customer</span>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <span class="detail-label">Name</span>
                            <span class="detail-value">${c.customer_name || doc.customers_name || '-'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Email</span>
                            <span class="detail-value">
                                <a href="mailto:${c.email || doc.customers_email_address}">${c.email || doc.customers_email_address || '-'}</a>
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Phone</span>
                            <span class="detail-value">
                                <a href="tel:${doc.customers_telephone}">${this.formatPhone(doc.customers_telephone)}</a>
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Company</span>
                            <span class="detail-value">${c.company || doc.customers_company || '-'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderBillingCard() {
        const doc = this.data.order || this.data;
        const b = this.data.billing_address || {};
        const addr = [b.street_address || doc.billing_street_address, b.city || doc.billing_city, b.state || doc.billing_state, b.postcode || doc.billing_postcode].filter(Boolean).join(', ');

        return `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center gap-2">
                        <div class="card-icon orange"><i class="fa fa-building"></i></div>
                        <span class="fw-semibold">Billing Address</span>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <span class="detail-label">Name</span>
                            <span class="detail-value">${b.name || doc.billing_name || '-'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Company</span>
                            <span class="detail-value">${b.company || doc.billing_company || '-'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Address</span>
                            <span class="detail-value">${addr || '-'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderShippingCard() {
        const doc = this.data.order || this.data;
        const s = this.data.shipping_address || {};
        const addr = [s.street_address || doc.delivery_street_address, s.city || doc.delivery_city, s.state || doc.delivery_state, s.postcode || doc.delivery_postcode].filter(Boolean).join(', ');

        return `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center gap-2">
                        <div class="card-icon purple"><i class="fa fa-truck"></i></div>
                        <span class="fw-semibold">Shipping Address</span>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <span class="detail-label">Name</span>
                            <span class="detail-value">${s.name || doc.delivery_name || '-'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Company</span>
                            <span class="detail-value">${s.company || doc.delivery_company || '-'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Address</span>
                            <span class="detail-value">${addr || '-'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderBlindCard() {
        const doc = this.data.order || this.data;
        const b = this.data.blind_shipping || {};
        const hasBlind = b.name || doc.blind_name;

        return `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center gap-2">
                        <div class="card-icon teal"><i class="fa fa-eye-slash"></i></div>
                        <span class="fw-semibold">Blind Shipping</span>
                    </div>
                    <div class="card-body">
                        ${hasBlind ? `
                            <div class="detail-row">
                                <span class="detail-label">Name</span>
                                <span class="detail-value">${b.name || doc.blind_name}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Company</span>
                                <span class="detail-value">${b.company || doc.blind_company || '-'}</span>
                            </div>
                        ` : `
                            <div class="text-center text-muted py-3">
                                <i class="fa fa-eye-slash fa-2x mb-2 opacity-50"></i>
                                <p class="mb-2">Not configured</p>
                                <button class="btn btn-sm btn-outline-primary">Enable</button>
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `;
    }

    renderPaymentCard() {
        const doc = this.data.order || this.data;
        return `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center gap-2">
                        <div class="card-icon pink"><i class="fa fa-credit-card"></i></div>
                        <span class="fw-semibold">Payment & Shipping</span>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <span class="detail-label">Shipping Method</span>
                            <span class="detail-value">${doc.shipping_mode || '-'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Carrier</span>
                            <span class="detail-value">${doc.courirer_company_name || '-'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Payment Method</span>
                            <span class="detail-value">${doc.payment_method_name || '-'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Transaction ID</span>
                            <span class="detail-value">${doc.transactionid || '-'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderProductsCard() {
        const products = this.data.products || this.data.order?.ops_order_products || [];
        const settings = this.settings || {};
        const columns = settings.products_columns || [
            {field: 'products_name', label: 'Product'},
            {field: 'product_status', label: 'Status'},
            {field: 'products_quantity', label: 'Qty'},
            {field: 'products_price', label: 'Price'},
            {field: 'final_price', label: 'Total'}
        ];

        return `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-2">
                        <i class="fa fa-cube text-primary"></i>
                        <span class="fw-semibold">Order Products</span>
                        <span class="badge bg-primary">${products.length}</span>
                    </div>
                    <button class="btn btn-sm btn-success">
                        <i class="fa fa-plus"></i> Add Product
                    </button>
                </div>
                <div class="card-body p-0">
                    ${products.length > 0 ? `
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th style="width:40px"><input type="checkbox" class="form-check-input"></th>
                                        <th>Product</th>
                                        <th style="width:120px">Status</th>
                                        <th style="width:60px" class="text-end">Qty</th>
                                        <th style="width:100px" class="text-end">Price</th>
                                        <th style="width:100px" class="text-end">Total</th>
                                        <th style="width:80px"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${products.map(p => this.renderProductRow(p)).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : `
                        <div class="text-center text-muted py-5">
                            <i class="fa fa-cube fa-3x mb-3 opacity-50"></i>
                            <p>No products in this order</p>
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    renderProductRow(p) {
        const id = p.orders_products_id || p.name;
        const name = p.products_title || p.products_name || 'Product';
        const sku = p.products_sku || '-';
        const status = p.product_status || 'Pending';
        const qty = p.products_quantity || 1;
        const price = parseFloat(p.products_price || 0);
        const total = parseFloat(p.final_price || price * qty);
        const proofs = p.proofs || [];
        const optCount = p.parsed_options?.options_count || 0;

        const statusColor = {
            'Pending': 'warning', 'In Design': 'info', 'In Production': 'info',
            'Completed': 'success', 'Shipped': 'primary', 'Fulfilled': 'success'
        }[status] || 'secondary';

        return `
            <tr>
                <td><input type="checkbox" class="form-check-input"></td>
                <td>
                    <div class="product-info">
                        <span class="product-name">${name}</span>
                        <span class="product-sku">SKU: ${sku}</span>
                    </div>
                    <div class="d-flex gap-1 mt-1">
                        ${optCount > 0 ? `<span class="badge bg-light text-dark">${optCount} options</span>` : ''}
                        ${proofs.length > 0 ? `<span class="badge bg-light text-dark"><i class="fa fa-file-image-o"></i> ${proofs.length}</span>` : ''}
                    </div>
                </td>
                <td>
                    <select class="form-select form-select-sm" onchange="OrderTestApp.updateStatus('${id}', this.value)">
                        <option ${status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option ${status === 'In Design' ? 'selected' : ''}>In Design</option>
                        <option ${status === 'In Production' ? 'selected' : ''}>In Production</option>
                        <option ${status === 'Completed' ? 'selected' : ''}>Completed</option>
                        <option ${status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                        <option ${status === 'Fulfilled' ? 'selected' : ''}>Fulfilled</option>
                    </select>
                </td>
                <td class="text-end">${qty}</td>
                <td class="text-end">$${price.toFixed(2)}</td>
                <td class="text-end fw-semibold">$${total.toFixed(2)}</td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary" onclick="OrderTestApp.openDrawer('${p.name || id}')" title="View Details">
                            <i class="fa fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-secondary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"></button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="#" onclick="OrderTestApp.editProduct('${id}')"><i class="fa fa-pencil me-2"></i>Edit</a></li>
                            <li><a class="dropdown-item" href="#" onclick="OrderTestApp.duplicateProduct('${id}')"><i class="fa fa-copy me-2"></i>Duplicate</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="#" onclick="OrderTestApp.createProof('${id}')"><i class="fa fa-file-image-o me-2"></i>Create Proof</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item text-danger" href="#" onclick="OrderTestApp.deleteProduct('${id}')"><i class="fa fa-trash me-2"></i>Delete</a></li>
                        </ul>
                    </div>
                </td>
            </tr>
        `;
    }

    renderTotalsCard() {
        const doc = this.data.order || this.data;
        const fin = this.data.financial_summary || {};

        const subtotal = fin.subtotal || parseFloat(doc.order_amount || 0);
        const shipping = fin.shipping_charges || parseFloat(doc.shipping_amount || 0);
        const tax = fin.tax || parseFloat(doc.tax_amount || 0);
        const total = fin.total || parseFloat(doc.total_amount || 0);
        const paid = fin.paid_amount || parseFloat(doc.partial_payment_paid || 0);
        const outstanding = fin.outstanding || parseFloat(doc.partial_payment_outstanding || total - paid);

        return `
            <div class="card">
                <div class="card-header d-flex align-items-center gap-2">
                    <i class="fa fa-calculator text-primary"></i>
                    <span class="fw-semibold">Order Summary</span>
                </div>
                <div class="card-body">
                    <div class="totals-row">
                        <span class="text-muted">Subtotal</span>
                        <span>$${subtotal.toFixed(2)}</span>
                    </div>
                    <div class="totals-row">
                        <span class="text-muted">Shipping</span>
                        <span>$${shipping.toFixed(2)}</span>
                    </div>
                    <div class="totals-row">
                        <span class="text-muted">Tax</span>
                        <span>$${tax.toFixed(2)}</span>
                    </div>
                    <div class="totals-row total">
                        <span>Total</span>
                        <span>$${total.toFixed(2)}</span>
                    </div>
                    <div class="totals-row">
                        <span class="text-muted">Paid</span>
                        <span class="text-success">$${paid.toFixed(2)}</span>
                    </div>
                    ${outstanding > 0 ? `
                        <div class="totals-row outstanding">
                            <span>Outstanding</span>
                            <span>$${outstanding.toFixed(2)}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderDrawer() {
        return `
            <div class="order-drawer" id="product-drawer">
                <div class="drawer-header">
                    <div>
                        <h5 class="mb-0" id="drawer-title">Product Details</h5>
                        <small class="text-muted" id="drawer-subtitle"></small>
                    </div>
                    <button class="btn btn-close" onclick="OrderTestApp.closeDrawer()"></button>
                </div>
                <div class="drawer-body" id="drawer-body"></div>
                <div class="drawer-footer">
                    <button class="btn btn-secondary" onclick="OrderTestApp.closeDrawer()">Close</button>
                    <button class="btn btn-primary" onclick="OrderTestApp.saveProduct()">Save Changes</button>
                </div>
            </div>
        `;
    }

    renderDrawerContent(product) {
        const options = product.parsed_options?.groups || [];
        const masterOpts = product.master_options || [];
        const proofs = product.proofs || [];
        const totalOptPrice = product.parsed_options?.total_options_price || 0;

        return `
            <!-- Summary -->
            <div class="mb-4">
                <h6 class="text-muted text-uppercase small mb-3">Summary</h6>
                <div class="row g-3">
                    <div class="col-6">
                        <div class="p-3 bg-light rounded">
                            <div class="text-muted small">Quantity</div>
                            <div class="fw-semibold">${product.products_quantity || 1}</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="p-3 bg-light rounded">
                            <div class="text-muted small">Status</div>
                            <div class="fw-semibold">${product.product_status || 'Pending'}</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="p-3 bg-light rounded">
                            <div class="text-muted small">Base Price</div>
                            <div class="fw-semibold text-success">$${parseFloat(product.products_price || 0).toFixed(2)}</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="p-3 bg-light rounded">
                            <div class="text-muted small">Total</div>
                            <div class="fw-semibold text-success">$${parseFloat(product.final_price || 0).toFixed(2)}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Options -->
            <div class="mb-4">
                <h6 class="text-muted text-uppercase small mb-3">
                    Product Options
                    ${totalOptPrice > 0 ? `<span class="badge bg-success ms-2">+$${totalOptPrice.toFixed(2)}</span>` : ''}
                </h6>
                ${options.length > 0 ? options.filter(g => g.name !== 'Ignore').flatMap(g => (g.options || []).map(o => `
                    <div class="option-item">
                        <span class="text-muted">${o.label || '-'}</span>
                        <span>
                            ${o.value || '-'}
                            ${o.price > 0 ? `<span class="option-price">+$${o.price.toFixed(2)}</span>` : ''}
                        </span>
                    </div>
                `)).join('') : '<p class="text-muted text-center py-3">No options</p>'}
            </div>

            <!-- Master Options -->
            <div class="mb-4">
                <h6 class="text-muted text-uppercase small mb-3">Master Options</h6>
                ${masterOpts.length > 0 ? masterOpts.map(o => `
                    <div class="option-item">
                        <span class="text-muted">${o.option_name || '-'}</span>
                        <span>${o.option_value || '-'}</span>
                    </div>
                `).join('') : '<p class="text-muted text-center py-3">No master options</p>'}
            </div>

            <!-- Proofs -->
            <div class="mb-4">
                <h6 class="text-muted text-uppercase small mb-3">
                    Ziflow Proofs
                    <span class="badge bg-secondary ms-2">${proofs.length}</span>
                </h6>
                ${proofs.length > 0 ? `
                    <div class="d-flex flex-wrap gap-2">
                        ${proofs.map(pr => `
                            <div class="proof-thumb" onclick="window.open('${pr.ziflow_url || '#'}', '_blank')" title="${pr.proof_name || 'Proof'}">
                                <img src="${pr.preview_url || '/assets/frappe/images/default-image.png'}"
                                     onerror="this.src='/assets/frappe/images/default-image.png'">
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <div class="text-center text-muted py-3">
                        <p class="mb-2">No proofs attached</p>
                        <button class="btn btn-sm btn-outline-primary" onclick="OrderTestApp.createProof('${product.orders_products_id}')">
                            <i class="fa fa-plus"></i> Create Proof
                        </button>
                    </div>
                `}
            </div>
        `;
    }

    bindEvents() {
        window.OrderTestApp = this;

        // Close drawer on overlay click
        $(document).on('click', '#drawer-overlay', () => this.closeDrawer());
    }

    openDrawer(productName) {
        const products = this.data.products || this.data.order?.ops_order_products || [];
        const product = products.find(p => p.name === productName || p.orders_products_id == productName);

        if (product) {
            $('#drawer-title').text(product.products_title || product.products_name || 'Product');
            $('#drawer-subtitle').text(`SKU: ${product.products_sku || '-'}`);
            $('#drawer-body').html(this.renderDrawerContent(product));
            $('#product-drawer').addClass('show');
            $('#drawer-overlay').addClass('show');
        }
    }

    closeDrawer() {
        $('#product-drawer').removeClass('show');
        $('#drawer-overlay').removeClass('show');
    }

    // Open settings configuration
    openSettings() {
        frappe.set_route('Form', 'OPS Order View Settings');
    }

    // Initialize default settings if needed
    async initializeDefaults() {
        try {
            const r = await frappe.call({
                method: 'ops_ziflow.ops_integration.doctype.ops_order_view_settings.ops_order_view_settings.initialize_default_settings'
            });
            frappe.show_alert({message: r.message.message, indicator: 'green'});
            this.init(); // Reload with new settings
        } catch (e) {
            frappe.show_alert({message: 'Failed to initialize settings', indicator: 'red'});
        }
    }

    // Actions
    updateOrder() { frappe.show_alert({message: 'Order updated', indicator: 'green'}); }
    syncOrder() { frappe.show_alert({message: 'Syncing...', indicator: 'blue'}); }
    sendEmail() {
        const doc = this.data.order || this.data;
        frappe.new_doc('Email', { recipients: doc.customers_email_address });
    }
    downloadInvoice() { window.open(`/printview?doctype=OPS Order&name=${this.orderName}&format=Invoice`, '_blank'); }
    updateStatus(id, status) { frappe.show_alert({message: `Status: ${status}`, indicator: 'green'}); }
    editProduct(id) { frappe.show_alert({message: 'Edit product', indicator: 'blue'}); }
    duplicateProduct(id) { frappe.show_alert({message: 'Duplicate product', indicator: 'blue'}); }
    createProof(id) { frappe.show_alert({message: 'Creating proof...', indicator: 'blue'}); }
    deleteProduct(id) { frappe.confirm('Delete this product?', () => frappe.show_alert({message: 'Deleted', indicator: 'red'})); }
    saveProduct() { frappe.show_alert({message: 'Saved', indicator: 'green'}); this.closeDrawer(); }

    // Utilities
    formatDate(d) {
        if (!d) return '-';
        try { return new Date(d).toLocaleDateString('en-US', {year: 'numeric', month: 'short', day: 'numeric'}); }
        catch { return '-'; }
    }

    formatDateTime(d) {
        if (!d) return '-';
        try { return new Date(d).toLocaleString('en-US', {year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'}); }
        catch { return '-'; }
    }

    formatPhone(p) {
        if (!p) return '-';
        const c = String(p).replace(/\D/g, '');
        return c.length === 10 ? `(${c.slice(0,3)}) ${c.slice(3,6)}-${c.slice(6)}` : p;
    }
}
