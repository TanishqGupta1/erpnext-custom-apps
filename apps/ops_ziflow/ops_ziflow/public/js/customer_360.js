/**
 * Customer 360 View - Client Script
 *
 * This script adds three embedded tabs to the Customer form:
 * 1. Orders - OPS Orders for this customer (last 6 months)
 * 2. Proofs - ZiFlow proofs for this customer
 * 3. Timeline - Unified communication log (Voice, Chat, Email)
 *
 * Features:
 * - Lazy loading: Data loads only when section is visible/clicked
 * - Pagination: Load more button for large datasets
 * - Refresh: Manual refresh buttons for each section
 * - Badge counts: Shows record counts in section headers
 */

frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        if (frm.is_new()) return;

        // Initialize Customer 360 View
        setup_customer_360(frm);
    },

    onload: function(frm) {
        // Initialize data containers
        frm.customer_360 = {
            orders_loaded: false,
            proofs_loaded: false,
            timeline_loaded: false,
            orders_data: [],
            proofs_data: [],
            timeline_data: [],
            orders_offset: 0,
            proofs_offset: 0,
            timeline_offset: 0,
            page_size: 20
        };
    }
});

function setup_customer_360(frm) {
    // Get summary counts for badges
    frappe.call({
        method: 'ops_ziflow.api.customer_360.get_customer_360_summary',
        args: { customer_name: frm.doc.name },
        async: true,
        callback: function(r) {
            if (r.message) {
                update_section_badges(frm, r.message);
            }
        }
    });

    // Setup section observers for lazy loading
    setup_lazy_loading(frm);

    // Render initial placeholders
    render_orders_placeholder(frm);
    render_proofs_placeholder(frm);
    render_timeline_placeholder(frm);
}

function update_section_badges(frm, counts) {
    // Update section labels with counts
    // This works if using Section Break with labels
    const orders_count = counts.orders || 0;
    const proofs_count = counts.proofs || 0;
    const comms_count = counts.communications || 0;

    // Store for later use
    frm.customer_360.counts = counts;

    // Update HTML field headers with badges
    if (frm.fields_dict.customer_orders_html) {
        const orders_header = `
            <div class="section-head" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h5>
                    <i class="fa fa-shopping-cart"></i> Recent Orders
                    <span class="badge badge-primary" style="background: var(--primary); padding: 3px 8px; border-radius: 10px; font-size: 11px;">${orders_count}</span>
                    <small class="text-muted" style="font-size: 11px; margin-left: 10px;">Last 12 months</small>
                </h5>
                <button class="btn btn-xs btn-default" onclick="refresh_orders_section('${frm.doc.name}')">
                    <i class="fa fa-refresh"></i> Refresh
                </button>
            </div>
        `;
        $(frm.fields_dict.customer_orders_html.wrapper).find('.section-head').remove();
        $(frm.fields_dict.customer_orders_html.wrapper).prepend(orders_header);
    }

    if (frm.fields_dict.customer_proofs_html) {
        const proofs_header = `
            <div class="section-head" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h5>
                    <i class="fa fa-file-image-o"></i> ZiFlow Proofs
                    <span class="badge badge-info" style="background: var(--cyan); padding: 3px 8px; border-radius: 10px; font-size: 11px;">${proofs_count}</span>
                </h5>
                <button class="btn btn-xs btn-default" onclick="refresh_proofs_section('${frm.doc.name}')">
                    <i class="fa fa-refresh"></i> Refresh
                </button>
            </div>
        `;
        $(frm.fields_dict.customer_proofs_html.wrapper).find('.section-head').remove();
        $(frm.fields_dict.customer_proofs_html.wrapper).prepend(proofs_header);
    }

    if (frm.fields_dict.customer_timeline_html) {
        const timeline_header = `
            <div class="section-head" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h5>
                    <i class="fa fa-comments"></i> Unified Timeline
                    <span class="badge badge-success" style="background: var(--green); padding: 3px 8px; border-radius: 10px; font-size: 11px;">${comms_count}</span>
                    <small class="text-muted" style="font-size: 11px; margin-left: 10px;">Last 12 months</small>
                </h5>
                <button class="btn btn-xs btn-default" onclick="refresh_timeline_section('${frm.doc.name}')">
                    <i class="fa fa-refresh"></i> Refresh
                </button>
            </div>
        `;
        $(frm.fields_dict.customer_timeline_html.wrapper).find('.section-head').remove();
        $(frm.fields_dict.customer_timeline_html.wrapper).prepend(timeline_header);
    }
}

