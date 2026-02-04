/**
 * OPS Order Product Enhancement
 * Expandable inline product options for OPS Order form
 *
 * Features:
 * - Expandable inline product options (not popup)
 * - Parse features_details JSON dynamically
 * - Display options in grouped sections with icons
 * - Show option prices inline
 * - Smooth slide-down animation
 * - Expand All / Collapse All toggle
 * - Enhanced product row display
 * - Inline Ziflow proof status
 */

(function() {
    'use strict';

    const OPSProductEnhancer = {
        frm: null,
        data: null,
        expandedRows: new Set(),

        init: function(frm, data) {
            this.frm = frm;
            this.data = data;
            this.expandedRows.clear();
            this.injectStyles();
            this.enhanceProductsGrid();
        },

        injectStyles: function() {
            if (document.getElementById('ops-product-styles')) return;

            const style = document.createElement('style');
            style.id = 'ops-product-styles';
            style.textContent = `
                /* Product Grid Enhancement */
                .ops-products-wrapper {
                    margin-top: 16px;
                }

                .ops-products-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 12px;
                }

                .ops-products-title {
                    font-size: 14px;
                    font-weight: 600;
                    color: #374151;
                }

                .ops-expand-all-btn {
                    background: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .ops-expand-all-btn:hover {
                    background: #e5e7eb;
                }

                /* Product Card */
                .ops-product-card {
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    margin-bottom: 8px;
                    overflow: hidden;
                    transition: box-shadow 0.2s;
                }

                .ops-product-card:hover {
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }

                .ops-product-card.expanded {
                    border-color: #6366f1;
                    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
                }

                /* Product Header Row */
                .ops-product-header {
                    display: grid;
                    grid-template-columns: 32px 1fr auto auto auto auto 32px;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    cursor: pointer;
                    background: #fafafa;
                    transition: background 0.2s;
                }

                .ops-product-header:hover {
                    background: #f3f4f6;
                }

                .ops-product-card.expanded .ops-product-header {
                    background: #eef2ff;
                    border-bottom: 1px solid #e5e7eb;
                }

                .ops-product-idx {
                    width: 24px;
                    height: 24px;
                    background: #e5e7eb;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 11px;
                    font-weight: 600;
                    color: #6b7280;
                }

                .ops-product-card.expanded .ops-product-idx {
                    background: #6366f1;
                    color: white;
                }

                .ops-product-info {
                    min-width: 0;
                }

                .ops-product-name {
                    font-weight: 500;
                    color: #111827;
                    font-size: 13px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .ops-product-sku {
                    font-size: 11px;
                    color: #6b7280;
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                }

                .ops-product-sku code {
                    background: #f3f4f6;
                    padding: 1px 4px;
                    border-radius: 3px;
                    font-size: 10px;
                }

                .ops-product-qty {
                    text-align: center;
                }

                .ops-product-qty-value {
                    font-size: 14px;
                    font-weight: 600;
                    color: #374151;
                }

                .ops-product-qty-label {
                    font-size: 10px;
                    color: #9ca3af;
                    text-transform: uppercase;
                }

                .ops-product-price {
                    text-align: right;
                }

                .ops-product-price-value {
                    font-size: 14px;
                    font-weight: 600;
                    color: #059669;
                }

                .ops-product-price-label {
                    font-size: 10px;
                    color: #9ca3af;
                }

                .ops-product-size {
                    display: flex;
                    gap: 4px;
                }

                .ops-size-chip {
                    background: #dbeafe;
                    color: #1e40af;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    white-space: nowrap;
                }

                .ops-product-badges {
                    display: flex;
                    gap: 6px;
                    align-items: center;
                }

                .ops-options-badge {
                    background: #fef3c7;
                    color: #92400e;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                }

                .ops-proof-indicator {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
                }

                .ops-proof-indicator.approved { background: #10b981; }
                .ops-proof-indicator.pending { background: #f59e0b; }
                .ops-proof-indicator.rejected { background: #ef4444; }
                .ops-proof-indicator.none { background: #d1d5db; }

                .ops-expand-icon {
                    color: #9ca3af;
                    transition: transform 0.2s;
                }

                .ops-product-card.expanded .ops-expand-icon {
                    transform: rotate(180deg);
                    color: #6366f1;
                }

                /* Expandable Options Panel */
                .ops-product-details {
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.3s ease-out;
                    background: white;
                }

                .ops-product-card.expanded .ops-product-details {
                    max-height: 2000px;
                    transition: max-height 0.5s ease-in;
                }

                .ops-product-details-inner {
                    padding: 16px;
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                }

                @media (max-width: 768px) {
                    .ops-product-details-inner {
                        grid-template-columns: 1fr;
                    }
                }

                /* Option Groups */
                .ops-option-group {
                    background: #f9fafb;
                    border-radius: 8px;
                    padding: 12px;
                }

                .ops-option-group-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 12px;
                    font-weight: 600;
                    color: #374151;
                    margin-bottom: 10px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #e5e7eb;
                }

                .ops-option-group-header i {
                    color: #6366f1;
                }

                .ops-option-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 6px 0;
                    font-size: 12px;
                    border-bottom: 1px dashed #e5e7eb;
                }

                .ops-option-row:last-child {
                    border-bottom: none;
                }

                .ops-option-label {
                    color: #6b7280;
                }

                .ops-option-value {
                    font-weight: 500;
                    color: #111827;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .ops-option-price {
                    font-size: 11px;
                    color: #059669;
                    background: #d1fae5;
                    padding: 1px 6px;
                    border-radius: 4px;
                }

                .ops-option-price.zero {
                    color: #6b7280;
                    background: #f3f4f6;
                }

                /* Options Total */
                .ops-options-total {
                    grid-column: 1 / -1;
                    display: flex;
                    justify-content: flex-end;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    background: #eef2ff;
                    border-radius: 6px;
                    margin-top: 8px;
                }

                .ops-options-total-label {
                    font-size: 12px;
                    color: #6b7280;
                }

                .ops-options-total-value {
                    font-size: 16px;
                    font-weight: 600;
                    color: #6366f1;
                }

                /* Proof Section in Details */
                .ops-product-proof-section {
                    grid-column: 1 / -1;
                    background: #fefce8;
                    border: 1px solid #fef08a;
                    border-radius: 8px;
                    padding: 12px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .ops-product-proof-thumbnail {
                    width: 60px;
                    height: 60px;
                    object-fit: cover;
                    border-radius: 6px;
                    background: #f3f4f6;
                }

                .ops-product-proof-info {
                    flex: 1;
                }

                .ops-product-proof-name {
                    font-weight: 500;
                    color: #111827;
                    font-size: 13px;
                }

                .ops-product-proof-status {
                    font-size: 12px;
                    margin-top: 4px;
                }

                .ops-product-proof-actions {
                    display: flex;
                    gap: 6px;
                }

                .ops-product-proof-btn {
                    padding: 6px 10px;
                    border-radius: 4px;
                    font-size: 11px;
                    cursor: pointer;
                    border: none;
                    transition: opacity 0.2s;
                }

                .ops-product-proof-btn:hover {
                    opacity: 0.9;
                }

                .ops-product-proof-btn.view {
                    background: #6366f1;
                    color: white;
                }

                .ops-product-proof-btn.approve {
                    background: #10b981;
                    color: white;
                }

                /* Product Actions */
                .ops-product-actions {
                    grid-column: 1 / -1;
                    display: flex;
                    justify-content: flex-end;
                    gap: 8px;
                    padding-top: 12px;
                    border-top: 1px solid #e5e7eb;
                }

                .ops-product-action-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    padding: 6px 10px;
                    border-radius: 4px;
                    font-size: 11px;
                    cursor: pointer;
                    border: 1px solid #e5e7eb;
                    background: white;
                    color: #374151;
                    transition: all 0.2s;
                }

                .ops-product-action-btn:hover {
                    background: #f3f4f6;
                    border-color: #d1d5db;
                }

                /* Raw Options Fallback */
                .ops-raw-options {
                    grid-column: 1 / -1;
                    background: #f9fafb;
                    border-radius: 6px;
                    padding: 12px;
                    font-family: monospace;
                    font-size: 11px;
                    white-space: pre-wrap;
                    word-break: break-all;
                    max-height: 200px;
                    overflow-y: auto;
                    color: #374151;
                }

                /* No Options Message */
                .ops-no-options {
                    grid-column: 1 / -1;
                    text-align: center;
                    color: #9ca3af;
                    padding: 16px;
                    font-size: 13px;
                }

                .ops-no-options i {
                    font-size: 24px;
                    margin-bottom: 8px;
                    display: block;
                }
            `;
            document.head.appendChild(style);
        },

        enhanceProductsGrid: function() {
            const productsField = this.frm.fields_dict.ops_order_products;
            if (!productsField || !productsField.$wrapper) return;

            // Get the grid wrapper
            const gridWrapper = productsField.$wrapper;
            const products = this.frm.doc.ops_order_products || [];

            if (products.length === 0) return;

            // Create enhanced products display
            const enhancedHtml = this.buildProductsHtml(products);

            // Insert after the grid or replace grid body
            const existingEnhanced = gridWrapper.find('.ops-products-wrapper');
            if (existingEnhanced.length) {
                existingEnhanced.replaceWith(enhancedHtml);
            } else {
                // Hide original grid rows and add enhanced view
                gridWrapper.find('.frappe-list').hide();
                gridWrapper.append(enhancedHtml);
            }

            // Bind events
            this.bindEvents(gridWrapper);
        },

        buildProductsHtml: function(products) {
            const enrichedProducts = this.data?.products || [];

            return `
                <div class="ops-products-wrapper">
                    <div class="ops-products-header">
                        <div class="ops-products-title">
                            <i class="fa fa-cube"></i> Order Products (${products.length})
                        </div>
                        <button class="ops-expand-all-btn" onclick="OPSProductEnhancer.toggleAll()">
                            <i class="fa fa-expand"></i> Expand All
                        </button>
                    </div>

                    ${products.map((product, index) => {
                        const enriched = enrichedProducts.find(p => p.name === product.name) || {};
                        return this.buildProductCard(product, enriched, index);
                    }).join('')}
                </div>
            `;
        },

        buildProductCard: function(product, enriched, index) {
            const options = enriched.parsed_options || this.parseOptions(product.features_details);
            const optionsCount = options.groups?.reduce((sum, g) => sum + (g.options?.length || 0), 0) || 0;
            const proofStatus = enriched.proof_status || product.ziflow_proof_status || 'none';
            const proofs = enriched.proofs || [];

            const size = this.formatSize(product);

            return `
                <div class="ops-product-card" data-idx="${index}" data-name="${product.name}">
                    <div class="ops-product-header" onclick="OPSProductEnhancer.toggleProduct(${index})">
                        <div class="ops-product-idx">${index + 1}</div>

                        <div class="ops-product-info">
                            <div class="ops-product-name">${product.products_title || product.products_name || 'Product'}</div>
                            <div class="ops-product-sku">
                                SKU: <code>${product.products_sku || 'N/A'}</code>
                            </div>
                        </div>

                        <div class="ops-product-qty">
                            <div class="ops-product-qty-value">${product.products_quantity || 1}</div>
                            <div class="ops-product-qty-label">Qty</div>
                        </div>

                        <div class="ops-product-price">
                            <div class="ops-product-price-value">$${(product.final_price || product.products_price || 0).toLocaleString()}</div>
                            <div class="ops-product-price-label">Total</div>
                        </div>

                        ${size ? `
                            <div class="ops-product-size">
                                <span class="ops-size-chip">${size}</span>
                            </div>
                        ` : '<div></div>'}

                        <div class="ops-product-badges">
                            ${optionsCount > 0 ? `
                                <span class="ops-options-badge">${optionsCount} options</span>
                            ` : ''}
                            <span class="ops-proof-indicator ${proofStatus.toLowerCase().replace(' ', '-')}"
                                  title="Proof: ${proofStatus}"></span>
                        </div>

                        <div class="ops-expand-icon">
                            <i class="fa fa-chevron-down"></i>
                        </div>
                    </div>

                    <div class="ops-product-details">
                        <div class="ops-product-details-inner">
                            ${this.buildOptionsHtml(options)}
                            ${this.buildProofSection(proofs, product)}
                            ${this.buildProductActions(product)}
                        </div>
                    </div>
                </div>
            `;
        },

        buildOptionsHtml: function(options) {
            if (!options || !options.groups || options.groups.length === 0) {
                if (options.raw) {
                    return `<div class="ops-raw-options">${this.escapeHtml(options.raw)}</div>`;
                }
                return `
                    <div class="ops-no-options">
                        <i class="fa fa-info-circle"></i>
                        No product options configured
                    </div>
                `;
            }

            let html = options.groups.map(group => `
                <div class="ops-option-group">
                    <div class="ops-option-group-header">
                        <i class="fa ${group.icon || 'fa-list'}"></i>
                        ${group.name}
                    </div>
                    ${group.options.map(opt => `
                        <div class="ops-option-row">
                            <span class="ops-option-label">${opt.label}</span>
                            <span class="ops-option-value">
                                ${opt.value}
                                <span class="ops-option-price ${opt.price === 0 ? 'zero' : ''}">
                                    ${opt.price_formatted || (opt.price > 0 ? '+$' + opt.price.toFixed(2) : 'included')}
                                </span>
                            </span>
                        </div>
                    `).join('')}
                </div>
            `).join('');

            if (options.total_options_price > 0) {
                html += `
                    <div class="ops-options-total">
                        <span class="ops-options-total-label">Options Total:</span>
                        <span class="ops-options-total-value">${options.total_formatted || '$' + options.total_options_price.toFixed(2)}</span>
                    </div>
                `;
            }

            return html;
        },

        buildProofSection: function(proofs, product) {
            if (!proofs || proofs.length === 0) {
                return `
                    <div class="ops-product-proof-section" style="background: #f3f4f6; border-color: #e5e7eb;">
                        <i class="fa fa-file-image-o" style="font-size: 24px; color: #9ca3af;"></i>
                        <div class="ops-product-proof-info">
                            <div style="color: #6b7280;">No proof attached</div>
                        </div>
                        <button class="ops-product-proof-btn view" onclick="OPSProductEnhancer.createProof('${product.name}')">
                            <i class="fa fa-plus"></i> Create Proof
                        </button>
                    </div>
                `;
            }

            const proof = proofs[0]; // Show first proof
            return `
                <div class="ops-product-proof-section">
                    <img class="ops-product-proof-thumbnail"
                         src="${proof.preview_url || '/assets/frappe/images/default-image.png'}"
                         onerror="this.src='/assets/frappe/images/default-image.png'"
                         alt="${proof.proof_name}">
                    <div class="ops-product-proof-info">
                        <div class="ops-product-proof-name">${proof.proof_name || 'Proof'}</div>
                        <div class="ops-product-proof-status">
                            <span class="ops-status-pill ops-status-${(proof.proof_status || 'pending').toLowerCase().replace(' ', '-')}">
                                ${proof.proof_status || 'Pending'}
                            </span>
                            ${proof.version ? `<span style="margin-left: 8px; color: #6b7280; font-size: 11px;">v${proof.version}</span>` : ''}
                        </div>
                    </div>
                    <div class="ops-product-proof-actions">
                        ${proof.ziflow_url ? `
                            <button class="ops-product-proof-btn view" onclick="window.open('${proof.ziflow_url}', '_blank')">
                                <i class="fa fa-external-link"></i> View
                            </button>
                        ` : ''}
                        ${proof.proof_status !== 'Approved' ? `
                            <button class="ops-product-proof-btn approve" onclick="OPSProductEnhancer.approveProof('${proof.name}')">
                                <i class="fa fa-check"></i> Approve
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        },

        buildProductActions: function(product) {
            return `
                <div class="ops-product-actions">
                    <button class="ops-product-action-btn" onclick="OPSProductEnhancer.copyProductDetails('${product.name}')">
                        <i class="fa fa-copy"></i> Copy Details
                    </button>
                    ${product.products_sku ? `
                        <button class="ops-product-action-btn" onclick="OPSProductEnhancer.viewProduct('${product.products_sku}')">
                            <i class="fa fa-external-link"></i> View Product
                        </button>
                    ` : ''}
                </div>
            `;
        },

        parseOptions: function(featuresDetails) {
            if (!featuresDetails) {
                return { groups: [], total_options_price: 0 };
            }

            try {
                const features = typeof featuresDetails === 'string'
                    ? JSON.parse(featuresDetails)
                    : featuresDetails;

                const groups = {};
                let totalPrice = 0;

                if (Array.isArray(features)) {
                    features.forEach(item => {
                        const groupName = item.group || item.category || 'Other';
                        if (!groups[groupName]) groups[groupName] = [];

                        const price = parseFloat(item.price || 0);
                        totalPrice += price;

                        groups[groupName].push({
                            label: item.name || item.label || '',
                            value: item.value || item.selected || '',
                            price: price,
                            price_formatted: price > 0 ? `+$${price.toFixed(2)}` : 'included'
                        });
                    });
                } else if (typeof features === 'object') {
                    Object.entries(features).forEach(([key, value]) => {
                        const groupName = 'Options';
                        if (!groups[groupName]) groups[groupName] = [];

                        if (typeof value === 'object') {
                            const price = parseFloat(value.price || 0);
                            totalPrice += price;

                            groups[groupName].push({
                                label: key,
                                value: value.value || value.selected || JSON.stringify(value),
                                price: price,
                                price_formatted: price > 0 ? `+$${price.toFixed(2)}` : 'included'
                            });
                        } else {
                            groups[groupName].push({
                                label: key,
                                value: String(value),
                                price: 0,
                                price_formatted: 'included'
                            });
                        }
                    });
                }

                const groupsList = Object.entries(groups).map(([name, options]) => ({
                    name,
                    options,
                    icon: this.getGroupIcon(name)
                }));

                return {
                    groups: groupsList,
                    total_options_price: totalPrice,
                    total_formatted: `$${totalPrice.toFixed(2)}`
                };

            } catch (e) {
                return {
                    groups: [],
                    total_options_price: 0,
                    raw: String(featuresDetails)
                };
            }
        },

        getGroupIcon: function(groupName) {
            const icons = {
                'Paper': 'fa-file',
                'Paper & Size': 'fa-file',
                'Size': 'fa-expand',
                'Finishing': 'fa-magic',
                'Design': 'fa-paint-brush',
                'Printing': 'fa-print',
                'Binding': 'fa-book',
                'Packaging': 'fa-box',
                'Delivery': 'fa-truck',
                'Options': 'fa-cog',
                'General': 'fa-cog',
                'Other': 'fa-list'
            };
            return icons[groupName] || 'fa-list';
        },

        formatSize: function(product) {
            const width = product.product_width;
            const height = product.product_height;
            const unit = product.product_size_unit || '';

            if (width && height) {
                return `${width}×${height}${unit}`;
            }
            return null;
        },

        escapeHtml: function(str) {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        },

        bindEvents: function(wrapper) {
            // Events are bound inline via onclick for simplicity
        },

        // Public Methods
        toggleProduct: function(idx) {
            const card = document.querySelector(`.ops-product-card[data-idx="${idx}"]`);
            if (!card) return;

            if (this.expandedRows.has(idx)) {
                card.classList.remove('expanded');
                this.expandedRows.delete(idx);
            } else {
                card.classList.add('expanded');
                this.expandedRows.add(idx);
            }

            this.updateExpandAllButton();
        },

        toggleAll: function() {
            const cards = document.querySelectorAll('.ops-product-card');
            const allExpanded = this.expandedRows.size === cards.length;

            cards.forEach((card, idx) => {
                if (allExpanded) {
                    card.classList.remove('expanded');
                    this.expandedRows.delete(idx);
                } else {
                    card.classList.add('expanded');
                    this.expandedRows.add(idx);
                }
            });

            this.updateExpandAllButton();
        },

        updateExpandAllButton: function() {
            const btn = document.querySelector('.ops-expand-all-btn');
            if (!btn) return;

            const cards = document.querySelectorAll('.ops-product-card');
            const allExpanded = this.expandedRows.size === cards.length;

            btn.innerHTML = allExpanded
                ? '<i class="fa fa-compress"></i> Collapse All'
                : '<i class="fa fa-expand"></i> Expand All';
        },

        copyProductDetails: function(productName) {
            const product = (this.frm.doc.ops_order_products || []).find(p => p.name === productName);
            if (!product) return;

            const text = [
                `Product: ${product.products_title || product.products_name}`,
                `SKU: ${product.products_sku || 'N/A'}`,
                `Quantity: ${product.products_quantity || 1}`,
                `Price: $${product.final_price || product.products_price || 0}`,
                product.product_width && product.product_height
                    ? `Size: ${product.product_width}×${product.product_height}${product.product_size_unit || ''}`
                    : null
            ].filter(Boolean).join('\n');

            navigator.clipboard.writeText(text).then(() => {
                frappe.show_alert({ message: 'Product details copied', indicator: 'green' });
            });
        },

        viewProduct: function(sku) {
            frappe.set_route('List', 'OPS Product', { products_sku: sku });
        },

        createProof: function(productName) {
            frappe.show_alert({ message: 'Creating proof...', indicator: 'blue' });
            // This would call the proof creation API
        },

        approveProof: function(proofName) {
            frappe.call({
                method: 'ops_ziflow.api.order_form.update_proof_status',
                args: {
                    proof_name: proofName,
                    status: 'Approved'
                },
                callback: (r) => {
                    if (r.message && r.message.success) {
                        frappe.show_alert({ message: 'Proof approved', indicator: 'green' });
                        if (this.frm) this.frm.reload_doc();
                    }
                }
            });
        }
    };

    // Listen for enhancement event from ops_order.js
    document.addEventListener('opsOrderEnhanceProducts', function(e) {
        const { frm, data } = e.detail;
        OPSProductEnhancer.init(frm, data);
    });

    // Make it globally accessible
    window.OPSProductEnhancer = OPSProductEnhancer;

})();
