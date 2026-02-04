import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, now_datetime
import re


class KnowledgeBaseArticle(Document):
	def validate(self):
		self.validate_priority()
		self.set_author()
		self.generate_ai_summary()

	def before_save(self):
		if self.is_ai_enabled and self.has_value_changed("content"):
			self.embedding_status = "Pending"

	def on_update(self):
		if self.status == "Published" and not self.published_date:
			self.db_set("published_date", nowdate())

	def validate_priority(self):
		"""Ensure priority is within valid range."""
		if self.ai_priority < 1:
			self.ai_priority = 1
		elif self.ai_priority > 10:
			self.ai_priority = 10

	def set_author(self):
		"""Set author if not set."""
		if not self.author:
			self.author = frappe.session.user

	def generate_ai_summary(self):
		"""Generate AI summary if not provided."""
		if not self.ai_summary and self.content:
			# Strip HTML tags and create a simple summary
			text = re.sub(r'<[^>]+>', '', self.content)
			text = ' '.join(text.split())  # Normalize whitespace
			if len(text) > 300:
				self.ai_summary = text[:297] + "..."
			else:
				self.ai_summary = text

	def get_content_for_ai(self):
		"""Get content optimized for AI context."""
		content_parts = []

		if self.title:
			content_parts.append(f"Title: {self.title}")

		if self.ai_summary:
			content_parts.append(f"Summary: {self.ai_summary}")
		elif self.summary:
			content_parts.append(f"Summary: {self.summary}")

		if self.keywords:
			content_parts.append(f"Keywords: {self.keywords}")

		# Get plain text content
		if self.content:
			plain_content = re.sub(r'<[^>]+>', '', self.content)
			plain_content = ' '.join(plain_content.split())
			content_parts.append(f"Content: {plain_content}")

		return "\n".join(content_parts)

	def increment_view(self):
		"""Increment view count."""
		frappe.db.set_value(
			"Knowledge Base Article",
			self.name,
			"view_count",
			self.view_count + 1,
			update_modified=False
		)

	def record_ai_usage(self):
		"""Record that this article was used in AI response."""
		frappe.db.set_value(
			"Knowledge Base Article",
			self.name,
			{
				"ai_usage_count": self.ai_usage_count + 1,
				"last_used_in_ai": now_datetime()
			},
			update_modified=False
		)

	def mark_helpful(self, helpful=True):
		"""Mark article as helpful or not helpful."""
		if helpful:
			frappe.db.set_value(
				"Knowledge Base Article",
				self.name,
				"helpful_count",
				self.helpful_count + 1,
				update_modified=False
			)
		else:
			frappe.db.set_value(
				"Knowledge Base Article",
				self.name,
				"not_helpful_count",
				self.not_helpful_count + 1,
				update_modified=False
			)


@frappe.whitelist()
def search_articles(query, category=None, limit=10):
	"""
	Search knowledge base articles.

	Args:
		query: Search query string
		category: Optional category filter
		limit: Maximum number of results

	Returns:
		List of matching articles
	"""
	filters = {"status": "Published", "is_ai_enabled": 1}

	if category:
		filters["category"] = category

	# Search in title, summary, keywords, and content
	articles = frappe.get_all(
		"Knowledge Base Article",
		filters=filters,
		or_filters=[
			["title", "like", f"%{query}%"],
			["summary", "like", f"%{query}%"],
			["keywords", "like", f"%{query}%"],
			["content", "like", f"%{query}%"]
		],
		fields=["name", "title", "summary", "category", "ai_priority", "ai_usage_count"],
		order_by="ai_priority desc, ai_usage_count desc",
		limit=limit
	)

	return articles


@frappe.whitelist()
def get_articles_for_ai_context(query, max_articles=5, max_tokens=2000):
	"""
	Get relevant articles for AI context.

	Args:
		query: User query or conversation context
		max_articles: Maximum number of articles to return
		max_tokens: Maximum total tokens

	Returns:
		List of articles with content for AI
	"""
	# Search for relevant articles
	articles = search_articles(query, limit=max_articles * 2)

	result = []
	total_tokens = 0

	for article in articles:
		if len(result) >= max_articles:
			break

		doc = frappe.get_doc("Knowledge Base Article", article.name)
		content = doc.get_content_for_ai()

		# Rough token estimation (1 token ≈ 4 characters)
		estimated_tokens = len(content) // 4

		if total_tokens + estimated_tokens <= max_tokens:
			result.append({
				"name": doc.name,
				"title": doc.title,
				"content": content,
				"category": doc.category,
				"tokens": estimated_tokens
			})
			total_tokens += estimated_tokens

			# Record AI usage
			doc.record_ai_usage()

	return result
