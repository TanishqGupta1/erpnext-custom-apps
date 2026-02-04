import frappe

def run():
    if frappe.db.exists("Client Script", "OPS ZiFlow Proof List View"):
        frappe.delete_doc("Client Script", "OPS ZiFlow Proof List View", force=True)
        frappe.db.commit()
        print("Client Script deleted - using file-based list.js instead")
    else:
        print("Client Script not found")
