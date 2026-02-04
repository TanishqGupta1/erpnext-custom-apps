"""Status mapping utilities between ZiFlow and OPS doctypes."""

ZIFLOW_TO_OPS_PROOF = {
    "draft": "Draft",
    "in_review": "In Review",
    "approved": "Approved",
    "completed": "Approved",  # Completed proofs are considered approved
    "rejected": "Rejected",
    "changes_requested": "Changes Requested",
    "archived": "Archived",
    "pending": "In Review",  # Pending proofs are considered in review
}

OPS_PROOF_TO_PRODUCT = {
    "Draft": "Pending",
    "In Review": "In Review",
    "Approved": "Approved",
    "Rejected": "Rejected",
    "Changes Requested": "In Review",
    "Archived": "Pending",
}


def map_ziflow_status(ziflow_status: str | None) -> str | None:
    if not ziflow_status:
        return None
    normalized = ziflow_status.lower().strip()
    # Fallback to "Draft" for unknown statuses to avoid validation errors
    return ZIFLOW_TO_OPS_PROOF.get(normalized, "Draft")


def map_proof_to_product_status(proof_status: str | None) -> str | None:
    if not proof_status:
        return None
    return OPS_PROOF_TO_PRODUCT.get(proof_status, proof_status)


def is_approved_status(proof_status: str | None) -> bool:
    return proof_status == "Approved"
