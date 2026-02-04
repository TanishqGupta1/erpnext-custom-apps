# -*- coding: utf-8 -*-
# Copyright (c) 2025, Visual Graphx and contributors
# For license information, please see license.txt

"""
Chatwoot Lead Capture API

Webhook endpoints for receiving leads from n8n Chatwoot Auto-reply workflow.
"""

from __future__ import unicode_literals
import frappe
from frappe import _
import json
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def receive_lead():
    """
    Webhook endpoint to receive leads from Chatwoot/n8n

    Endpoint: /api/method/ops_integration.ops_integration.api.receive_lead
    Method: POST

    Expected payload:
    {
        "lead_type": "schedule_call" | "quote_request" | "general_inquiry",
        "chatwoot_conversation_id": "123",
        "chatwoot_contact_id": "456",
        "chatwoot_account_id": "1",
        "inbox_name": "Website Chat",
        "lead_name": "John Doe",
        "email": "john@example.com",
        "phone": "480-123-4567",
        "company": "Acme Inc",
        "inquiry_type": "Business Cards",
        "inquiry_summary": "Customer wants 500 business cards...",
        "conversation_summary": "Full conversation...",
        "ai_notes": "Customer seems interested in...",
        "products_interested": [
            {"product_category": "Business Cards", "quantity": "500", "specifications": "..."}
        ],
        "schedule_call": {
            "preferred_call_time": "Morning (8am-12pm)",
            "preferred_contact_method": "Phone",
            "callback_datetime": "2025-12-18 10:00:00",
            "callback_notes": "..."
        },
        "quote_request": {
            "product_type": "Business Cards",
            "quantity": "500",
            "specifications": "...",
            "delivery_method": "Email"
        }
    }
    """
    try:
        # Validate request method
        if frappe.request.method != 'POST':
            frappe.throw(_("Only POST requests are allowed"))

        # Get payload
        payload = frappe.request.get_json()
        if not payload:
            frappe.throw(_("No payload provided"))

        # Validate required fields
        required_fields = ['lead_type', 'lead_name']
        for field in required_fields:
            if not payload.get(field):
                frappe.throw(_(f"Missing required field: {field}"))

        # Check if lead already exists for this conversation
        existing_lead = None
        if payload.get('chatwoot_conversation_id'):
            existing_lead = frappe.db.get_value(
                'Chatwoot Lead',
                {'chatwoot_conversation_id': payload.get('chatwoot_conversation_id')},
                'name'
            )

        if existing_lead:
            # Update existing lead
            lead = frappe.get_doc('Chatwoot Lead', existing_lead)
            result = update_lead(lead, payload)
        else:
            # Create new lead
            result = create_lead(payload)

        # Send notification email to sales team
        send_lead_notification(result)

        return {
            "success": True,
            "message": "Lead processed successfully",
            "lead_id": result.name,
            "lead_name": result.lead_name,
            "status": result.status,
            "action": "updated" if existing_lead else "created"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Chatwoot Lead Webhook Error")
        return {
            "success": False,
            "message": str(e)
        }


def create_lead(payload):
    """Create a new Chatwoot Lead from payload"""

    lead_type_map = {
        'schedule_call': 'Schedule Call',
        'quote_request': 'Quote Request',
        'general_inquiry': 'General Inquiry',
        'order_status': 'Order Status',
        'complaint': 'Complaint',
        'support': 'Support'
    }

    # Create lead document
    lead = frappe.get_doc({
        'doctype': 'Chatwoot Lead',
        'lead_type': lead_type_map.get(payload.get('lead_type'), 'General Inquiry'),
        'status': 'New',
        'priority': 'High' if payload.get('lead_type') in ['schedule_call', 'quote_request'] else 'Medium',

        # Source info
        'chatwoot_conversation_id': payload.get('chatwoot_conversation_id'),
        'chatwoot_contact_id': payload.get('chatwoot_contact_id'),
        'chatwoot_account_id': payload.get('chatwoot_account_id'),
        'inbox_name': payload.get('inbox_name'),
        'lead_source': payload.get('lead_source', 'Website Chat'),

        # Contact info
        'lead_name': payload.get('lead_name'),
        'email': payload.get('email'),
        'phone': payload.get('phone'),
        'company': payload.get('company'),
        'website': payload.get('website'),

        # Inquiry details
        'inquiry_type': payload.get('inquiry_type'),
        'inquiry_summary': payload.get('inquiry_summary'),
        'quantity_needed': payload.get('quantity_needed'),
        'timeline': payload.get('timeline'),
        'estimated_value': payload.get('estimated_value'),

        # Conversation
        'conversation_summary': payload.get('conversation_summary'),
        'ai_notes': payload.get('ai_notes'),
    })

    # Handle schedule call request
    if payload.get('lead_type') == 'schedule_call' and payload.get('schedule_call'):
        schedule = payload.get('schedule_call')
        lead.preferred_contact_method = schedule.get('preferred_contact_method', 'Phone')
        lead.preferred_call_time = schedule.get('preferred_call_time')
        lead.timezone = schedule.get('timezone', 'America/Phoenix')

        if schedule.get('callback_datetime'):
            lead.callback_scheduled = 1
            lead.callback_datetime = schedule.get('callback_datetime')
            lead.callback_notes = schedule.get('callback_notes')

            # Add to call schedules child table
            lead.append('call_schedules', {
                'scheduled_datetime': schedule.get('callback_datetime'),
                'call_type': schedule.get('call_type', 'Phone Call'),
                'status': 'Scheduled',
                'notes': schedule.get('callback_notes'),
                'created_from_chat': 1
            })

    # Handle quote request
    if payload.get('lead_type') == 'quote_request' and payload.get('quote_request'):
        quote = payload.get('quote_request')
        lead.quote_requested = 1

        # Add to quote requests child table
        lead.append('quote_requests', {
            'request_date': datetime.now(),
            'product_type': quote.get('product_type', payload.get('inquiry_type', 'Other')),
            'quantity': quote.get('quantity', payload.get('quantity_needed')),
            'specifications': quote.get('specifications'),
            'delivery_method': quote.get('delivery_method', 'Email'),
            'status': 'Pending'
        })

    # Add products interested
    if payload.get('products_interested'):
        for product in payload.get('products_interested'):
            lead.append('products_interested', {
                'product_category': product.get('product_category'),
                'product_name': product.get('product_name'),
                'quantity': product.get('quantity'),
                'specifications': product.get('specifications'),
                'estimated_price': product.get('estimated_price'),
                'priority': product.get('priority', 'Medium'),
                'notes': product.get('notes')
            })

    lead.insert(ignore_permissions=True)
    frappe.db.commit()

    return lead


def update_lead(lead, payload):
    """Update an existing Chatwoot Lead with new data"""

    # Update conversation summary if provided
    if payload.get('conversation_summary'):
        lead.conversation_summary = payload.get('conversation_summary')

    if payload.get('ai_notes'):
        lead.ai_notes = payload.get('ai_notes')

    # Handle new schedule call request
    if payload.get('lead_type') == 'schedule_call' and payload.get('schedule_call'):
        schedule = payload.get('schedule_call')

        if schedule.get('callback_datetime'):
            lead.callback_scheduled = 1
            lead.callback_datetime = schedule.get('callback_datetime')
            lead.callback_notes = schedule.get('callback_notes')

            # Add new call schedule to history
            lead.append('call_schedules', {
                'scheduled_datetime': schedule.get('callback_datetime'),
                'call_type': schedule.get('call_type', 'Phone Call'),
                'status': 'Scheduled',
                'notes': schedule.get('callback_notes'),
                'created_from_chat': 1
            })

    # Handle new quote request
    if payload.get('lead_type') == 'quote_request' and payload.get('quote_request'):
        quote = payload.get('quote_request')
        lead.quote_requested = 1

        # Add new quote request to history
        lead.append('quote_requests', {
            'request_date': datetime.now(),
            'product_type': quote.get('product_type', 'Other'),
            'quantity': quote.get('quantity'),
            'specifications': quote.get('specifications'),
            'delivery_method': quote.get('delivery_method', 'Email'),
            'status': 'Pending'
        })

    # Add new products if provided
    if payload.get('products_interested'):
        for product in payload.get('products_interested'):
            lead.append('products_interested', {
                'product_category': product.get('product_category'),
                'product_name': product.get('product_name'),
                'quantity': product.get('quantity'),
                'specifications': product.get('specifications'),
                'estimated_price': product.get('estimated_price'),
                'priority': product.get('priority', 'Medium'),
                'notes': product.get('notes')
            })

    lead.save(ignore_permissions=True)
    frappe.db.commit()

    return lead


def send_lead_notification(lead):
    """Send email notification for new leads"""
    try:
        # Get sales team emails
        sales_emails = frappe.db.get_all(
            'User',
            filters={'role': 'Sales User', 'enabled': 1},
            fields=['email']
        )

        if not sales_emails:
            # Fallback to default
            sales_emails = [{'email': 'sales@visualgraphx.com'}]

        recipients = [u['email'] for u in sales_emails if u.get('email')]

        # Determine priority emoji
        priority_emoji = {
            'Urgent': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢'
        }.get(lead.priority, '🟡')

        # Build email content
        subject = f"{priority_emoji} New {lead.lead_type} Lead: {lead.lead_name}"

        message = f"""
<h2>New Lead from Chatwoot</h2>

<table style="border-collapse: collapse; width: 100%;">
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Lead Name:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{lead.lead_name}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Type:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{lead.lead_type}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Email:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{lead.email or 'Not provided'}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Phone:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{lead.phone or 'Not provided'}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Company:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{lead.company or 'Not provided'}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Inquiry Type:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{lead.inquiry_type or 'Not specified'}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Priority:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{lead.priority}</td></tr>
</table>

<h3>Inquiry Summary</h3>
<p>{lead.inquiry_summary or 'No summary available'}</p>
"""

        if lead.callback_scheduled and lead.callback_datetime:
            message += f"""
<h3>📞 Callback Scheduled</h3>
<p><strong>Date/Time:</strong> {lead.callback_datetime}</p>
<p><strong>Notes:</strong> {lead.callback_notes or 'None'}</p>
"""

        if lead.quote_requested:
            message += f"""
<h3>📝 Quote Requested</h3>
<p>Customer requested a quote via {lead.quote_requests[0].delivery_method if lead.quote_requests else 'Email'}</p>
"""

        message += f"""
<p style="margin-top: 20px;">
<a href="{frappe.utils.get_url()}/app/chatwoot-lead/{lead.name}"
   style="background: #5046e5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
   View Lead in ERP
</a>
</p>
"""

        # Send email
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            now=True
        )

    except Exception as e:
        frappe.log_error(f"Failed to send lead notification: {str(e)}", "Lead Notification Error")


