import json
from typing import Any

import frappe
from frappe.model.document import Document

from ops_ziflow.utils.status_mapper import map_ziflow_status


class OPSZiFlowProof(Document):
    """Stores ZiFlow proof metadata and sync state."""

    def apply_ziflow_payload(self, payload: dict[str, Any] | None) -> None:
        """Update fields from a ZiFlow payload while keeping local edits."""
        if not payload:
            return

        self.ziflow_proof_id = payload.get("id") or self.ziflow_proof_id
        self.proof_name = payload.get("name") or self.proof_name
        self.proof_status = map_ziflow_status(payload.get("status")) or self.proof_status
        self.ziflow_url = payload.get("url") or payload.get("share_url") or self.ziflow_url
        self.file_url = payload.get("file_url") or self.file_url
        self.deadline = payload.get("deadline") or self.deadline
        self.created_at = payload.get("created_at") or self.created_at
        self.approved_at = payload.get("approved_at") or self.approved_at
        self.current_version = payload.get("current_version") or self.current_version
        self.total_versions = payload.get("total_versions") or self.total_versions
        self.versions_json = (
            json.dumps(payload.get("versions"), indent=2)
            if payload.get("versions")
            else self.versions_json
        )
        self.reviewers_json = (
            json.dumps(payload.get("reviewers"), indent=2)
            if payload.get("reviewers")
            else self.reviewers_json
        )
        comments = payload.get("comments")
        if comments:
            self.comments_json = json.dumps(comments, indent=2)
            self.total_comments = len(comments)
            unresolved = [c for c in comments if not c.get("resolved")]
            self.unresolved_comments = len(unresolved)

        if payload:
            self.raw_payload = json.dumps(payload, indent=2)
        self.last_synced = frappe.utils.now_datetime()
