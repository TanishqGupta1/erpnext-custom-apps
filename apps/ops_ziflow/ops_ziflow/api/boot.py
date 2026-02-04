"""
Boot session hook for OPS ZiFlow
Sets the default home page to OPS Cluster Dashboard
"""

import frappe


def set_ops_bootinfo(bootinfo):
    """
    Set the default home page to OPS Cluster Dashboard for desk users.
    This hook is called during boot to modify the bootinfo dict.
    """
    if frappe.session.user == "Guest":
        return

    # Set the home page to our dashboard
    bootinfo["home_page"] = "ops-cluster-dashboard"

    # Also set default workspace redirect info
    bootinfo["ops_default_route"] = "ops-cluster-dashboard"


def get_website_user_home_page(user):
    """
    Return the home page for logged-in website users.
    This redirects logged-in users from / to the dashboard.
    """
    if user and user != "Guest":
        return "app/ops-cluster-dashboard"
    return None
