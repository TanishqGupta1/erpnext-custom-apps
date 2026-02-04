import frappe
from frappe import _
from frappe.utils import nowdate, now_datetime
import json


@frappe.whitelist()
def get_categories(include_inactive=False):
	"""
	Get all knowledge base categories.

	Args:
		include_inactive: Include inactive categories

	Returns:
		List of categories with article counts
	"""
	filters = {}
	if not include_inactive:
		filters["is_active"] = 1

	categories = frappe.get_all(
		"Knowledge Base Category",
		filters=filters,
		fields=["name", "category_name", "description", "parent_category", "icon", "include_in_ai_context", "priority"],
		order_by="priority desc, category_name asc"
	)

	# Add article counts
	for cat in categories:
		cat["article_count"] = frappe.db.count(
			"Knowledge Base Article",
			filters={"category": cat.name, "status": "Published"}
		)
		cat["total_article_count"] = frappe.db.count(
			"Knowledge Base Article",
			filters={"category": cat.name}
		)

	return categories


@frappe.whitelist()
def get_articles(category=None, status=None, search=None, page=1, page_size=20):
	"""
	Get knowledge base articles with filters.

	Args:
		category: Filter by category
		status: Filter by status
		search: Search term
		page: Page number
		page_size: Items per page

	Returns:
		Paginated list of articles
	"""
	filters = {}

	if category:
		filters["category"] = category
	if status:
		filters["status"] = status

	or_filters = None
	if search:
		or_filters = [
			["title", "like", f"%{search}%"],
			["summary", "like", f"%{search}%"],
			["keywords", "like", f"%{search}%"]
		]

	# Get total count
	total = frappe.db.count("Knowledge Base Article", filters=filters)

	# Get paginated results
	start = (int(page) - 1) * int(page_size)
	articles = frappe.get_all(
		"Knowledge Base Article",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "title", "category", "status", "author",
			"published_date", "view_count", "helpful_count",
			"ai_usage_count", "is_ai_enabled", "embedding_status"
		],
		order_by="modified desc",
		start=start,
		page_length=int(page_size)
	)

	return {
		"articles": articles,
		"total": total,
		"page": int(page),
		"page_size": int(page_size),
		"total_pages": (total + int(page_size) - 1) // int(page_size)
	}


@frappe.whitelist()
def create_article(title, category, content, summary=None, keywords=None, is_ai_enabled=1, status="Draft"):
	"""
	Create a new knowledge base article.

	Args:
		title: Article title
		category: Category name
		content: Article content (HTML)
		summary: Brief summary
		keywords: Comma-separated keywords
		is_ai_enabled: Enable for AI
		status: Initial status

	Returns:
		Created article name
	"""
	doc = frappe.get_doc({
		"doctype": "Knowledge Base Article",
		"title": title,
		"category": category,
		"content": content,
		"summary": summary,
		"keywords": keywords,
		"is_ai_enabled": is_ai_enabled,
		"status": status,
		"author": frappe.session.user
	})
	doc.insert()
	frappe.db.commit()

	return {"name": doc.name, "message": "Article created successfully"}


@frappe.whitelist()
def update_article(name, **kwargs):
	"""
	Update an existing knowledge base article.

	Args:
		name: Article name
		**kwargs: Fields to update

	Returns:
		Updated article name
	"""
	doc = frappe.get_doc("Knowledge Base Article", name)

	allowed_fields = [
		"title", "category", "content", "summary", "keywords",
		"is_ai_enabled", "status", "ai_priority", "max_tokens"
	]

	for field in allowed_fields:
		if field in kwargs:
			setattr(doc, field, kwargs[field])

	doc.save()
	frappe.db.commit()

	return {"name": doc.name, "message": "Article updated successfully"}


@frappe.whitelist()
def publish_article(name):
	"""Publish an article."""
	doc = frappe.get_doc("Knowledge Base Article", name)
	doc.status = "Published"
	doc.published_date = nowdate()
	doc.save()
	frappe.db.commit()

	return {"name": doc.name, "message": "Article published successfully"}


@frappe.whitelist()
def archive_article(name):
	"""Archive an article."""
	doc = frappe.get_doc("Knowledge Base Article", name)
	doc.status = "Archived"
	doc.save()
	frappe.db.commit()

	return {"name": doc.name, "message": "Article archived successfully"}


