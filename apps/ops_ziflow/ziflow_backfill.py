#!/usr/bin/env python3
"""
ZiFlow Backfill Script
Syncs all ZiFlow proofs to the OPS ZiFlow Proof doctype in Frappe
Run with: bench --site erp.visualgraphx.com execute ziflow_backfill.backfill_proofs
"""

import json
import requests
from datetime import datetime

# ZiFlow API Configuration
ZIFLOW_API_KEY = "cn1393t8lbb2hb71iq67rkaecu"
ZIFLOW_BASE_URL = "https://api.ziflow.io/v1"


def fetch_all_proofs():
    """Fetch all proofs from ZiFlow API with pagination"""
    all_proofs = []
    offset = 0
    limit = 100

    headers = {
        "apikey": ZIFLOW_API_KEY,
        "Content-Type": "application/json"
    }

    while True:
        print(f"Fetching proofs with offset {offset}...")
        response = requests.get(
            f"{ZIFLOW_BASE_URL}/proofs",
            headers=headers,
            params={"limit": limit, "offset": offset}
        )

        if response.status_code != 200:
            print(f"Error fetching proofs: {response.status_code} - {response.text}")
            break

        data = response.json()
        proofs = data.get("proofs", [])

        if not proofs:
            break

        all_proofs.extend(proofs)
        print(f"Fetched {len(proofs)} proofs, total: {len(all_proofs)}")

        # Check if we've fetched all
        if len(proofs) < limit:
            break

        offset += limit

    return all_proofs


def transform_proof(proof):
    """Transform ZiFlow proof data to Frappe doctype format"""
    # Map ZiFlow status to Frappe status
    status_map = {
        "draft": "Draft",
        "in_progress": "In Review",
        "completed": "Approved",
        "rejected": "Rejected",
        "archived": "Archived"
    }

    # Get proof status
    proof_status = status_map.get(proof.get("status"), "Draft")
    decision_status = proof.get("decision_status", "")

    if decision_status == "approved":
        proof_status = "Approved"
    elif decision_status == "rejected":
        proof_status = "Rejected"
    elif decision_status == "changes_required":
        proof_status = "Changes Requested"

    # Extract order and line IDs from pass_through_value
    pass_through = (proof.get("pass_through_value") or "").split("|")
    order_id = pass_through[0] if len(pass_through) > 0 else ""
    line_id = pass_through[1] if len(pass_through) > 1 else ""

    # Get deadline from first stage
    deadline = None
    stages = proof.get("stages", [])
    if stages and stages[0].get("deadline"):
        deadline = stages[0]["deadline"]

    # Extract reviewers
    reviewers = []
    for stage in stages:
        members = stage.get("members", [])
        for member in members:
            contact = member.get("contact", {})
            reviewers.append({
                "email": member.get("email"),
                "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or member.get("email"),
                "decision_status": member.get("decision_status"),
                "decision_date": member.get("decision_date")
            })

    # Build the document
    folder = proof.get("folder", {})
    source_files = proof.get("source_files", [])

    doc = {
        "doctype": "OPS ZiFlow Proof",
        "ziflow_proof_id": proof.get("id"),
        "proof_name": proof.get("name"),
        "proof_status": proof_status,
        "ziflow_url": proof.get("public_link"),
        "file_url": source_files[0].get("name") if source_files else "",
        "ziflow_folder_id": folder.get("id", ""),
        "folder_name": folder.get("name", ""),
        "deadline": deadline,
        "created_at": proof.get("created_at"),
        "approved_at": datetime.utcnow().isoformat() if proof_status == "Approved" else None,
        "last_synced": datetime.utcnow().isoformat(),
        "current_version": int(proof.get("version", 1)),
        "total_versions": len(proof.get("versions", [])) or 1,
        "versions_json": json.dumps(proof.get("versions", [])),
        "reviewers_json": json.dumps(reviewers),
        "total_comments": 0,
        "unresolved_comments": 0,
        "comments_json": "[]",
        "sync_status": "Synced",
        "sync_error": "",
        "raw_payload": json.dumps(proof)
    }

    return doc


def backfill_proofs():
    """Main backfill function - run this with bench execute"""
    import frappe

    print("Starting ZiFlow backfill...")

    # Fetch all proofs
    proofs = fetch_all_proofs()
    print(f"Total proofs to sync: {len(proofs)}")

    created = 0
    updated = 0
    errors = 0

    for proof in proofs:
        try:
            doc_data = transform_proof(proof)
            ziflow_id = doc_data["ziflow_proof_id"]

            # Check if proof already exists
            existing = frappe.db.exists("OPS ZiFlow Proof", ziflow_id)

            if existing:
                # Update existing
                doc = frappe.get_doc("OPS ZiFlow Proof", ziflow_id)
                doc.update(doc_data)
                doc.save(ignore_permissions=True)
                updated += 1
                print(f"Updated: {ziflow_id} - {doc_data['proof_name']}")
            else:
                # Create new
                doc = frappe.get_doc(doc_data)
                doc.insert(ignore_permissions=True)
                created += 1
                print(f"Created: {ziflow_id} - {doc_data['proof_name']}")

            frappe.db.commit()

        except Exception as e:
            errors += 1
            print(f"Error processing proof {proof.get('id')}: {str(e)}")
            frappe.db.rollback()

    print(f"\nBackfill complete!")
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"Errors: {errors}")

    return {"created": created, "updated": updated, "errors": errors}


if __name__ == "__main__":
    # For testing outside of frappe context
    proofs = fetch_all_proofs()
    print(f"Would sync {len(proofs)} proofs")
    for p in proofs[:3]:
        print(json.dumps(transform_proof(p), indent=2, default=str))