function setup_lazy_loading(frm) {
    // Use Intersection Observer for lazy loading when sections become visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const fieldname = $(entry.target).data('fieldname');
                if (fieldname === 'customer_orders_html' && !frm.customer_360.orders_loaded) {
                    load_orders_data(frm);
                } else if (fieldname === 'customer_proofs_html' && !frm.customer_360.proofs_loaded) {
                    load_proofs_data(frm);
                } else if (fieldname === 'customer_timeline_html' && !frm.customer_360.timeline_loaded) {
                    load_timeline_data(frm);
                }
            }
        });
    }, { threshold: 0.1 });

    // Observe the HTML field wrappers
    setTimeout(() => {
        ['customer_orders_html', 'customer_proofs_html', 'customer_timeline_html'].forEach(fieldname => {
            if (frm.fields_dict[fieldname]) {
                const wrapper = frm.fields_dict[fieldname].wrapper;
                $(wrapper).attr('data-fieldname', fieldname);
                observer.observe(wrapper);
            }
        });
    }, 500);
}

// ========== ORDERS SECTION ==========

function render_orders_placeholder(frm) {
    if (!frm.fields_dict.customer_orders_html) return;

    $(frm.fields_dict.customer_orders_html.wrapper).find('.orders-content').remove();
    $(frm.fields_dict.customer_orders_html.wrapper).append(`
        <div class="orders-content">
            <div class="text-center text-muted" style="padding: 20px;">
                <i class="fa fa-spinner fa-spin"></i> Loading orders...
            </div>
        </div>
    `);
}

function load_orders_data(frm, append = false) {
    if (!append) {
        frm.customer_360.orders_offset = 0;
        frm.customer_360.orders_data = [];
    }

    frappe.call({
        method: 'ops_ziflow.api.customer_360.get_customer_orders',
        args: {
            customer_name: frm.doc.name,
            limit: frm.customer_360.page_size,
            offset: frm.customer_360.orders_offset
        },
        callback: function(r) {
            frm.customer_360.orders_loaded = true;
            if (r.message) {
                if (append) {
                    frm.customer_360.orders_data = frm.customer_360.orders_data.concat(r.message.data);
                } else {
                    frm.customer_360.orders_data = r.message.data;
                }
                frm.customer_360.orders_total = r.message.total;
                frm.customer_360.orders_message = r.message.message || '';
                render_orders_table(frm);
            }
        },
        error: function() {
            $(frm.fields_dict.customer_orders_html.wrapper).find('.orders-content').html(`
                <div class="text-center text-danger" style="padding: 20px;">
                    <i class="fa fa-exclamation-triangle"></i> Failed to load orders
                </div>
            `);
        }
    });
}

