"""
Qdrant FAQ Sync Service

Handles syncing Chatwoot FAQ documents to Qdrant vector database
for semantic search in Chatwoot conversations.

Collection: chatwoot_knowledge_v2
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
import requests
import uuid
from typing import Dict, List, Any, Optional


# Collection configuration - shared with n8n workflows
COLLECTION_NAME = "chatwoot_knowledge_v2"
VECTOR_SIZE = 512  # text-embedding-3-small with dimensions=512


def get_settings() -> Dict[str, Any]:
    """Get Qdrant and embedding settings from AI Communications Hub Settings."""
    settings_doc = frappe.get_single("AI Communications Hub Settings")

    # Get Qdrant API key
    qdrant_api_key = None
    if settings_doc.qdrant_api_key:
        try:
            qdrant_api_key = settings_doc.get_password("qdrant_api_key")
        except Exception:
            qdrant_api_key = settings_doc.qdrant_api_key

    # Get LLM API key for embeddings
    llm_api_key = None
    if settings_doc.llm_api_key:
        try:
            llm_api_key = settings_doc.get_password("llm_api_key")
        except Exception:
            llm_api_key = settings_doc.llm_api_key

    return {
        "qdrant_url": settings_doc.qdrant_url or "http://qdrant:6333",
        "qdrant_api_key": qdrant_api_key,
        "llm_api_url": settings_doc.llm_api_url or "https://api.naga.ac/v1",
        "llm_api_key": llm_api_key,
    }


def get_qdrant_headers(settings: Dict) -> Dict[str, str]:
    """Build headers for Qdrant API requests."""
    headers = {"Content-Type": "application/json"}
    if settings.get("qdrant_api_key"):
        headers["api-key"] = settings["qdrant_api_key"]
    return headers


def ensure_collection_exists() -> bool:
    """Create the chatwoot_knowledge_v2 collection if it doesn't exist."""
    settings = get_settings()
    url = f"{settings['qdrant_url']}/collections/{COLLECTION_NAME}"

    try:
        response = requests.get(url, headers=get_qdrant_headers(settings), timeout=5)

        if response.status_code == 404:
            # Create collection
            create_response = requests.put(
                url,
                headers=get_qdrant_headers(settings),
                json={
                    "vectors": {
                        "size": VECTOR_SIZE,
                        "distance": "Cosine"
                    },
                    "on_disk_payload": True
                },
                timeout=10
            )
            create_response.raise_for_status()
            frappe.logger().info(f"Created Qdrant collection: {COLLECTION_NAME}")
            return True

        response.raise_for_status()
        return True

    except Exception as e:
        frappe.log_error(f"Qdrant collection check failed: {str(e)}", "Qdrant FAQ Sync")
        raise