@frappe.whitelist(allow_guest=True)
def update_lead_status():
    """
    Update lead status from external systems

    Endpoint: /api/method/ops_integration.ops_integration.api.update_lead_status
    Method: POST

    Payload:
    {
        "lead_id": "CW-LEAD-0001",
        "status": "Contacted",
        "notes": "Called customer, will follow up"
    }
    """
    try:
        if frappe.request.method != 'POST':
            frappe.throw(_("Only POST requests are allowed"))

        payload = frappe.request.get_json()
        if not payload.get('lead_id'):
            frappe.throw(_("Missing lead_id"))

        lead = frappe.get_doc('Chatwoot Lead', payload.get('lead_id'))

        if payload.get('status'):
            lead.status = payload.get('status')

        if payload.get('notes'):
            if lead.ai_notes:
                lead.ai_notes += f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {payload.get('notes')}"
            else:
                lead.ai_notes = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {payload.get('notes')}"

        lead.last_contacted = datetime.now()
        lead.contact_count = (lead.contact_count or 0) + 1

        lead.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "message": "Lead status updated",
            "lead_id": lead.name,
            "new_status": lead.status
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Lead Status Error")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def get_lead_stats():
    """
    Get lead statistics for dashboard

    Endpoint: /api/method/ops_integration.ops_integration.api.get_lead_stats
    """
    try:
        # Total leads
        total_leads = frappe.db.count('Chatwoot Lead')

        # Leads by status
        status_counts = frappe.db.sql("""
            SELECT status, COUNT(*) as count
            FROM `tabChatwoot Lead`
            GROUP BY status
        """, as_dict=True)

        # Leads by type
        type_counts = frappe.db.sql("""
            SELECT lead_type, COUNT(*) as count
            FROM `tabChatwoot Lead`
            GROUP BY lead_type
        """, as_dict=True)

        # Leads this week
        this_week = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabChatwoot Lead`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, as_dict=True)[0].get('count', 0)

        # Conversion rate
        converted = frappe.db.count('Chatwoot Lead', {'converted': 1})
        conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0

        # Pending callbacks
        pending_callbacks = frappe.db.count('Chatwoot Lead', {
            'callback_scheduled': 1,
            'status': ['not in', ['Won', 'Lost', 'Unqualified']]
        })

        # Pending quotes
        pending_quotes = frappe.db.count('Chatwoot Lead', {
            'quote_requested': 1,
            'quote_sent': 0
        })

        return {
            "success": True,
            "stats": {
                "total_leads": total_leads,
                "leads_this_week": this_week,
                "conversion_rate": round(conversion_rate, 1),
                "pending_callbacks": pending_callbacks,
                "pending_quotes": pending_quotes,
                "by_status": {s['status']: s['count'] for s in status_counts},
                "by_type": {t['lead_type']: t['count'] for t in type_counts}
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Lead Stats Error")
        return {
            "success": False,
            "message": str(e)
        }


def cleanup_old_leads():
    """
    Scheduled task: Clean up old closed leads (> 6 months)
    Runs daily
    """
    try:
        # Find leads closed more than 6 months ago
        old_leads = frappe.db.get_all(
            'Chatwoot Lead',
            filters={
                'status': ['in', ['Won', 'Lost', 'Unqualified']],
                'modified': ['<', frappe.utils.add_months(frappe.utils.now(), -6)]
            },
            fields=['name']
        )

        # Archive or delete based on settings
        for lead in old_leads:
            # For now, just log - could implement archive logic
            frappe.log_error(f"Old lead ready for archival: {lead['name']}", "Lead Cleanup")

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Lead cleanup failed: {str(e)}", "Lead Cleanup Error")


def send_pending_notifications():
    """
    Scheduled task: Send reminders for pending callbacks and quotes
    Runs hourly
    """
    try:
        from datetime import timedelta

        now = frappe.utils.now_datetime()

        # Find callbacks due in the next hour
        upcoming_callbacks = frappe.db.get_all(
            'Chatwoot Lead',
            filters={
                'callback_scheduled': 1,
                'callback_datetime': ['between', [now, now + timedelta(hours=1)]],
                'status': ['not in', ['Won', 'Lost', 'Unqualified']]
            },
            fields=['name', 'lead_name', 'phone', 'callback_datetime', 'callback_notes', 'assigned_to']
        )

        for callback in upcoming_callbacks:
            # Get assignee email
            if callback.get('assigned_to'):
                recipient = frappe.db.get_value('User', callback['assigned_to'], 'email')
            else:
                recipient = 'sales@visualgraphx.com'

            subject = f"Reminder: Callback with {callback['lead_name']} in 1 hour"
            message = f"""
<h2>Upcoming Callback Reminder</h2>
<p><strong>Lead:</strong> {callback['lead_name']}</p>
<p><strong>Phone:</strong> {callback['phone'] or 'Not provided'}</p>
<p><strong>Scheduled Time:</strong> {callback['callback_datetime']}</p>
<p><strong>Notes:</strong> {callback['callback_notes'] or 'None'}</p>

<p>
<a href="{frappe.utils.get_url()}/app/chatwoot-lead/{callback['name']}"
   style="background: #5046e5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
   View Lead
</a>
</p>
"""
            frappe.sendmail(
                recipients=[recipient],
                subject=subject,
                message=message,
                now=True
            )

        # Find quote requests pending for more than 24 hours
        stale_quotes = frappe.db.get_all(
            'Chatwoot Lead',
            filters={
                'quote_requested': 1,
                'quote_sent': 0,
                'creation': ['<', now - timedelta(hours=24)]
            },
            fields=['name', 'lead_name', 'email', 'inquiry_type', 'creation']
        )

        if stale_quotes:
            # Send summary email to sales team
            subject = f"Alert: {len(stale_quotes)} Quote Requests Pending > 24 Hours"
            message = f"""
<h2>Pending Quote Requests</h2>
<p>The following quote requests have been pending for more than 24 hours:</p>
<ul>
"""
            for quote in stale_quotes:
                message += f"""
<li><a href="{frappe.utils.get_url()}/app/chatwoot-lead/{quote['name']}">{quote['lead_name']}</a> - {quote['inquiry_type'] or 'General'} (since {quote['creation']})</li>
"""
            message += "</ul>"

            frappe.sendmail(
                recipients=['sales@visualgraphx.com'],
                subject=subject,
                message=message,
                now=True
            )

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Pending notifications failed: {str(e)}", "Notification Error")
