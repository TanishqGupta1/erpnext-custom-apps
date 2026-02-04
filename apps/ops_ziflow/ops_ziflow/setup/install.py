"""Install-time setup for OPS ZiFlow app."""

import frappe

from ops_ziflow.setup import bootstrap


def after_install():
    """Ensure module, custom fields, and base configuration exist."""
    bootstrap.ensure_module_def()
    bootstrap.ensure_custom_fields()
    bootstrap.ensure_workspace()
    frappe.clear_cache()
