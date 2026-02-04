"""Check recent OPS errors"""
import frappe

def check():
    # Check if OPS Error Log exists
    if not frappe.db.exists("DocType", "OPS Error Log"):
        print("OPS Error Log doctype does not exist")
        return

    errors = frappe.db.sql("""
        SELECT name, error_title, error_message, error_type, severity, creation
        FROM `tabOPS Error Log`
        ORDER BY creation DESC
        LIMIT 10
    """, as_dict=True)

    print(f"\n=== Recent OPS Errors ({len(errors)}) ===\n")

    for err in errors:
        print(f"[{err.creation}] {err.severity} - {err.error_type}")
        print(f"  Title: {err.error_title}")
        print(f"  Message: {err.error_message[:200] if err.error_message else 'N/A'}...")
        print()

    # Also check standard Error Log
    print("\n=== Recent Frappe Error Logs ===\n")
    std_errors = frappe.db.sql("""
        SELECT name, method, error, creation
        FROM `tabError Log`
        WHERE method LIKE '%quote%' OR error LIKE '%quote%'
        ORDER BY creation DESC
        LIMIT 5
    """, as_dict=True)

    for err in std_errors:
        print(f"[{err.creation}] {err.method}")
        print(f"  {err.error[:300] if err.error else 'N/A'}...")
        print()