def generate_embedding(text: str) -> List[float]:
    """Generate embedding using text-embedding-3-small model with 512 dimensions."""
    settings = get_settings()

    try:
        response = requests.post(
            f"{settings['llm_api_url']}/embeddings",
            headers={
                "Authorization": f"Bearer {settings['llm_api_key']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "text-embedding-3-small",
                "input": text,
                "dimensions": VECTOR_SIZE  # Match collection's vector size (512)
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        frappe.log_error(f"Embedding generation failed: {str(e)}", "Qdrant FAQ Sync")
        raise


def generate_point_id(doc_name: str) -> str:
    """Generate a deterministic UUID from document name."""
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace
    return str(uuid.uuid5(namespace, f"chatwoot_faq:{doc_name}"))


def build_faq_content(faq_doc) -> str:
    """Build the text content to be embedded."""
    clean_answer = frappe.utils.strip_html_tags(faq_doc.answer or "")

    parts = [
        f"Question: {faq_doc.question}",
        f"Answer: {clean_answer}"
    ]

    if faq_doc.category:
        category_name = frappe.db.get_value("Chatwoot FAQ Category", faq_doc.category, "category_name")
        if category_name:
            parts.append(f"Category: {category_name}")

    if faq_doc.tags:
        parts.append(f"Tags: {faq_doc.tags}")

    return "\n\n".join(parts)


def build_faq_payload(faq_doc) -> Dict[str, Any]:
    """Build the Qdrant point payload."""
    clean_answer = frappe.utils.strip_html_tags(faq_doc.answer or "")

    return {
        "doc_name": faq_doc.name,
        "doctype": "Chatwoot FAQ",
        "question": faq_doc.question,
        "answer": clean_answer,
        "answer_html": faq_doc.answer,
        "category": faq_doc.category,
        "priority": faq_doc.priority,
        "tags": faq_doc.tags.split(",") if faq_doc.tags else [],
        "enabled": faq_doc.enabled,
        "created_at": str(faq_doc.creation),
        "modified_at": str(faq_doc.modified),
        "source": "Chatwoot FAQ"
    }


def sync_faq(faq_doc) -> Dict[str, Any]:
    """
    Sync a single FAQ to Qdrant.

    Args:
        faq_doc: Chatwoot FAQ document

    Returns:
        dict: Result with status and point_id
    """
    try:
        ensure_collection_exists()

        content = build_faq_content(faq_doc)
        embedding = generate_embedding(content)

        # Use existing point_id if available (for imported FAQs), otherwise generate new
        if faq_doc.qdrant_point_id:
            point_id = faq_doc.qdrant_point_id
            # Convert to int if it's a numeric string (legacy points use integer IDs)
            if point_id.isdigit():
                point_id = int(point_id)
        else:
            point_id = generate_point_id(faq_doc.name)

        payload = build_faq_payload(faq_doc)

        settings = get_settings()
        url = f"{settings['qdrant_url']}/collections/{COLLECTION_NAME}/points"

        response = requests.put(
            url,
            headers=get_qdrant_headers(settings),
            json={
                "points": [
                    {
                        "id": point_id,
                        "vector": embedding,
                        "payload": payload
                    }
                ]
            },
            timeout=30
        )
        response.raise_for_status()

        return {
            "status": "success",
            "point_id": point_id
        }

    except Exception as e:
        frappe.log_error(f"FAQ sync failed for {faq_doc.name}: {str(e)}", "Qdrant FAQ Sync")
        return {
            "status": "error",
            "error": str(e)
        }


def delete_faq(doc_name: str) -> Dict[str, Any]:
    """
    Delete FAQ point from Qdrant.

    Args:
        doc_name: Document name

    Returns:
        dict: Result with status
    """
    try:
        point_id = generate_point_id(doc_name)
        settings = get_settings()
        url = f"{settings['qdrant_url']}/collections/{COLLECTION_NAME}/points/delete"

        response = requests.post(
            url,
            headers=get_qdrant_headers(settings),
            json={
                "points": [point_id]
            },
            timeout=10
        )
        response.raise_for_status()

        return {"status": "success"}

    except Exception as e:
        frappe.log_error(f"FAQ delete failed for {doc_name}: {str(e)}", "Qdrant FAQ Sync")
        return {
            "status": "error",
            "error": str(e)
        }


# Background job functions

def sync_faq_by_name(doc_name: str):
    """
    Sync FAQ by document name (for background jobs).

    Args:
        doc_name: Chatwoot FAQ document name
    """
    try:
        doc = frappe.get_doc("Chatwoot FAQ", doc_name)
        result = sync_faq(doc)

        # Update sync status
        frappe.db.set_value("Chatwoot FAQ", doc_name, {
            "sync_status": "Synced" if result.get("status") == "success" else "Failed",
            "last_synced": now_datetime() if result.get("status") == "success" else None,
            "qdrant_point_id": result.get("point_id"),
            "sync_error": result.get("error", "")[:500] if result.get("error") else ""
        }, update_modified=False)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"FAQ sync job failed for {doc_name}: {str(e)}", "Qdrant FAQ Sync")

        frappe.db.set_value("Chatwoot FAQ", doc_name, {
            "sync_status": "Failed",
            "sync_error": str(e)[:500]
        }, update_modified=False)

        frappe.db.commit()


def delete_faq_by_name(doc_name: str):
    """Delete FAQ from Qdrant by document name (for background jobs)."""
    try:
        delete_faq(doc_name)
    except Exception as e:
        frappe.log_error(f"FAQ delete job failed for {doc_name}: {str(e)}", "Qdrant FAQ Sync")


# Hook handlers

def on_faq_insert(doc, method):
    """Hook: after_insert - Sync new FAQ to Qdrant."""
    if doc.enabled:
        frappe.enqueue(
            "ai_comms_hub.services.qdrant_faq_sync.sync_faq_by_name",
            doc_name=doc.name,
            queue="default",
            timeout=120,
            enqueue_after_commit=True
        )


def on_faq_update(doc, method):
    """Hook: on_update - Sync updated FAQ or delete if disabled."""
    if doc.enabled and doc.sync_status == "Pending":
        frappe.enqueue(
            "ai_comms_hub.services.qdrant_faq_sync.sync_faq_by_name",
            doc_name=doc.name,
            queue="default",
            timeout=120,
            enqueue_after_commit=True
        )
    elif not doc.enabled and doc.qdrant_point_id:
        # Remove from Qdrant when disabled
        frappe.enqueue(
            "ai_comms_hub.services.qdrant_faq_sync.delete_faq_by_name",
            doc_name=doc.name,
            queue="default",
            timeout=60,
            enqueue_after_commit=True
        )


def on_faq_delete(doc, method):
    """Hook: on_trash - Remove FAQ from Qdrant."""
    if doc.qdrant_point_id:
        delete_faq(doc.name)


# Scheduled tasks

def verify_sync_integrity():
    """Daily job to verify all enabled FAQs are synced."""
    faqs_to_sync = frappe.get_all(
        "Chatwoot FAQ",
        filters={
            "enabled": 1,
            "sync_status": ["in", ["Not Synced", "Failed", "Pending"]]
        },
        fields=["name"]
    )

    for faq in faqs_to_sync:
        frappe.enqueue(
            "ai_comms_hub.services.qdrant_faq_sync.sync_faq_by_name",
            doc_name=faq.name,
            queue="long",
            timeout=120
        )

    if faqs_to_sync:
        frappe.logger().info(f"Queued {len(faqs_to_sync)} FAQs for sync verification")


# API endpoints

@frappe.whitelist()
def search_faqs(query: str, limit: int = 5, score_threshold: float = 0.7) -> List[Dict]:
    """
    Search FAQs by semantic similarity.

    Args:
        query: Search query
        limit: Max results
        score_threshold: Minimum similarity score

    Returns:
        list: Matching FAQs with scores
    """
    try:
        settings = get_settings()
        embedding = generate_embedding(query)

        url = f"{settings['qdrant_url']}/collections/{COLLECTION_NAME}/points/search"

        response = requests.post(
            url,
            headers=get_qdrant_headers(settings),
            json={
                "vector": embedding,
                "limit": int(limit),
                "score_threshold": float(score_threshold),
                "with_payload": True,
                "filter": {
                    "must": [
                        {"key": "doctype", "match": {"value": "Chatwoot FAQ"}}
                    ]
                }
            },
            timeout=10
        )
        response.raise_for_status()
        results = response.json()

        return [
            {
                "doc_name": hit["payload"].get("doc_name"),
                "question": hit["payload"].get("question"),
                "answer": hit["payload"].get("answer"),
                "category": hit["payload"].get("category"),
                "score": hit["score"]
            }
            for hit in results.get("result", [])
        ]

    except Exception as e:
        frappe.log_error(f"FAQ search failed: {str(e)}", "Qdrant FAQ Sync")
        return []


@frappe.whitelist()
def manual_sync_all_faqs():
    """API endpoint to manually trigger full FAQ sync."""
    frappe.enqueue(
        "ai_comms_hub.services.qdrant_faq_sync._bulk_sync_all",
        queue="long",
        timeout=1800
    )
    return {"status": "started", "message": "Bulk FAQ sync started in background"}


def _bulk_sync_all():
    """Internal bulk sync function."""
    ensure_collection_exists()

    faqs = frappe.get_all(
        "Chatwoot FAQ",
        filters={"enabled": 1},
        fields=["name"]
    )

    success_count = 0
    error_count = 0

    for faq in faqs:
        try:
            sync_faq_by_name(faq.name)
            success_count += 1
        except Exception:
            error_count += 1

    frappe.logger().info(f"Bulk FAQ sync complete: {success_count} success, {error_count} errors")


@frappe.whitelist()
def import_existing_faqs():
    """
    Import existing FAQs from Qdrant into Frappe Chatwoot FAQ DocType.

    This fetches all FAQ-type points from chatwoot_knowledge_v2 that don't have
    doctype="Chatwoot FAQ" (i.e., not created by Frappe) and creates corresponding
    Frappe documents.

    Returns:
        dict: Import results with counts
    """
    frappe.enqueue(
        "ai_comms_hub.services.qdrant_faq_sync._import_existing_faqs_job",
        queue="long",
        timeout=1800
    )
    return {"status": "started", "message": "FAQ import started in background"}


def _import_existing_faqs_job():
    """Background job to import existing FAQs from Qdrant."""
    settings = get_settings()

    imported = 0
    skipped = 0
    errors = 0

    # Scroll through all points in the collection
    offset = None
    batch_size = 100

    while True:
        try:
            url = f"{settings['qdrant_url']}/collections/{COLLECTION_NAME}/points/scroll"

            payload = {
                "limit": batch_size,
                "with_payload": True,
                "with_vector": False
            }
            if offset:
                payload["offset"] = offset

            response = requests.post(
                url,
                headers=get_qdrant_headers(settings),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            points = result.get("result", {}).get("points", [])
            next_offset = result.get("result", {}).get("next_page_offset")

            if not points:
                break

            for point in points:
                point_payload = point.get("payload", {})
                point_id = point.get("id")

                # Skip if already imported from Frappe
                if point_payload.get("doctype") == "Chatwoot FAQ":
                    skipped += 1
                    continue

                # Skip if not a FAQ type
                if point_payload.get("type") != "faq":
                    skipped += 1
                    continue

                # Check if already imported (by checking qdrant_point_id)
                existing = frappe.db.exists("Chatwoot FAQ", {"qdrant_point_id": str(point_id)})
                if existing:
                    skipped += 1
                    continue

                try:
                    # Extract FAQ data
                    question = point_payload.get("question", "")
                    answer = point_payload.get("answer", "") or point_payload.get("content", "")
                    category_name = point_payload.get("category", "")

                    if not question or not answer:
                        skipped += 1
                        continue

                    # Ensure category exists
                    category_link = None
                    if category_name:
                        category_link = _ensure_category_exists(category_name)

                    # Create FAQ document
                    faq_doc = frappe.new_doc("Chatwoot FAQ")
                    faq_doc.question = question[:140] if len(question) > 140 else question
                    faq_doc.answer = answer
                    faq_doc.category = category_link
                    faq_doc.enabled = 1
                    faq_doc.sync_status = "Synced"  # Already in Qdrant
                    faq_doc.qdrant_point_id = str(point_id)
                    faq_doc.last_synced = now_datetime()

                    # Set tags from source if available
                    source = point_payload.get("source", "")
                    if source:
                        faq_doc.tags = source

                    faq_doc.flags.ignore_permissions = True
                    faq_doc.flags.ignore_hooks = True  # Don't trigger sync hooks
                    faq_doc.insert()

                    # Update sync_status after insert (before_save resets it)
                    frappe.db.set_value("Chatwoot FAQ", faq_doc.name, {
                        "sync_status": "Synced",
                        "last_synced": now_datetime()
                    }, update_modified=False)

                    imported += 1

                except Exception as e:
                    frappe.log_error(
                        f"Failed to import FAQ: {question[:50]}... Error: {str(e)}",
                        "Qdrant FAQ Import"
                    )
                    errors += 1

            # Move to next page
            if next_offset:
                offset = next_offset
            else:
                break

        except Exception as e:
            frappe.log_error(f"FAQ import batch failed: {str(e)}", "Qdrant FAQ Import")
            break

    frappe.db.commit()

    message = f"FAQ Import complete: {imported} imported, {skipped} skipped, {errors} errors"
    frappe.logger().info(message)

    # Create a notification
    frappe.publish_realtime(
        "msgprint",
        {"message": message, "title": "FAQ Import Complete"},
        user=frappe.session.user
    )

    return {
        "status": "complete",
        "imported": imported,
        "skipped": skipped,
        "errors": errors
    }


def _ensure_category_exists(category_name: str) -> Optional[str]:
    """Create category if it doesn't exist, return the category name for linking."""
    # Normalize category name
    category_name = category_name.strip().title()

    if not category_name:
        return None

    # Check if exists
    existing = frappe.db.exists("Chatwoot FAQ Category", {"category_name": category_name})
    if existing:
        return existing

    try:
        # Create new category
        cat_doc = frappe.new_doc("Chatwoot FAQ Category")
        cat_doc.category_name = category_name
        cat_doc.flags.ignore_permissions = True
        cat_doc.insert()
        return cat_doc.name
    except Exception as e:
        frappe.log_error(f"Failed to create category {category_name}: {str(e)}", "Qdrant FAQ Import")
        return None


def cleanup_test_faq(doc_name: str = "FAQ-20404"):
    """Remove test text from FAQ and sync."""
    doc = frappe.get_doc("Chatwoot FAQ", doc_name)

    # Remove test text
    doc.answer = doc.answer.replace(" [EDIT TEST - This was added via Frappe]", "")
    doc.save()
    frappe.db.commit()

    # Sync immediately
    result = sync_faq(doc)

    if result.get("status") == "success":
        frappe.db.set_value("Chatwoot FAQ", doc_name, {
            "sync_status": "Synced",
            "last_synced": now_datetime(),
            "sync_error": ""
        }, update_modified=False)
        frappe.db.commit()

    return {"status": "cleaned", "sync_result": result}


@frappe.whitelist()
def fix_imported_sync_status():
    """Fix sync_status for imported FAQs that have qdrant_point_id but status is Pending."""
    count = frappe.db.sql("""
        UPDATE `tabChatwoot FAQ`
        SET sync_status = 'Synced'
        WHERE qdrant_point_id IS NOT NULL
        AND sync_status != 'Synced'
    """)
    frappe.db.commit()
    return {"status": "success", "message": "Updated sync status for imported FAQs"}


@frappe.whitelist()
def get_qdrant_faq_stats():
    """Get statistics about FAQs in Qdrant collection."""
    settings = get_settings()

    try:
        # Get collection info
        url = f"{settings['qdrant_url']}/collections/{COLLECTION_NAME}"
        response = requests.get(url, headers=get_qdrant_headers(settings), timeout=10)
        response.raise_for_status()
        collection_info = response.json()

        total_points = collection_info.get("result", {}).get("points_count", 0)

        # Count FAQs by source
        # Count Frappe FAQs
        frappe_count_url = f"{settings['qdrant_url']}/collections/{COLLECTION_NAME}/points/count"
        frappe_response = requests.post(
            frappe_count_url,
            headers=get_qdrant_headers(settings),
            json={
                "filter": {
                    "must": [
                        {"key": "doctype", "match": {"value": "Chatwoot FAQ"}}
                    ]
                }
            },
            timeout=10
        )
        frappe_response.raise_for_status()
        frappe_faq_count = frappe_response.json().get("result", {}).get("count", 0)

        # Count legacy FAQs (type=faq but not from Frappe)
        legacy_response = requests.post(
            frappe_count_url,
            headers=get_qdrant_headers(settings),
            json={
                "filter": {
                    "must": [
                        {"key": "type", "match": {"value": "faq"}}
                    ],
                    "must_not": [
                        {"key": "doctype", "match": {"value": "Chatwoot FAQ"}}
                    ]
                }
            },
            timeout=10
        )
        legacy_response.raise_for_status()
        legacy_faq_count = legacy_response.json().get("result", {}).get("count", 0)

        # Count FAQs in Frappe
        frappe_doc_count = frappe.db.count("Chatwoot FAQ")
        frappe_synced_count = frappe.db.count("Chatwoot FAQ", {"sync_status": "Synced"})

        return {
            "status": "success",
            "qdrant": {
                "total_points": total_points,
                "frappe_faqs": frappe_faq_count,
                "legacy_faqs": legacy_faq_count
            },
            "frappe": {
                "total_docs": frappe_doc_count,
                "synced_docs": frappe_synced_count
            }
        }

    except Exception as e:
        frappe.log_error(f"Failed to get FAQ stats: {str(e)}", "Qdrant FAQ Sync")
        return {
            "status": "error",
            "error": str(e)
        }
