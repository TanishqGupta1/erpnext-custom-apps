#!/usr/bin/env python3
# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

"""
Unit tests for RAG (Retrieval-Augmented Generation) module.
"""

import unittest
import frappe
from ai_comms_hub.api.rag import (
	get_qdrant_settings,
	generate_embedding,
	query_knowledge_base,
	add_to_knowledge_base,
	delete_from_knowledge_base,
	update_knowledge_base
)


class TestRAG(unittest.TestCase):
	"""Test RAG functionality."""

	def setUp(self):
		"""Set up test environment."""
		self.settings = get_qdrant_settings()
		self.test_article_id = None

	def test_get_qdrant_settings(self):
		"""Test Qdrant settings retrieval."""
		self.assertIsNotNone(self.settings)
		self.assertIn("url", self.settings)
		self.assertIn("collection", self.settings)

	def test_generate_embedding(self):
		"""Test embedding generation."""
		text = "This is a test product description."

		embedding = generate_embedding(text)

		self.assertIsNotNone(embedding)
		self.assertIsInstance(embedding, list)
		self.assertEqual(len(embedding), 1536)  # OpenAI embedding size
		self.assertTrue(all(isinstance(x, float) for x in embedding))

	def test_generate_embedding_empty_text(self):
		"""Test embedding generation with empty text."""
		with self.assertRaises(ValueError):
			generate_embedding("")

	def test_add_to_knowledge_base(self):
		"""Test adding document to knowledge base."""
		# Create test article
		article = frappe.get_doc({
			"doctype": "Knowledge Base Article",
			"title": "Test Product",
			"content": "This is a test product for unit testing. It has great features.",
			"category": "Products"
		})
		article.insert(ignore_permissions=True)
		self.test_article_id = article.name

		# Add to vector database
		result = add_to_knowledge_base(article.name)

		self.assertTrue(result)
		frappe.db.commit()

	def test_query_knowledge_base_simple(self):
		"""Test simple knowledge base query."""
		query = "test product"

		results = query_knowledge_base(query, top_k=5)

		self.assertIsNotNone(results)
		self.assertIsInstance(results, list)

		if len(results) > 0:
			result = results[0]
			self.assertIn("id", result)
			self.assertIn("score", result)
			self.assertIn("content", result)

	def test_query_knowledge_base_with_filter(self):
		"""Test knowledge base query with category filter."""
		query = "product"
		filters = {"category": "Products"}

		results = query_knowledge_base(query, top_k=5, filters=filters)

		self.assertIsNotNone(results)
		self.assertIsInstance(results, list)

	def test_query_knowledge_base_confidence_threshold(self):
		"""Test confidence threshold filtering."""
		query = "test product"

		# High threshold should return fewer results
		high_threshold_results = query_knowledge_base(
			query,
			top_k=10,
			min_score=0.9
		)

		# Low threshold should return more results
		low_threshold_results = query_knowledge_base(
			query,
			top_k=10,
			min_score=0.5
		)

		# Low threshold should have >= results than high threshold
		self.assertGreaterEqual(
			len(low_threshold_results),
			len(high_threshold_results)
		)

	def test_update_knowledge_base(self):
		"""Test updating knowledge base article."""
		if not self.test_article_id:
			self.skipTest("Test article not created")

		# Update article content
		article = frappe.get_doc("Knowledge Base Article", self.test_article_id)
		article.content = "Updated content with new information about the test product."
		article.save()

		# Update in vector database
		result = update_knowledge_base(self.test_article_id)

		self.assertTrue(result)

	def test_delete_from_knowledge_base(self):
		"""Test deleting from knowledge base."""
		if not self.test_article_id:
			self.skipTest("Test article not created")

		# Delete from vector database
		result = delete_from_knowledge_base(self.test_article_id)

		self.assertTrue(result)

	def test_semantic_search_relevance(self):
		"""Test semantic search returns relevant results."""
		query = "how do I check my order status?"

		results = query_knowledge_base(query, top_k=3)

		# Results should be semantically relevant
		self.assertIsNotNone(results)

		# Check if any result contains relevant keywords
		if len(results) > 0:
			combined_text = " ".join(r.get("content", "") for r in results).lower()
			# At least one of these terms should appear
			relevant_terms = ["order", "status", "track", "shipment", "delivery"]
			self.assertTrue(any(term in combined_text for term in relevant_terms))

	def test_chunking_long_content(self):
		"""Test handling of long content (chunking)."""
		# Create article with long content
		long_content = " ".join(["Test sentence number {}.".format(i) for i in range(500)])

		article = frappe.get_doc({
			"doctype": "Knowledge Base Article",
			"title": "Long Test Article",
			"content": long_content,
			"category": "Testing"
		})
		article.insert(ignore_permissions=True)

		# Add to knowledge base (should chunk automatically)
		result = add_to_knowledge_base(article.name)

		self.assertTrue(result)

		# Cleanup
		frappe.delete_doc("Knowledge Base Article", article.name, ignore_permissions=True)

	def tearDown(self):
		"""Clean up after tests."""
		# Delete test article if it exists
		if self.test_article_id and frappe.db.exists("Knowledge Base Article", self.test_article_id):
			frappe.delete_doc("Knowledge Base Article", self.test_article_id, ignore_permissions=True)
			frappe.db.commit()


if __name__ == "__main__":
	unittest.main()