function render_orders_table(frm) {
    const orders = frm.customer_360.orders_data;
    const total = frm.customer_360.orders_total || 0;
    const message = frm.customer_360.orders_message || '';

    let html = '';

    if (!orders || orders.length === 0) {
        // Check if customer has no OPS link
        const no_ops_link = message && message.includes('No OPS');
        html = `
            <div class="text-center text-muted" style="padding: 30px;">
                <i class="fa fa-${no_ops_link ? 'unlink' : 'inbox'}" style="font-size: 24px;"></i>
                <p style="margin-top: 10px;">${no_ops_link ? 'Customer not linked to OPS Webstore' : 'No orders found in the last 12 months'}</p>
                ${no_ops_link ? '<small>Set the OPS Corporate ID in the Webstore tab to enable</small>' : ''}
            </div>
        `;
    } else {
        html = `
            <div class="table-responsive">
                <table class="table table-bordered table-hover" style="font-size: 12px; margin-bottom: 10px;">
                    <thead style="background: var(--bg-color);">
                        <tr>
                            <th>Order ID</th>
                            <th>Date</th>
                            <th>Status</th>
                            <th>Payment</th>
                            <th style="text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${orders.map(order => `
                            <tr style="cursor: pointer;" onclick="frappe.set_route('Form', 'OPS Order', '${order.name}')">
                                <td>
                                    <a href="/app/ops-order/${order.name}">${order.ops_order_id || order.name}</a>
                                    ${order.order_name ? `<br><small class="text-muted">${frappe.utils.escape_html(order.order_name.substring(0, 40))}</small>` : ''}
                                </td>
                                <td>${order.orders_date_finished || '-'}</td>
                                <td>${get_status_badge(order.order_status)}</td>
                                <td>${get_payment_badge(order.payment_status_title)}</td>
                                <td style="text-align: right; font-weight: 500;">${order.total_amount || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <small class="text-muted">Showing ${orders.length} of ${total} orders</small>
                ${orders.length < total ? `
                    <button class="btn btn-xs btn-default" onclick="load_more_orders('${frm.doc.name}')">
                        Load More <i class="fa fa-chevron-down"></i>
                    </button>
                ` : ''}
            </div>
        `;
    }

    $(frm.fields_dict.customer_orders_html.wrapper).find('.orders-content').html(html);
}

// ========== PROOFS SECTION ==========

function render_proofs_placeholder(frm) {
    if (!frm.fields_dict.customer_proofs_html) return;

    $(frm.fields_dict.customer_proofs_html.wrapper).find('.proofs-content').remove();
    $(frm.fields_dict.customer_proofs_html.wrapper).append(`
        <div class="proofs-content">
            <div class="text-center text-muted" style="padding: 20px;">
                <i class="fa fa-spinner fa-spin"></i> Loading proofs...
            </div>
        </div>
    `);
}

function load_proofs_data(frm, append = false) {
    if (!append) {
        frm.customer_360.proofs_offset = 0;
        frm.customer_360.proofs_data = [];
    }

    frappe.call({
        method: 'ops_ziflow.api.customer_360.get_customer_proofs',
        args: {
            customer_name: frm.doc.name,
            limit: frm.customer_360.page_size,
            offset: frm.customer_360.proofs_offset
        },
        callback: function(r) {
            frm.customer_360.proofs_loaded = true;
            if (r.message) {
                if (append) {
                    frm.customer_360.proofs_data = frm.customer_360.proofs_data.concat(r.message.data);
                } else {
                    frm.customer_360.proofs_data = r.message.data;
                }
                frm.customer_360.proofs_total = r.message.total;
                frm.customer_360.proofs_message = r.message.message || '';
                render_proofs_table(frm);
            }
        },
        error: function() {
            $(frm.fields_dict.customer_proofs_html.wrapper).find('.proofs-content').html(`
                <div class="text-center text-danger" style="padding: 20px;">
                    <i class="fa fa-exclamation-triangle"></i> Failed to load proofs
                </div>
            `);
        }
    });
}

function render_proofs_table(frm) {
    const proofs = frm.customer_360.proofs_data;
    const total = frm.customer_360.proofs_total || 0;
    const message = frm.customer_360.proofs_message || '';

    let html = '';

    if (!proofs || proofs.length === 0) {
        const no_ops_link = message && message.includes('No OPS');
        html = `
            <div class="text-center text-muted" style="padding: 30px;">
                <i class="fa fa-${no_ops_link ? 'unlink' : 'file-o'}" style="font-size: 24px;"></i>
                <p style="margin-top: 10px;">${no_ops_link ? 'Customer not linked to OPS Webstore' : 'No proofs found for this customer'}</p>
                ${no_ops_link ? '<small>Set the OPS Corporate ID in the Webstore tab to enable</small>' : ''}
            </div>
        `;
    } else {
        html = `
            <div class="table-responsive">
                <table class="table table-bordered table-hover" style="font-size: 12px; margin-bottom: 10px;">
                    <thead style="background: var(--bg-color);">
                        <tr>
                            <th>Proof</th>
                            <th>Status</th>
                            <th>Version</th>
                            <th>Comments</th>
                            <th>Modified</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${proofs.map(proof => `
                            <tr>
                                <td>
                                    <a href="/app/ops-ziflow-proof/${proof.name}">${frappe.utils.escape_html(proof.proof_name || proof.ziflow_proof_id)}</a>
                                    ${proof.ops_order ? `<br><small class="text-muted">Order: ${proof.ops_order}</small>` : ''}
                                </td>
                                <td>${get_proof_status_badge(proof.proof_status)}</td>
                                <td style="text-align: center;">v${proof.current_version || 1}</td>
                                <td style="text-align: center;">
                                    ${proof.unresolved_comments > 0
                                        ? `<span class="badge badge-warning">${proof.unresolved_comments} unresolved</span>`
                                        : (proof.total_comments > 0 ? `<span class="text-muted">${proof.total_comments}</span>` : '-')}
                                </td>
                                <td>${proof.modified || '-'}</td>
                                <td>
                                    <a href="/app/ops-ziflow-proof/${proof.name}" class="btn btn-xs btn-primary">
                                        <i class="fa fa-eye"></i> View
                                    </a>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <small class="text-muted">Showing ${proofs.length} of ${total} proofs</small>
                ${proofs.length < total ? `
                    <button class="btn btn-xs btn-default" onclick="load_more_proofs('${frm.doc.name}')">
                        Load More <i class="fa fa-chevron-down"></i>
                    </button>
                ` : ''}
            </div>
        `;
    }

    $(frm.fields_dict.customer_proofs_html.wrapper).find('.proofs-content').html(html);
}

// ========== TIMELINE SECTION ==========

function render_timeline_placeholder(frm) {
    if (!frm.fields_dict.customer_timeline_html) return;

    $(frm.fields_dict.customer_timeline_html.wrapper).find('.timeline-content').remove();
    $(frm.fields_dict.customer_timeline_html.wrapper).append(`
        <div class="timeline-content">
            <div class="text-center text-muted" style="padding: 20px;">
                <i class="fa fa-spinner fa-spin"></i> Loading timeline...
            </div>
        </div>
    `);
}

function load_timeline_data(frm, append = false) {
    if (!append) {
        frm.customer_360.timeline_offset = 0;
        frm.customer_360.timeline_data = [];
    }

    frappe.call({
        method: 'ops_ziflow.api.customer_360.get_customer_timeline',
        args: {
            customer_name: frm.doc.name,
            limit: frm.customer_360.page_size,
            offset: frm.customer_360.timeline_offset
        },
        callback: function(r) {
            frm.customer_360.timeline_loaded = true;
            if (r.message) {
                if (append) {
                    frm.customer_360.timeline_data = frm.customer_360.timeline_data.concat(r.message.data);
                } else {
                    frm.customer_360.timeline_data = r.message.data;
                }
                frm.customer_360.timeline_total = r.message.total;
                render_timeline_table(frm);
            }
        },
        error: function() {
            $(frm.fields_dict.customer_timeline_html.wrapper).find('.timeline-content').html(`
                <div class="text-center text-danger" style="padding: 20px;">
                    <i class="fa fa-exclamation-triangle"></i> Failed to load timeline
                </div>
            `);
        }
    });
}

function render_timeline_table(frm) {
    const timeline = frm.customer_360.timeline_data;
    const total = frm.customer_360.timeline_total || 0;

    let html = '';

    if (!timeline || timeline.length === 0) {
        html = `
            <div class="text-center text-muted" style="padding: 30px;">
                <i class="fa fa-comments-o" style="font-size: 24px;"></i>
                <p style="margin-top: 10px;">No communications found</p>
            </div>
        `;
    } else {
        html = `
            <div class="timeline-list" style="max-height: 500px; overflow-y: auto;">
                ${timeline.map(comm => `
                    <div class="timeline-item" style="border-left: 3px solid ${get_channel_color(comm.channel)}; padding: 10px 15px; margin-bottom: 10px; background: var(--bg-color); border-radius: 4px; cursor: pointer;"
                         onclick="frappe.set_route('Form', 'Communication', '${comm.name}')">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1;">
                                <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 5px;">
                                    ${get_channel_icon(comm.channel)}
                                    <strong>${comm.channel || 'Other'}</strong>
                                    ${get_direction_badge(comm.sent_or_received)}
                                    ${comm.has_attachment ? '<i class="fa fa-paperclip text-muted"></i>' : ''}
                                    ${comm.delivery_status ? get_delivery_badge(comm.delivery_status) : ''}
                                </div>
                                ${comm.subject ? `<div style="font-weight: 500; margin-bottom: 5px;">${frappe.utils.escape_html(comm.subject)}</div>` : ''}
                                ${comm.content_preview ? `
                                    <div class="text-muted" style="font-size: 11px;">
                                        ${frappe.utils.escape_html(comm.content_preview)}
                                    </div>
                                ` : ''}
                                <div style="font-size: 10px; color: var(--text-light); margin-top: 5px;">
                                    ${comm.sent_or_received === 'Sent' ? 'To: ' : 'From: '}
                                    ${comm.sent_or_received === 'Sent'
                                        ? frappe.utils.escape_html(comm.recipients || '-')
                                        : frappe.utils.escape_html(comm.sender_full_name || comm.sender || '-')}
                                </div>
                            </div>
                            <div style="text-align: right; min-width: 120px;">
                                <div style="font-size: 11px; color: var(--text-muted);">${comm.communication_date_formatted || '-'}</div>
                                ${comm.seen ? '<span class="text-success" style="font-size: 10px;"><i class="fa fa-check"></i> Seen</span>' : ''}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                <small class="text-muted">Showing ${timeline.length} of ${total} communications</small>
                ${timeline.length < total ? `
                    <button class="btn btn-xs btn-default" onclick="load_more_timeline('${frm.doc.name}')">
                        Load More <i class="fa fa-chevron-down"></i>
                    </button>
                ` : ''}
            </div>
        `;
    }

    $(frm.fields_dict.customer_timeline_html.wrapper).find('.timeline-content').html(html);
}

// ========== HELPER FUNCTIONS ==========

function get_status_badge(status) {
    const colors = {
        'Pending': 'orange',
        'Processing': 'blue',
        'Production': 'cyan',
        'In Design': 'purple',
        'Materials on Order': 'yellow',
        'Shipped': 'green',
        'Fulfilled': 'green',
        'Completed': 'green',
        'Cancelled': 'red',
        'On Hold': 'gray'
    };
    const color = colors[status] || 'gray';
    return `<span class="indicator-pill ${color}">${status || '-'}</span>`;
}

function get_payment_badge(status) {
    const colors = {
        'Paid': 'green',
        'Partially Paid': 'orange',
        'Unpaid': 'red',
        'Refunded': 'gray'
    };
    const color = colors[status] || 'gray';
    return status ? `<span class="indicator-pill ${color}">${status}</span>` : '-';
}

function get_proof_status_badge(status) {
    const colors = {
        'Draft': 'gray',
        'In Review': 'orange',
        'Approved': 'green',
        'Rejected': 'red',
        'Changes Requested': 'yellow',
        'Archived': 'darkgray'
    };
    const color = colors[status] || 'gray';
    return `<span class="indicator-pill ${color}">${status || '-'}</span>`;
}

function get_comm_status_badge(status) {
    const colors = {
        'Open': 'blue',
        'In Progress': 'orange',
        'Resolved': 'green',
        'Closed': 'gray'
    };
    const color = colors[status] || 'gray';
    return `<span class="indicator-pill ${color}">${status || '-'}</span>`;
}

function get_sentiment_badge(sentiment) {
    const icons = {
        'Positive': '<i class="fa fa-smile-o text-success"></i>',
        'Neutral': '<i class="fa fa-meh-o text-muted"></i>',
        'Negative': '<i class="fa fa-frown-o text-danger"></i>'
    };
    return icons[sentiment] || '';
}

function get_channel_color(channel) {
    const colors = {
        'Voice': '#6c5ce7',
        'Chat': '#00cec9',
        'WhatsApp': '#25D366',
        'SMS': '#fdcb6e',
        'Facebook': '#3b5998',
        'Instagram': '#e1306c',
        'Twitter': '#1da1f2',
        'LinkedIn': '#0077b5',
        'Email': '#0984e3'
    };
    return colors[channel] || '#636e72';
}

function get_channel_icon(channel) {
    const icons = {
        'Voice': '<i class="fa fa-phone" style="color: #6c5ce7;"></i>',
        'Phone': '<i class="fa fa-phone" style="color: #6c5ce7;"></i>',
        'Chat': '<i class="fa fa-comments" style="color: #00cec9;"></i>',
        'WhatsApp': '<i class="fa fa-whatsapp" style="color: #25D366;"></i>',
        'SMS': '<i class="fa fa-mobile" style="color: #fdcb6e;"></i>',
        'Facebook': '<i class="fa fa-facebook" style="color: #3b5998;"></i>',
        'Instagram': '<i class="fa fa-instagram" style="color: #e1306c;"></i>',
        'Twitter': '<i class="fa fa-twitter" style="color: #1da1f2;"></i>',
        'LinkedIn': '<i class="fa fa-linkedin" style="color: #0077b5;"></i>',
        'Email': '<i class="fa fa-envelope" style="color: #0984e3;"></i>',
        'Meeting': '<i class="fa fa-calendar" style="color: #00b894;"></i>',
        'Event': '<i class="fa fa-calendar-check-o" style="color: #00b894;"></i>',
        'Visit': '<i class="fa fa-building" style="color: #636e72;"></i>',
        'Other': '<i class="fa fa-comment-o" style="color: #636e72;"></i>'
    };
    return icons[channel] || '<i class="fa fa-comment"></i>';
}

function get_direction_badge(direction) {
    if (direction === 'Sent') {
        return '<span class="indicator-pill blue" style="font-size: 10px;">Sent</span>';
    } else if (direction === 'Received') {
        return '<span class="indicator-pill green" style="font-size: 10px;">Received</span>';
    }
    return '';
}

function get_delivery_badge(status) {
    const colors = {
        'Sent': 'blue',
        'Delivered': 'green',
        'Read': 'green',
        'Error': 'red',
        'Bounced': 'red',
        'Opened': 'cyan',
        'Clicked': 'cyan',
        'Pending': 'orange',
        'Spam': 'red',
        'Rejected': 'red'
    };
    const color = colors[status] || 'gray';
    return status ? `<span class="indicator-pill ${color}" style="font-size: 10px;">${status}</span>` : '';
}

// ========== GLOBAL FUNCTIONS FOR BUTTON HANDLERS ==========

window.refresh_orders_section = function(customer_name) {
    const frm = cur_frm;
    if (frm && frm.doc.name === customer_name) {
        frm.customer_360.orders_loaded = false;
        render_orders_placeholder(frm);
        load_orders_data(frm);
    }
};

window.refresh_proofs_section = function(customer_name) {
    const frm = cur_frm;
    if (frm && frm.doc.name === customer_name) {
        frm.customer_360.proofs_loaded = false;
        render_proofs_placeholder(frm);
        load_proofs_data(frm);
    }
};

window.refresh_timeline_section = function(customer_name) {
    const frm = cur_frm;
    if (frm && frm.doc.name === customer_name) {
        frm.customer_360.timeline_loaded = false;
        render_timeline_placeholder(frm);
        load_timeline_data(frm);
    }
};

window.load_more_orders = function(customer_name) {
    const frm = cur_frm;
    if (frm && frm.doc.name === customer_name) {
        frm.customer_360.orders_offset += frm.customer_360.page_size;
        load_orders_data(frm, true);
    }
};

window.load_more_proofs = function(customer_name) {
    const frm = cur_frm;
    if (frm && frm.doc.name === customer_name) {
        frm.customer_360.proofs_offset += frm.customer_360.page_size;
        load_proofs_data(frm, true);
    }
};

window.load_more_timeline = function(customer_name) {
    const frm = cur_frm;
    if (frm && frm.doc.name === customer_name) {
        frm.customer_360.timeline_offset += frm.customer_360.page_size;
        load_timeline_data(frm, true);
    }
};
