"""Full ZiFlow proof synchronization service."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import frappe
from frappe.utils import now_datetime

from ops_ziflow.services.ziflow_client import ZiFlowClient
from ops_ziflow.utils.config import load_settings, require_api_key
from ops_ziflow.utils.status_mapper import map_ziflow_status


def _parse_iso_datetime(iso_string: str) -> Optional[str]:
    """Parse ISO datetime string to MySQL format.

    Args:
        iso_string: ISO format like "2025-12-29T10:00:00.000Z"

    Returns:
        MySQL datetime string like "2025-12-29 10:00:00"
    """
    if not iso_string:
        return None
    try:
        # Handle various ISO formats
        iso_string = iso_string.replace("Z", "+00:00")
        if "T" in iso_string:
            # Parse ISO format
            dt = datetime.fromisoformat(iso_string.replace("+00:00", ""))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return iso_string
    except Exception:
        return None


def sync_all_proofs(from_date: str = None, to_date: str = None, page_size: int = 50) -> Dict:
    """Sync all proofs from ZiFlow API.

    Args:
        from_date: Start date filter (YYYY-MM-DD), defaults to Dec 1, 2024
        to_date: End date filter (YYYY-MM-DD), defaults to today
        page_size: Number of proofs per API call

    Returns:
        Dict with sync statistics
    """
    stats = {
        "total_fetched": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "skipped": 0,
        "start_time": now_datetime(),
    }

    # Default date range
    if not from_date:
        from_date = "2024-12-01"
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")

    try:
        settings = load_settings()
        require_api_key(settings)
        client = ZiFlowClient(settings)

        page = 1
        all_proofs = []
        has_more = True

        # Fetch all proofs with pagination
        while has_more:
            frappe.logger().info(f"[ZiFlow Sync] Fetching page {page}...")
            result = client.list_proofs(page=page, page_size=page_size)

            # Handle response structure: {"proofs": [...], "count": ..., "has_more": ..., "page": ...}
            proofs = result.get("proofs", [])
            has_more = result.get("has_more", False)

            if not proofs:
                break

            # Filter by date if created_at is available
            for proof in proofs:
                created_at = proof.get("created_at", "")
                if created_at:
                    try:
                        if "T" in created_at:
                            proof_date = created_at.split("T")[0]
                        else:
                            proof_date = created_at.split(" ")[0]

                        if from_date <= proof_date <= to_date:
                            all_proofs.append(proof)
                        else:
                            stats["skipped"] += 1
                    except Exception:
                        all_proofs.append(proof)
                else:
                    all_proofs.append(proof)

            stats["total_fetched"] += len(proofs)

            page += 1

            # Safety limit
            if page > 200:
                frappe.logger().warning("[ZiFlow Sync] Hit page limit of 200")
                break

        frappe.logger().info(f"[ZiFlow Sync] Total proofs to sync: {len(all_proofs)} (skipped {stats['skipped']} outside date range)")

        # Sync each proof
        for i, proof_data in enumerate(all_proofs):
            try:
                result = sync_single_proof(proof_data)
                if result.get("created"):
                    stats["created"] += 1
                else:
                    stats["updated"] += 1

                # Commit every 50 records
                if (stats["created"] + stats["updated"]) % 50 == 0:
                    frappe.db.commit()
                    frappe.logger().info(f"[ZiFlow Sync] Progress: {stats['created'] + stats['updated']}/{len(all_proofs)}")

            except Exception as e:
                stats["errors"] += 1
                if stats["errors"] <= 10:  # Only log first 10 errors
                    frappe.log_error(
                        f"Proof {proof_data.get('id')}: {str(e)[:200]}",
                        "ZiFlow Sync"
                    )

        frappe.db.commit()
        stats["end_time"] = now_datetime()
        frappe.logger().info(f"[ZiFlow Sync] Completed: {stats}")

    except Exception as e:
        stats["error_message"] = str(e)
        frappe.log_error(f"ZiFlow full sync failed: {e}", "ZiFlow Sync Error")

    return stats


def sync_single_proof(proof_data: Dict) -> Dict:
    """Sync a single proof from ZiFlow.

    Args:
        proof_data: Proof data from ZiFlow API (list_proofs already returns full data)

    Returns:
        Dict with sync result
    """
    proof_id = proof_data.get("id")
    if not proof_id:
        raise ValueError("Proof data missing 'id'")

    # Check if proof exists by ziflow_proof_id
    existing = frappe.db.get_value("OPS ZiFlow Proof", {"ziflow_proof_id": proof_id}, "name")

    if existing:
        doc = frappe.get_doc("OPS ZiFlow Proof", existing)
        created = False
    else:
        doc = frappe.new_doc("OPS ZiFlow Proof")
        doc.ziflow_proof_id = proof_id
        created = True

    # Map fields from ZiFlow API response
    map_ziflow_fields(doc, proof_data)

    # Try to link to OPS Order based on pass_through_value or proof name
    if not doc.ops_order:
        doc.ops_order = find_linked_order(proof_data)

    # Validate ops_order exists
    if doc.ops_order and not frappe.db.exists("OPS Order", doc.ops_order):
        doc.ops_order = None

    # Try to link to OPS Order Product
    if doc.ops_order and not doc.ops_order_product:
        doc.ops_order_product = find_linked_product(doc.ops_order, proof_data)

    # Validate ops_order_product exists
    if doc.ops_order_product and not frappe.db.exists("OPS Order Product", doc.ops_order_product):
        doc.ops_order_product = None

    # Set OPS Customer from linked order
    if doc.ops_order and not doc.ops_customer:
        ops_customer = frappe.db.get_value("OPS Order", doc.ops_order, "customer_company")
        if ops_customer:
            doc.ops_customer = ops_customer

    # Validate ops_customer exists
    if doc.ops_customer and not frappe.db.exists("OPS Customer", doc.ops_customer):
        doc.ops_customer = None

    # Save
    if created:
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    return {"created": created, "name": doc.name}


def _extract_line_id(proof_data: Dict) -> Optional[str]:
    """Extract line ID from proof data.

    Checks pass_through_value first, then proof name pattern.
    """
    # First try pass_through_value (format: "order_id|line_id")
    pass_through = proof_data.get("pass_through_value", "") or ""
    if pass_through and "|" in pass_through:
        parts = pass_through.split("|")
        if len(parts) >= 2 and parts[1].strip():
            return parts[1].strip()

    # Fallback: parse proof name pattern "Order XXXX: Line ID YYYY"
    proof_name = proof_data.get("name", "") or ""
    match = re.search(r'Line ID\s+(\d+)', proof_name, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def _extract_approval_date(proof_data: Dict) -> Optional[str]:
    """Extract approval date from stages/members decision_date.

    Returns the earliest approval decision_date found.
    """
    stages = proof_data.get("stages", [])
    approval_dates = []

    for stage in stages:
        members = stage.get("members", [])
        for member in members:
            decision_status = member.get("decision_status", "")
            decision_date = member.get("decision_date", "")
            if decision_status == "approved" and decision_date:
                parsed = _parse_iso_datetime(decision_date)
                if parsed:
                    approval_dates.append(parsed)

    # Return the earliest approval date
    if approval_dates:
        approval_dates.sort()
        return approval_dates[0]

    return None


def map_ziflow_fields(doc, proof_data: Dict):
    """Map ZiFlow API fields to OPS ZiFlow Proof fields.

    Args:
        doc: OPS ZiFlow Proof document
        proof_data: Proof data from ZiFlow API
    """
    # Basic fields
    doc.ziflow_proof_id = proof_data.get("id") or doc.ziflow_proof_id
    doc.proof_name = proof_data.get("name") or doc.proof_name

    # Status mapping
    status = proof_data.get("status", "")
    doc.proof_status = map_ziflow_status(status) or doc.proof_status

    # URLs
    doc.ziflow_url = proof_data.get("public_link") or proof_data.get("url") or doc.ziflow_url

    # Thumbnail URL (field is now TEXT type, no length limit)
    thumbnail = proof_data.get("thumbnail_link") or proof_data.get("image_link") or ""
    if thumbnail:
        doc.file_url = thumbnail

    # Folder info
    folder = proof_data.get("folder") or {}
    doc.ziflow_folder_id = folder.get("id") or doc.ziflow_folder_id
    doc.folder_name = folder.get("name") or doc.folder_name

    # Extract line ID (ops_line_id)
    line_id = _extract_line_id(proof_data)
    if line_id:
        doc.ops_line_id = line_id

    # Dates - convert ISO format to MySQL format
    created_at = proof_data.get("created_at")
    if created_at:
        doc.created_at = _parse_iso_datetime(created_at) or doc.created_at

    # Get deadline from stages
    stages = proof_data.get("stages", [])
    if stages:
        first_stage = stages[0]
        deadline = first_stage.get("deadline")
        if deadline:
            doc.deadline = _parse_iso_datetime(deadline) or doc.deadline

        # Decision status
        stage_status = first_stage.get("status", {})
        decision_status = stage_status.get("decision_status") or proof_data.get("decision_status")
        if decision_status == "approved":
            doc.proof_status = "Approved"
            # Set approved_at from member decision dates
            approved_at = _extract_approval_date(proof_data)
            if approved_at:
                doc.approved_at = approved_at
        elif decision_status == "rejected":
            doc.proof_status = "Rejected"

    # Version info
    doc.current_version = proof_data.get("version") or doc.current_version
    versions = proof_data.get("versions", [])
    doc.total_versions = len(versions) if versions else doc.total_versions

    # Reviewers from stages
    reviewers = []
    for stage in stages:
        members = stage.get("members", [])
        for member in members:
            contact = member.get("contact", {})
            reviewers.append({
                "email": contact.get("email"),
                "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                "decision_status": member.get("decision_status"),
                "decision_date": member.get("decision_date"),
                "company": contact.get("company"),
            })

    if reviewers:
        doc.reviewers_json = json.dumps(reviewers, indent=2)

    # Store raw payload (truncate if too large)
    raw_json = json.dumps(proof_data, indent=2)
    if len(raw_json) > 60000:  # Limit to 60KB
        raw_json = raw_json[:60000] + "\n... (truncated)"
    doc.raw_payload = raw_json

    # Last synced
    doc.last_synced = now_datetime()


def find_linked_order(proof_data: Dict) -> Optional[str]:
    """Try to find linked OPS Order from proof data.

    Uses pass_through_value (format: "order_id|line_id") or extracts from folder/proof name.
    """
    # First try pass_through_value (most reliable)
    pass_through = proof_data.get("pass_through_value", "")
    if pass_through and "|" in pass_through:
        order_id = pass_through.split("|")[0]
        order_name = frappe.db.get_value("OPS Order", {"ops_order_id": order_id}, "name")
        if order_name:
            return order_name

    # Fallback: try folder name (often just the order ID)
    folder = proof_data.get("folder", {})
    folder_name = folder.get("name", "") or ""

    if folder_name and folder_name.isdigit():
        order_name = frappe.db.get_value("OPS Order", {"ops_order_id": folder_name}, "name")
        if order_name:
            return order_name

    # Fallback: parse proof name pattern "Order XXXX: Line ID YYYY"
    proof_name = proof_data.get("name", "") or ""
    match = re.search(r'Order\s+(\d+)', proof_name, re.IGNORECASE)
    if match:
        order_id = match.group(1)
        order_name = frappe.db.get_value("OPS Order", {"ops_order_id": order_id}, "name")
        if order_name:
            return order_name

    return None


def find_linked_product(order_name: str, proof_data: Dict) -> Optional[str]:
    """Try to find linked OPS Order Product.

    Uses pass_through_value (format: "order_id|line_id") or matches by proof URL.
    """
    if not order_name:
        return None

    # First try pass_through_value which contains line_id (orders_products_id)
    pass_through = proof_data.get("pass_through_value", "")
    if pass_through and "|" in pass_through:
        parts = pass_through.split("|")
        if len(parts) >= 2:
            line_id = parts[1]
            product = frappe.db.get_value(
                "OPS Order Product",
                {"parent": order_name, "orders_products_id": line_id},
                "name"
            )
            if product:
                return product

    # Try matching by proof URL
    proof_url = proof_data.get("public_link") or proof_data.get("url") or ""

    if proof_url:
        product = frappe.db.get_value(
            "OPS Order Product",
            {"parent": order_name, "ziflow_proof_url": proof_url},
            "name"
        )
        if product:
            return product

        # Try matching by partial URL (proof ID in URL)
        if "/proof/" in proof_url:
            proof_id = proof_url.split("/proof/")[-1].strip("/")
            if proof_id:
                product = frappe.db.get_value(
                    "OPS Order Product",
                    {"parent": order_name, "ziflow_proof_url": ["like", f"%{proof_id}%"]},
                    "name"
                )
                if product:
                    return product

    # Try matching by Line ID in proof name
    proof_name = proof_data.get("name", "") or ""
    match = re.search(r'Line ID\s+(\d+)', proof_name, re.IGNORECASE)
    if match:
        line_id = match.group(1)
        product = frappe.db.get_value(
            "OPS Order Product",
            {"parent": order_name, "orders_products_id": line_id},
            "name"
        )
        if product:
            return product

    return None


@frappe.whitelist()
def full_sync_ziflow_proofs(from_date: str = "2024-12-01", to_date: str = None) -> Dict:
    """Whitelist wrapper for full ZiFlow sync.

    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD), defaults to today

    Returns:
        Sync statistics
    """
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")

    return sync_all_proofs(from_date=from_date, to_date=to_date)


@frappe.whitelist()
def resync_proof(proof_name: str) -> Dict:
    """Resync a single proof from ZiFlow API.

    Args:
        proof_name: Name of the OPS ZiFlow Proof document

    Returns:
        Sync result
    """
    doc = frappe.get_doc("OPS ZiFlow Proof", proof_name)

    if not doc.ziflow_proof_id:
        return {"status": "error", "message": "No ziflow_proof_id"}

    settings = load_settings()
    require_api_key(settings)
    client = ZiFlowClient(settings)

    try:
        proof_data = client.get_proof(doc.ziflow_proof_id)
        doc.apply_ziflow_payload(proof_data)
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "proof_status": doc.proof_status,
            "current_version": doc.current_version,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def sync_latest_proofs(lookback_minutes: int = 30) -> Dict:
    """Sync latest proofs from ZiFlow API (scheduled job).

    This function is designed to run every 10 minutes and fetch only recent proofs.
    It fetches proofs created/updated in the last N minutes.

    Args:
        lookback_minutes: How far back to look for proofs (default 30 min for safety margin)

    Returns:
        Dict with sync statistics
    """
    stats = {
        "total_fetched": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "start_time": now_datetime(),
    }

    try:
        settings = load_settings()
        require_api_key(settings)
        client = ZiFlowClient(settings)

        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        cutoff_str = cutoff_time.strftime("%Y-%m-%d")

        page = 1
        page_size = 50
        has_more = True
        found_older = False

        frappe.logger().info(f"[ZiFlow Scheduled Sync] Starting sync for proofs since {cutoff_str}...")

        while has_more and not found_older:
            result = client.list_proofs(page=page, page_size=page_size)
            proofs = result.get("proofs", [])
            has_more = result.get("has_more", False)

            if not proofs:
                break

            stats["total_fetched"] += len(proofs)

            for proof_data in proofs:
                # Check created_at to see if we've gone past our lookback window
                created_at = proof_data.get("created_at", "")
                if created_at:
                    try:
                        if "T" in created_at:
                            proof_datetime = datetime.fromisoformat(created_at.replace("Z", "+00:00").replace("+00:00", ""))
                        else:
                            proof_datetime = datetime.strptime(created_at.split(" ")[0], "%Y-%m-%d")

                        # If proof is older than our lookback window, we can stop
                        # But still process this batch
                        if proof_datetime < cutoff_time:
                            found_older = True
                    except Exception:
                        pass

                # Sync the proof
                try:
                    result = sync_single_proof(proof_data)
                    if result.get("created"):
                        stats["created"] += 1
                    else:
                        stats["updated"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    if stats["errors"] <= 5:
                        frappe.log_error(
                            f"Proof {proof_data.get('id')}: {str(e)[:200]}",
                            "ZiFlow Scheduled Sync"
                        )

            page += 1

            # Safety limit - don't fetch more than 10 pages (500 proofs) in scheduled job
            if page > 10:
                frappe.logger().warning("[ZiFlow Scheduled Sync] Hit page limit of 10")
                break

        frappe.db.commit()
        stats["end_time"] = now_datetime()

        # Only log if there were changes
        if stats["created"] > 0 or stats["updated"] > 0 or stats["errors"] > 0:
            frappe.logger().info(f"[ZiFlow Scheduled Sync] Completed: created={stats['created']}, updated={stats['updated']}, errors={stats['errors']}")

    except Exception as e:
        stats["error_message"] = str(e)
        frappe.log_error(f"ZiFlow scheduled sync failed: {e}", "ZiFlow Scheduled Sync Error")

    return stats


def poll_ziflow_proofs():
    """Scheduled job entry point for ZiFlow proof sync.

    This is called by the Frappe scheduler every 10 minutes.
    It syncs proofs from the last 30 minutes to catch any updates.
    """
    try:
        # Use 30 minute lookback to ensure we don't miss any proofs
        # even if there are timing issues or API delays
        return sync_latest_proofs(lookback_minutes=30)
    except Exception as e:
        frappe.log_error(f"ZiFlow poll failed: {e}", "ZiFlow Poll Error")
        return {"error": str(e)}


@frappe.whitelist()
def resync_existing_proofs() -> Dict:
    """Resync all existing proofs from their stored raw_payload.

    This updates fields like ops_line_id, ops_customer, approved_at without
    making new API calls. It reads the raw_payload stored in each proof document.

    Returns:
        Dict with sync statistics
    """
    stats = {
        "total": 0,
        "updated": 0,
        "errors": 0,
        "start_time": now_datetime(),
    }

    try:
        # Get all proofs that have raw_payload
        proofs = frappe.db.sql(
            """SELECT name, raw_payload FROM `tabOPS ZiFlow Proof`
               WHERE raw_payload IS NOT NULL AND raw_payload != ''""",
            as_dict=1
        )

        stats["total"] = len(proofs)
        frappe.logger().info(f"[ZiFlow Resync] Starting resync of {stats['total']} proofs...")

        for i, proof_row in enumerate(proofs):
            try:
                proof_data = json.loads(proof_row["raw_payload"])
                doc = frappe.get_doc("OPS ZiFlow Proof", proof_row["name"])

                # Re-apply field mapping
                map_ziflow_fields(doc, proof_data)

                # Re-link order if not set
                if not doc.ops_order:
                    doc.ops_order = find_linked_order(proof_data)

                # Validate ops_order exists
                if doc.ops_order and not frappe.db.exists("OPS Order", doc.ops_order):
                    doc.ops_order = None

                # Re-link product if not set
                if doc.ops_order and not doc.ops_order_product:
                    doc.ops_order_product = find_linked_product(doc.ops_order, proof_data)

                # Validate ops_order_product exists
                if doc.ops_order_product and not frappe.db.exists("OPS Order Product", doc.ops_order_product):
                    doc.ops_order_product = None

                # Set OPS Customer from linked order
                if doc.ops_order and not doc.ops_customer:
                    ops_customer = frappe.db.get_value("OPS Order", doc.ops_order, "customer_company")
                    if ops_customer:
                        doc.ops_customer = ops_customer

                # Validate ops_customer exists
                if doc.ops_customer and not frappe.db.exists("OPS Customer", doc.ops_customer):
                    doc.ops_customer = None

                doc.save(ignore_permissions=True)
                stats["updated"] += 1

                # Commit every 100 records
                if stats["updated"] % 100 == 0:
                    frappe.db.commit()
                    frappe.logger().info(f"[ZiFlow Resync] Progress: {stats['updated']}/{stats['total']}")

            except Exception as e:
                stats["errors"] += 1
                if stats["errors"] <= 10:
                    frappe.log_error(
                        f"Proof {proof_row['name']}: {str(e)[:200]}",
                        "ZiFlow Resync"
                    )

        frappe.db.commit()
        stats["end_time"] = now_datetime()
        frappe.logger().info(f"[ZiFlow Resync] Completed: {stats}")

    except Exception as e:
        stats["error_message"] = str(e)
        frappe.log_error(f"ZiFlow resync failed: {e}", "ZiFlow Resync Error")

    return stats
