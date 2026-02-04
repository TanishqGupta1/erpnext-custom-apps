import frappe

def run():
    """Compare duplicate proofs side by side."""

    # Get the Order proof
    order_proof = frappe.get_doc("OPS ZiFlow Proof", "Order 2378: Line ID 7721")
    # Get the UUID proof
    uuid_proof = frappe.get_doc("OPS ZiFlow Proof", "4d9eb4c9-6a5d-4a44-b075-8bc3beabe5a6")

    print("=" * 60)
    print("COMPARISON: Same ZiFlow proof stored twice with different IDs")
    print("=" * 60)
    print()
    print(f"{'Field':<25} {'ORDER PROOF':<40} {'UUID PROOF':<40}")
    print("-" * 105)
    print(f"{'name (doc ID)':<25} {order_proof.name:<40} {uuid_proof.name:<40}")
    print(f"{'ziflow_proof_id':<25} {str(order_proof.ziflow_proof_id)[:38]:<40} {str(uuid_proof.ziflow_proof_id)[:38]:<40}")
    print(f"{'proof_name':<25} {str(order_proof.proof_name)[:38]:<40} {str(uuid_proof.proof_name)[:38]:<40}")
    print(f"{'proof_status':<25} {str(order_proof.proof_status):<40} {str(uuid_proof.proof_status):<40}")
    print(f"{'ops_order':<25} {str(order_proof.ops_order):<40} {str(uuid_proof.ops_order):<40}")
    print(f"{'ops_line_id':<25} {str(order_proof.ops_line_id):<40} {str(uuid_proof.ops_line_id):<40}")
    print(f"{'created_at':<25} {str(order_proof.created_at):<40} {str(uuid_proof.created_at):<40}")
    print(f"{'creation (frappe)':<25} {str(order_proof.creation):<40} {str(uuid_proof.creation):<40}")
    print(f"{'has preview_url':<25} {str(bool(order_proof.preview_url)):<40} {str(bool(uuid_proof.preview_url)):<40}")
    print(f"{'has raw_payload':<25} {str(bool(order_proof.raw_payload)):<40} {str(bool(uuid_proof.raw_payload)):<40}")
    print()
    print("CONCLUSION:")
    print("- Both records represent the SAME ZiFlow proof")
    print("- 'Order 2378: Line ID 7721' was created using proof_name as ID (old logic)")
    print("- '4d9eb4c9-6a5d-4a44-b075-8bc3beabe5a6' was created using ZiFlow UUID as ID (correct)")
    print("- The UUID version has the raw_payload with full data from ZiFlow API")
