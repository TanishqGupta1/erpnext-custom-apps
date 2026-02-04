import frappe

def run():
    """Check for duplicate proofs."""

    # Get proofs with "Order" in name
    order_proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters=[["name", "like", "Order%"]],
        fields=["name", "proof_name"],
        limit=0
    )

    print(f"Found {len(order_proofs)} proofs with 'Order' in name")

    duplicates = 0
    unique = 0

    for p in order_proofs[:20]:  # Check first 20
        # Find matching UUID proof with same proof_name
        uuid_proofs = frappe.get_all(
            "OPS ZiFlow Proof",
            filters={"proof_name": p.proof_name, "name": ["!=", p.name]},
            fields=["name"]
        )
        if uuid_proofs:
            duplicates += 1
            print(f"DUPLICATE: '{p.name}' has matching UUID proof: '{uuid_proofs[0].name}'")
        else:
            unique += 1
            print(f"UNIQUE: '{p.name}'")

    print(f"\nSample results: {duplicates} duplicates, {unique} unique out of first 20")
