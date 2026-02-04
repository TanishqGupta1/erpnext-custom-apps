# -*- coding: utf-8 -*-
# Copyright (c) 2025, Visual Graphx and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json


# Required fields configuration for each lead type
REQUIRED_FIELDS = {
    'Schedule Call': {
        'required': ['lead_name', 'phone', 'preferred_call_time'],
        'optional': ['email', 'company', 'callback_datetime', 'callback_notes'],
        'prompts': {
            'lead_name': "May I have your name please?",
            'phone': "What's the best phone number to reach you?",
            'preferred_call_time': "When would be a good time for us to call you? (Morning, Afternoon, or Evening)"
        }
    },
    'Quote Request': {
        'required': ['lead_name', 'email', 'inquiry_type', 'quantity_needed'],
        'optional': ['phone', 'company', 'timeline'],
        'prompts': {
            'lead_name': "May I have your name please?",
            'email': "What email address should we send the quote to?",
            'inquiry_type': "What type of product are you interested in? (e.g., Business Cards, Banners, Flyers)",
            'quantity_needed': "How many do you need?",
            'timeline': "When do you need these by?"
        }
    },
    'General Inquiry': {
        'required': ['lead_name'],
        'optional': ['email', 'phone', 'company', 'inquiry_summary'],
        'prompts': {
            'lead_name': "May I have your name please?"
        }
    }
}


class ChatwootLead(Document):
    """
    Controller for Chatwoot Lead DocType

    Handles:
    - Multi-turn info collection status
    - ERPNext Lead sync (bidirectional)
    - Status change notifications
    """

    def validate(self):
        """Validate before save"""
        self.validate_info_collection()
        self.update_missing_fields()

    def before_save(self):
        """Before save hook"""
        # Auto-update info collection status
        if self.info_collection_status == 'Pending' and self.has_minimum_info():
            self.info_collection_status = 'Complete'

    def after_insert(self):
        """After insert - create ERPNext Lead if complete"""
        if self.info_collection_status == 'Complete' and not self.erp_lead:
            self.create_erp_lead()

    def on_update(self):
        """On update - sync with ERPNext Lead"""
        if self.erp_lead:
            self.sync_to_erp_lead()

    def validate_info_collection(self):
        """Check if required info is collected"""
        lead_type = self.lead_type or 'General Inquiry'
        config = REQUIRED_FIELDS.get(lead_type, REQUIRED_FIELDS['General Inquiry'])

        missing = []
        for field in config['required']:
            if not self.get(field):
                missing.append(field)

        if missing:
            self.missing_fields = json.dumps(missing)
            if self.info_collection_status == 'Complete':
                self.info_collection_status = 'In Progress'
        else:
            self.missing_fields = None
            self.info_collection_status = 'Complete'

    def update_missing_fields(self):
        """Update the missing fields list"""
        lead_type = self.lead_type or 'General Inquiry'
        config = REQUIRED_FIELDS.get(lead_type, REQUIRED_FIELDS['General Inquiry'])

        missing = []
        for field in config['required']:
            if not self.get(field):
                missing.append(field)

        self.missing_fields = json.dumps(missing) if missing else None

    def has_minimum_info(self):
        """Check if minimum required info is present"""
        lead_type = self.lead_type or 'General Inquiry'
        config = REQUIRED_FIELDS.get(lead_type, REQUIRED_FIELDS['General Inquiry'])

        for field in config['required']:
            if not self.get(field):
                return False
        return True

    def get_next_prompt(self):
        """Get the next prompt to ask the customer"""
        if not self.missing_fields:
            return None

        missing = json.loads(self.missing_fields)
        if not missing:
            return None

        lead_type = self.lead_type or 'General Inquiry'
        config = REQUIRED_FIELDS.get(lead_type, REQUIRED_FIELDS['General Inquiry'])
        prompts = config.get('prompts', {})

        # Return prompt for first missing field
        next_field = missing[0]
        return prompts.get(next_field, f"Could you please provide your {next_field.replace('_', ' ')}?")

    def create_erp_lead(self):
        """Create ERPNext CRM Lead from this Chatwoot Lead"""
        try:
            # Check if Lead doctype exists
            if not frappe.db.exists('DocType', 'Lead'):
                frappe.log_error("Lead DocType not found - ERPNext CRM not installed?", "Chatwoot Lead Sync")
                return

            # Map Chatwoot Lead to ERPNext Lead
            lead_data = {
                'doctype': 'Lead',
                'lead_name': self.lead_name,
                'email_id': self.email,
                'phone': self.phone,
                'mobile_no': self.phone,
                'company_name': self.company,
                'website': self.website,
                'source': 'Chat',  # Standard ERPNext Lead Source
                'notes': self.build_lead_notes(),
                'status': self.map_status_to_erp()
            }

            # Create the ERPNext Lead
            erp_lead = frappe.get_doc(lead_data)
            erp_lead.insert(ignore_permissions=True)

            # Link back to Chatwoot Lead
            self.db_set('erp_lead', erp_lead.name, update_modified=False)

            frappe.msgprint(_(f"Created ERPNext Lead: {erp_lead.name}"), alert=True)

        except Exception as e:
            frappe.log_error(f"Failed to create ERPNext Lead: {str(e)}", "Chatwoot Lead Sync Error")

    def sync_to_erp_lead(self):
        """Sync changes to ERPNext Lead"""
        if not self.erp_lead:
            return

        try:
            erp_lead = frappe.get_doc('Lead', self.erp_lead)

            # Update fields if changed
            changed = False

            if erp_lead.lead_name != self.lead_name:
                erp_lead.lead_name = self.lead_name
                changed = True

            if erp_lead.email_id != self.email:
                erp_lead.email_id = self.email
                changed = True

            if erp_lead.phone != self.phone:
                erp_lead.phone = self.phone
                erp_lead.mobile_no = self.phone
                changed = True

            # Map status
            new_status = self.map_status_to_erp()
            if erp_lead.status != new_status:
                erp_lead.status = new_status
                changed = True

            if changed:
                erp_lead.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to sync to ERPNext Lead: {str(e)}", "Chatwoot Lead Sync Error")

    def map_status_to_erp(self):
        """Map Chatwoot Lead status to ERPNext Lead status"""
        status_map = {
            'New': 'Lead',
            'Contacted': 'Open',
            'Qualified': 'Interested',
            'Proposal Sent': 'Quotation',
            'Negotiation': 'Quotation',
            'Won': 'Converted',
            'Lost': 'Do Not Contact',
            'Unqualified': 'Do Not Contact'
        }
        return status_map.get(self.status, 'Lead')

    def build_lead_notes(self):
        """Build notes from Chatwoot Lead data"""
        notes = []

        notes.append(f"**Source:** Chatwoot Chat ({self.chatwoot_conversation_id})")
        notes.append(f"**Lead Type:** {self.lead_type}")

        if self.inquiry_type:
            notes.append(f"**Product Interest:** {self.inquiry_type}")

        if self.quantity_needed:
            notes.append(f"**Quantity:** {self.quantity_needed}")

        if self.timeline:
            notes.append(f"**Timeline:** {self.timeline}")

        if self.inquiry_summary:
            notes.append(f"\n**Inquiry Summary:**\n{self.inquiry_summary}")

        if self.callback_scheduled and self.callback_datetime:
            notes.append(f"\n**Callback Scheduled:** {self.callback_datetime}")
            if self.preferred_call_time:
                notes.append(f"**Preferred Time:** {self.preferred_call_time}")

        if self.quote_requested:
            notes.append(f"\n**Quote Requested:** Yes")

        return '\n'.join(notes)


