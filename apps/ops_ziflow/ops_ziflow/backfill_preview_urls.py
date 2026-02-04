import frappe
import json

def run():
    """Backfill preview_url from raw_payload for proofs missing it."""

    # Get proofs without preview_url but with raw_payload
    proofs = frappe.get_all(
        "OPS ZiFlow Proof",
        filters={
            "preview_url": ["is", "not set"],
            "raw_payload": ["is", "set"]
        },
        fields=["name", "raw_payload"],
        limit=0  # All records
    )

    print(f"Found {len(proofs)} proofs without preview_url")

    updated = 0
    errors = 0

    for proof in proofs:
        try:
            payload = json.loads(proof.raw_payload)

            # Try to extract preview URL (prefer image_link over thumbnail_link)
            preview_url = None
            if payload.get("image_link"):
                preview_url = payload["image_link"]
            elif payload.get("thumbnail_link"):
                preview_url = payload["thumbnail_link"]

            if preview_url:
                frappe.db.set_value("OPS ZiFlow Proof", proof.name, "preview_url", preview_url, update_modified=False)
                updated += 1
                if updated % 100 == 0:
                    print(f"Updated {updated} proofs...")
                    frappe.db.commit()
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"Error processing {proof.name}: {e}")

    frappe.db.commit()
    print(f"\nDone! Updated: {updated}, Errors: {errors}")
