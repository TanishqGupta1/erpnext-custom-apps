#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Qdrant Setup Script

This script initializes the Qdrant vector database for AI Communications Hub.

Usage:
    # From Frappe bench
    bench --site <site-name> execute ai_comms_hub.scripts.setup_qdrant.main

    # Or run directly
    python3 setup_qdrant.py
"""

import frappe
from frappe import _
import requests
import sys


def main():
	"""
	Main setup function for Qdrant.

	Steps:
	1. Check Qdrant connection
	2. Create collection if not exists
	3. Verify collection structure
	4. Sync initial knowledge base
	"""
	print("=" * 60)
	print("AI Communications Hub - Qdrant Setup")
	print("=" * 60)

	try:
		# Get settings
		settings = get_qdrant_settings()

		# Step 1: Check connection
		print("\n[1/4] Checking Qdrant connection...")
		if not check_qdrant_connection(settings):
			print("❌ Failed to connect to Qdrant")
			sys.exit(1)
		print("✅ Connected to Qdrant successfully")

		# Step 2: Create collection
		print("\n[2/4] Creating collection...")
		if create_collection(settings):
			print(f"✅ Collection '{settings['collection']}' created")
		else:
			print(f"ℹ️  Collection '{settings['collection']}' already exists")

		# Step 3: Verify collection
		print("\n[3/4] Verifying collection structure...")
		if verify_collection(settings):
			print("✅ Collection structure verified")
		else:
			print("❌ Collection structure verification failed")
			sys.exit(1)

		# Step 4: Sync knowledge base
		print("\n[4/4] Syncing initial knowledge base...")
		count = sync_knowledge_base(settings)
		print(f"✅ Synced {count} documents to knowledge base")

		print("\n" + "=" * 60)
		print("✅ Qdrant setup completed successfully!")
		print("=" * 60)

	except Exception as e:
		print(f"\n❌ Error during setup: {str(e)}")
		frappe.log_error(f"Qdrant setup failed: {str(e)}", "Qdrant Setup Error")
		sys.exit(1)


def get_qdrant_settings():
	"""
	Get Qdrant settings from AI Communications Hub Settings.

	Returns:
		dict: Qdrant configuration
	"""
	if frappe.db.exists("AI Communications Hub Settings", "AI Communications Hub Settings"):
		settings_doc = frappe.get_single("AI Communications Hub Settings")
		return {
			"url": settings_doc.qdrant_url or "http://qdrant:6333",
			"collection": settings_doc.qdrant_collection or "knowledge_base",
			"vector_size": settings_doc.qdrant_vector_size or 1536,
			"distance": "Cosine",
			"on_disk_payload": True
		}
	else:
		# Use defaults if settings don't exist
		return {
			"url": "http://qdrant:6333",
			"collection": "knowledge_base",
			"vector_size": 1536,
			"distance": "Cosine",
			"on_disk_payload": True
		}


def check_qdrant_connection(settings):
	"""
	Check if Qdrant is accessible.

	Args:
		settings (dict): Qdrant configuration

	Returns:
		bool: True if connection successful
	"""
	try:
		response = requests.get(f"{settings['url']}/", timeout=5)
		return response.status_code == 200
	except Exception as e:
		print(f"Connection error: {str(e)}")
		return False


def create_collection(settings):
	"""
	Create Qdrant collection if it doesn't exist.

	Args:
		settings (dict): Qdrant configuration

	Returns:
		bool: True if collection was created, False if already exists
	"""
	try:
		# Check if collection exists
		response = requests.get(
			f"{settings['url']}/collections/{settings['collection']}",
			timeout=5
		)

		if response.status_code == 200:
			return False  # Collection already exists

		# Create collection
		payload = {
			"vectors": {
				"size": settings["vector_size"],
				"distance": settings["distance"]
			},
			"on_disk_payload": settings["on_disk_payload"]
		}

		response = requests.put(
			f"{settings['url']}/collections/{settings['collection']}",
			json=payload,
			timeout=10
		)

		if response.status_code in [200, 201]:
			return True
		else:
			raise Exception(f"Failed to create collection: {response.text}")

	except requests.exceptions.RequestException as e:
		raise Exception(f"Request failed: {str(e)}")


def verify_collection(settings):
	"""
	Verify collection exists and has correct structure.

	Args:
		settings (dict): Qdrant configuration

	Returns:
		bool: True if verification passed
	"""
	try:
		response = requests.get(
			f"{settings['url']}/collections/{settings['collection']}",
			timeout=5
		)

		if response.status_code != 200:
			return False

		data = response.json()
		config = data.get("result", {}).get("config", {})

		# Verify vector size
		vectors_config = config.get("params", {}).get("vectors", {})
		actual_size = vectors_config.get("size")

		if actual_size != settings["vector_size"]:
			print(f"⚠️  Warning: Vector size mismatch. Expected {settings['vector_size']}, got {actual_size}")
			return False

		return True

	except Exception as e:
		print(f"Verification error: {str(e)}")
		return False


def sync_knowledge_base(settings):
	"""
	Sync initial knowledge base from ERPNext.

	Args:
		settings (dict): Qdrant configuration

	Returns:
		int: Number of documents synced
	"""
	try:
		# Use the RAG module's sync function
		from ai_comms_hub.api.rag import sync_erpnext_knowledge

		count = sync_erpnext_knowledge()
		return count

	except Exception as e:
		print(f"Sync error: {str(e)}")
		# Don't fail the entire setup if sync fails
		return 0


def delete_collection(settings):
	"""
	Delete Qdrant collection (for cleanup/reset).

	WARNING: This deletes all data in the collection!

	Args:
		settings (dict): Qdrant configuration

	Returns:
		bool: True if deletion successful
	"""
	try:
		response = requests.delete(
			f"{settings['url']}/collections/{settings['collection']}",
			timeout=10
		)

		return response.status_code in [200, 204]

	except Exception as e:
		print(f"Deletion error: {str(e)}")
		return False


def recreate_collection(settings):
	"""
	Delete and recreate collection (full reset).

	Args:
		settings (dict): Qdrant configuration
	"""
	print("\n⚠️  WARNING: This will delete all existing data!")
	confirmation = input("Type 'yes' to confirm: ")

	if confirmation.lower() != "yes":
		print("Cancelled")
		return

	print("\nDeleting collection...")
	if delete_collection(settings):
		print("✅ Collection deleted")
	else:
		print("❌ Failed to delete collection")
		return

	print("\nCreating new collection...")
	if create_collection(settings):
		print("✅ Collection created")
	else:
		print("❌ Failed to create collection")
		return

	print("\nSyncing knowledge base...")
	count = sync_knowledge_base(settings)
	print(f"✅ Synced {count} documents")


def get_collection_info(settings):
	"""
	Get detailed information about the collection.

	Args:
		settings (dict): Qdrant configuration
	"""
	try:
		response = requests.get(
			f"{settings['url']}/collections/{settings['collection']}",
			timeout=5
		)

		if response.status_code == 200:
			data = response.json()
			result = data.get("result", {})

			print(f"\n📊 Collection: {settings['collection']}")
			print(f"   Status: {result.get('status')}")
			print(f"   Vectors Count: {result.get('vectors_count', 0):,}")
			print(f"   Points Count: {result.get('points_count', 0):,}")

			config = result.get("config", {})
			vectors = config.get("params", {}).get("vectors", {})
			print(f"   Vector Size: {vectors.get('size')}")
			print(f"   Distance: {vectors.get('distance')}")

		else:
			print(f"❌ Failed to get collection info: {response.status_code}")

	except Exception as e:
		print(f"Error: {str(e)}")


# CLI interface
if __name__ == "__main__":
	import sys

	if len(sys.argv) > 1:
		command = sys.argv[1]

		if command == "info":
			settings = get_qdrant_settings()
			get_collection_info(settings)

		elif command == "recreate":
			settings = get_qdrant_settings()
			recreate_collection(settings)

		elif command == "delete":
			settings = get_qdrant_settings()
			print("\n⚠️  WARNING: This will delete all data!")
			confirmation = input("Type 'yes' to confirm: ")
			if confirmation.lower() == "yes":
				if delete_collection(settings):
					print("✅ Collection deleted")
				else:
					print("❌ Failed to delete collection")

		else:
			print(f"Unknown command: {command}")
			print("\nAvailable commands:")
			print("  python setup_qdrant.py          - Run full setup")
			print("  python setup_qdrant.py info     - Show collection info")
			print("  python setup_qdrant.py recreate - Delete and recreate")
			print("  python setup_qdrant.py delete   - Delete collection")
	else:
		# Run main setup
		main()
