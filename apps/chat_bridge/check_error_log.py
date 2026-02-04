#!/usr/bin/env python3
"""Check Error Log for DEBUG entries"""
import frappe
import json

def check_errors():
    frappe.init(site='erp.visualgraphx.com')
    frappe.connect()

    print("\n=== Checking Error Log for DEBUG entries ===\n")

    # Get recent error logs related to linking accounts
    errors = frappe.get_all(
        "Error Log",
        filters=[
            ["method", "like", "%DEBUG%"]
        ],
        fields=["name", "creation", "method", "error"],
        order_by="creation desc",
        limit=20
    )

    if not errors:
        print("No DEBUG error logs found. Checking for Link Account errors...")
        errors = frappe.get_all(
            "Error Log",
            filters=[
                ["method", "like", "%Link%"]
            ],
            fields=["name", "creation", "method", "error"],
            order_by="creation desc",
            limit=20
        )

    if not errors:
        print("No Link Account errors found. Checking for recent errors...")
        errors = frappe.get_all(
            "Error Log",
            fields=["name", "creation", "method", "error"],
            order_by="creation desc",
            limit=10
        )

    print(f"Found {len(errors)} error log entries:\n")

    for i, err in enumerate(errors, 1):
        print(f"\n{'='*80}")
        print(f"Entry {i}: {err.name}")
        print(f"Created: {err.creation}")
        print(f"Method: {err.method}")
        print(f"\nError:")
        print(err.error[:500] if err.error else "No error text")
        if err.error and len(err.error) > 500:
            print(f"\n... (truncated, total length: {len(err.error)})")

    frappe.destroy()

if __name__ == "__main__":
    check_errors()