@frappe.whitelist()
def mark_article_feedback(name, helpful):
	"""
	Mark article as helpful or not helpful.

	Args:
		name: Article name
		helpful: True if helpful, False if not
	"""
	doc = frappe.get_doc("Knowledge Base Article", name)
	doc.mark_helpful(helpful=helpful)

	return {"message": "Feedback recorded"}


@frappe.whitelist()
def get_kb_stats():
	"""Get knowledge base statistics."""
	total_articles = frappe.db.count("Knowledge Base Article")
	published = frappe.db.count("Knowledge Base Article", filters={"status": "Published"})
	draft = frappe.db.count("Knowledge Base Article", filters={"status": "Draft"})
	archived = frappe.db.count("Knowledge Base Article", filters={"status": "Archived"})

	ai_enabled = frappe.db.count("Knowledge Base Article", filters={"is_ai_enabled": 1, "status": "Published"})

	total_categories = frappe.db.count("Knowledge Base Category")
	active_categories = frappe.db.count("Knowledge Base Category", filters={"is_active": 1})

	# Most used articles
	top_articles = frappe.get_all(
		"Knowledge Base Article",
		filters={"status": "Published"},
		fields=["name", "title", "ai_usage_count", "view_count"],
		order_by="ai_usage_count desc",
		limit=5
	)

	# Categories with most articles
	category_stats = frappe.db.sql("""
		SELECT category, COUNT(*) as count
		FROM `tabKnowledge Base Article`
		WHERE status = 'Published'
		GROUP BY category
		ORDER BY count DESC
		LIMIT 5
	""", as_dict=True)

	return {
		"total_articles": total_articles,
		"published": published,
		"draft": draft,
		"archived": archived,
		"ai_enabled": ai_enabled,
		"total_categories": total_categories,
		"active_categories": active_categories,
		"top_articles": top_articles,
		"category_stats": category_stats
	}


@frappe.whitelist()
def bulk_import_articles(articles_json):
	"""
	Bulk import articles from JSON.

	Args:
		articles_json: JSON string with list of articles

	Returns:
		Import results
	"""
	articles = json.loads(articles_json)
	results = {"success": 0, "failed": 0, "errors": []}

	for article_data in articles:
		try:
			# Check required fields
			if not article_data.get("title") or not article_data.get("content"):
				results["failed"] += 1
				results["errors"].append(f"Missing title or content: {article_data.get('title', 'Unknown')}")
				continue

			# Create or get category
			category = article_data.get("category", "General")
			if not frappe.db.exists("Knowledge Base Category", category):
				cat_doc = frappe.get_doc({
					"doctype": "Knowledge Base Category",
					"category_name": category
				})
				cat_doc.insert()

			# Create article
			doc = frappe.get_doc({
				"doctype": "Knowledge Base Article",
				"title": article_data["title"],
				"category": category,
				"content": article_data["content"],
				"summary": article_data.get("summary"),
				"keywords": article_data.get("keywords"),
				"is_ai_enabled": article_data.get("is_ai_enabled", 1),
				"status": article_data.get("status", "Draft"),
				"external_id": article_data.get("external_id"),
				"source_url": article_data.get("source_url")
			})
			doc.insert()
			results["success"] += 1

		except Exception as e:
			results["failed"] += 1
			results["errors"].append(f"Error importing {article_data.get('title', 'Unknown')}: {str(e)}")

	frappe.db.commit()
	return results


@frappe.whitelist()
def regenerate_embeddings(article_name=None):
	"""
	Queue embedding regeneration for articles.

	Args:
		article_name: Specific article or None for all pending
	"""
	if article_name:
		articles = [{"name": article_name}]
	else:
		articles = frappe.get_all(
			"Knowledge Base Article",
			filters={"embedding_status": "Pending", "is_ai_enabled": 1, "status": "Published"},
			fields=["name"]
		)

	for article in articles:
		frappe.db.set_value(
			"Knowledge Base Article",
			article["name"],
			"embedding_status",
			"Processing"
		)
		# In production, this would queue a background job to generate embeddings
		# frappe.enqueue(generate_embedding, article_name=article["name"])

	frappe.db.commit()

	return {"queued": len(articles)}
