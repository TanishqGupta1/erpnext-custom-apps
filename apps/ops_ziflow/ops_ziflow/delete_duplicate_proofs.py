import frappe

def run():
    """Delete duplicate proofs with 'Order...' names that have UUID counterparts."""

    # Get proofs with "Order" in name
    order_proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters=[["name", "like", "Order%"]],
        fields=["name", "proof_name"],
        limit=0
    )

    print(f"Found {len(order_proofs)} proofs with 'Order' in name")

    deleted = 0
    skipped = 0

    for p in order_proofs:
        # Check if there's a matching UUID proof
        uuid_proofs = frappe.get_all(
            "OPS ZiFlow Proof",
            filters={"proof_name": p.proof_name, "name": ["!=", p.name]},
            fields=["name"]
        )

        if uuid_proofs:
            # Has a UUID counterpart - safe to delete
            try:
                frappe.delete_doc("OPS ZiFlow Proof", p.name, force=True)
                deleted += 1
                if deleted % 10 == 0:
                    print(f"Deleted {deleted} duplicates...")
                    frappe.db.commit()
            except Exception as e:
                print(f"Error deleting {p.name}: {e}")
                skipped += 1
        else:
            # No UUID counterpart - keep it
            skipped += 1
            print(f"SKIPPED (no UUID match): {p.name}")

    frappe.db.commit()
    print(f"\nDone! Deleted: {deleted}, Skipped: {skipped}")
