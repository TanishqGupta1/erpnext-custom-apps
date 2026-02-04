"""Debug ZiFlow API responses."""

import frappe
import json

def debug_list_proofs():
    """List proofs and show structure."""
    from ops_ziflow.services.ziflow_client import ZiFlowClient
    from ops_ziflow.utils.config import load_settings, require_api_key

    settings = load_settings()
    require_api_key(settings)
    client = ZiFlowClient(settings)

    # Get first page of proofs
    result = client.list_proofs(page=1, page_size=5)

    print("=" * 50)
    print("API Response Type:", type(result))
    print("API Response Keys:", result.keys() if isinstance(result, dict) else "N/A")

    if isinstance(result, dict):
        proofs = result.get("data", []) or result.get("proofs", []) or []
    elif isinstance(result, list):
        proofs = result
    else:
        proofs = []

    print(f"Number of proofs: {len(proofs)}")

    if proofs:
        print("\nFirst proof structure:")
        first = proofs[0]
        print(json.dumps(first, indent=2, default=str)[:2000])

        print("\n\nProof IDs and names:")
        for p in proofs[:5]:
            print(f"  ID: {p.get('id')} | Name: {p.get('name')} | Status: {p.get('status')}")

    return {"proofs_count": len(proofs), "sample": proofs[0] if proofs else None}
