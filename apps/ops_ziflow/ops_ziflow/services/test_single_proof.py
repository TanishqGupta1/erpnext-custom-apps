"""Test syncing a single proof."""

import frappe
import json
import traceback

def test_sync_single():
    """Test syncing one proof to find the error."""
    from ops_ziflow.services.ziflow_client import ZiFlowClient
    from ops_ziflow.utils.config import load_settings, require_api_key
    from ops_ziflow.services.ziflow_full_sync import sync_single_proof, map_ziflow_fields

    settings = load_settings()
    require_api_key(settings)
    client = ZiFlowClient(settings)

    # Get first proof
    result = client.list_proofs(page=1, page_size=1)
    proofs = result.get("proofs", [])

    if not proofs:
        return {"error": "No proofs found"}

    proof_data = proofs[0]
    print(f"Proof ID: {proof_data.get('id')}")
    print(f"Proof Name: {proof_data.get('name')}")

    try:
        result = sync_single_proof(proof_data)
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}