@frappe.whitelist()
def sync_from_erp_lead(doc, method=None):
    """
    Sync changes from ERPNext Lead back to Chatwoot Lead
    Called via hook when ERPNext Lead is updated

    Args:
        doc: Lead document (passed by Frappe hook)
        method: Hook method name (on_update, after_insert, etc.)
    """
    try:
        # Handle both hook call (doc object) and direct API call (lead name string)
        if isinstance(doc, str):
            erp_lead_name = doc
        else:
            erp_lead_name = doc.name

        # Find linked Chatwoot Lead
        chatwoot_lead_name = frappe.db.get_value(
            'Chatwoot Lead',
            {'erp_lead': erp_lead_name},
            'name'
        )

        if not chatwoot_lead_name:
            return

        erp_lead = frappe.get_doc('Lead', erp_lead_name)
        chatwoot_lead = frappe.get_doc('Chatwoot Lead', chatwoot_lead_name)

        # Map ERPNext status back to Chatwoot status
        erp_status_map = {
            'Lead': 'New',
            'Open': 'Contacted',
            'Replied': 'Contacted',
            'Interested': 'Qualified',
            'Quotation': 'Proposal Sent',
            'Converted': 'Won',
            'Do Not Contact': 'Lost'
        }

        new_status = erp_status_map.get(erp_lead.status)
        if new_status and chatwoot_lead.status != new_status:
            chatwoot_lead.status = new_status
            chatwoot_lead.save(ignore_permissions=True)

    except Exception as e:
        frappe.log_error(f"Failed to sync from ERPNext Lead: {str(e)}", "Chatwoot Lead Sync Error")


@frappe.whitelist()
def get_info_collection_config(lead_type):
    """
    Get the required fields configuration for a lead type
    Called from n8n to know what info to collect
    """
    config = REQUIRED_FIELDS.get(lead_type, REQUIRED_FIELDS['General Inquiry'])
    return config


@frappe.whitelist()
def update_collected_info(lead_name, field_name, field_value):
    """
    Update a single field on a Chatwoot Lead
    Called from n8n as info is collected
    """
    try:
        lead = frappe.get_doc('Chatwoot Lead', lead_name)
        lead.set(field_name, field_value)
        lead.collection_attempts = (lead.collection_attempts or 0) + 1
        lead.save(ignore_permissions=True)

        return {
            'success': True,
            'info_collection_status': lead.info_collection_status,
            'missing_fields': lead.missing_fields,
            'next_prompt': lead.get_next_prompt()
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
