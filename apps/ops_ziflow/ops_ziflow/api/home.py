"""Home page override for OPS Ziflow app."""

import frappe


def get_home_page():
    """Return the default home page for logged in users.

    Returns:
        str: The route to redirect to
    """
    if frappe.session.user and frappe.session.user != "Guest":
        return "ops-cluster-dashboard"
    return "login"
