"""
RAG (Retrieval-Augmented Generation) Module

Handles knowledge base search using Qdrant vector database.
"""

import frappe
from frappe import _
import requests
import json


def get_qdrant_settings():
	"""Get Qdrant settings from configuration"""
	settings = frappe.get_single("AI Communications Hub Settings")
	# Use get_password() for API key if it's a password field
	api_key = None
	if settings.qdrant_api_key:
		try:
			api_key = settings.get_password("qdrant_api_key")
		except Exception:
			api_key = settings.qdrant_api_key
	return {
		"url": settings.qdrant_url or "http://qdrant:6333",
		"collection": settings.qdrant_collection or "knowledge_base",
		"api_key": api_key
	}


def get_qdrant_headers(settings):
	"""Build headers for Qdrant API requests"""
	headers = {"Content-Type": "application/json"}
	if settings.get("api_key"):
		headers["api-key"] = settings["api_key"]
	return headers


def query_knowledge_base(query, top_k=5, score_threshold=0.7):
	"""
	Query knowledge base using semantic search.

	Args:
		query (str): Search query
		top_k (int): Number of results to return
		score_threshold (float): Minimum similarity score (0-1)

	Returns:
		list: List of matching documents with scores
	"""
	try:
		# Get query embedding
		embedding = get_embedding(query)

		# Search Qdrant
		settings = get_qdrant_settings()

		response = requests.post(
			f"{settings['url']}/collections/{settings['collection']}/points/search",
			headers=get_qdrant_headers(settings),
			json={
				"vector": embedding,
				"limit": top_k,
				"score_threshold": score_threshold,
				"with_payload": True
			},
			timeout=10
		)

		response.raise_for_status()
		results = response.json()

		# Format results
		documents = []
		for hit in results.get("result", []):
			documents.append({
				"id": hit["id"],
				"score": hit["score"],
				"title": hit["payload"].get("title", ""),
				"content": hit["payload"].get("content", ""),
				"source": hit["payload"].get("source", ""),
				"metadata": hit["payload"].get("metadata", {})
			})

		return documents

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Qdrant Query Error")
		return []


def get_embedding(text):
	"""
	Get text embedding from naga.ac API.

	Args:
		text (str): Text to embed

	Returns:
		list: Embedding vector
	"""
	from ai_comms_hub.api.llm import get_llm_settings

	settings = get_llm_settings()

	try:
		response = requests.post(
			f"{settings['api_url']}/embeddings",
			headers={
				"Authorization": f"Bearer {settings['api_key']}",
				"Content-Type": "application/json"
			},
			json={
				"model": "text-embedding-3-small",
				"input": text
			},
			timeout=10
		)

		response.raise_for_status()
		result = response.json()

		return result["data"][0]["embedding"]

	except Exception as e:
		frappe.log_error(f"Embedding Error: {str(e)}", "RAG")
		raise


def insert_document(content, title="", source="", metadata=None):
	"""
	Insert document into Qdrant knowledge base.

	Args:
		content (str): Document content
		title (str): Document title
		source (str): Source reference
		metadata (dict): Additional metadata

	Returns:
		dict: Insertion result
	"""
	try:
		# Get embedding
		embedding = get_embedding(content)

		# Insert into Qdrant
		settings = get_qdrant_settings()

		import hashlib
		doc_id = hashlib.md5(content.encode()).hexdigest()

		response = requests.put(
			f"{settings['url']}/collections/{settings['collection']}/points",
			headers=get_qdrant_headers(settings),
			json={
				"points": [
					{
						"id": doc_id,
						"vector": embedding,
						"payload": {
							"title": title,
							"content": content,
							"source": source,
							"metadata": metadata or {},
							"created_at": frappe.utils.now()
						}
					}
				]
			},
			timeout=10
		)

		response.raise_for_status()

		return {
			"status": "success",
			"doc_id": doc_id
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Qdrant Insert Error")
		return {
			"status": "error",
			"message": str(e)
		}


def create_collection_if_not_exists():
	"""Create Qdrant collection if it doesn't exist"""
	settings = get_qdrant_settings()

	try:
		# Check if collection exists
		response = requests.get(
			f"{settings['url']}/collections/{settings['collection']}",
			headers=get_qdrant_headers(settings),
			timeout=5
		)

		if response.status_code == 404:
			# Create collection
			create_response = requests.put(
				f"{settings['url']}/collections/{settings['collection']}",
				headers=get_qdrant_headers(settings),
				json={
					"vectors": {
						"size": 1536,  # text-embedding-3-small dimension
						"distance": "Cosine"
					}
				},
				timeout=10
			)

			create_response.raise_for_status()
			frappe.log("Qdrant collection created successfully")

	except Exception as e:
		frappe.log_error(f"Qdrant Collection Error: {str(e)}")


def sync_erpnext_knowledge():
	"""
	Sync ERPNext knowledge base to Qdrant.

	Syncs:
	- Products (Item doctype)
	- FAQs (FAQ doctype if exists)
	- Help Articles (Frappe Help Article doctype)
	- Company policies (from Website Settings or custom doctype)
	"""
	try:
		create_collection_if_not_exists()

		# Sync products
		sync_products()

		# Sync Help Articles
		sync_help_articles()

		# Sync FAQs (custom FAQ doctype if exists)
		sync_faqs()

		# Sync company information
		sync_company_info()

		frappe.logger().info("Knowledge base sync completed")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Knowledge Sync Error")


def sync_products():
	"""Sync products to knowledge base"""
	items = frappe.get_all(
		"Item",
		filters={"disabled": 0},
		fields=["name", "item_name", "description", "standard_rate", "item_group"]
	)

	for item in items:
		content = f"""Product: {item.item_name}
Description: {item.description or 'No description'}
Category: {item.item_group}
Price: {item.standard_rate or 'Contact for pricing'}
SKU: {item.name}
"""

		insert_document(
			content=content,
			title=item.item_name,
			source="ERPNext Item",
			metadata={
				"doctype": "Item",
				"name": item.name,
				"category": item.item_group
			}
		)

	frappe.logger().info(f"Synced {len(items)} products to knowledge base")


def sync_help_articles():
	"""
	Sync Help Articles to knowledge base.

	Help Article is a standard Frappe doctype for documentation/FAQ content.
	"""
	try:
		# Check if Help Article doctype exists
		if not frappe.db.exists("DocType", "Help Article"):
			frappe.logger().info("Help Article doctype not found, skipping")
			return

		# Get published help articles
		articles = frappe.get_all(
			"Help Article",
			filters={"published": 1},
			fields=["name", "title", "content", "category", "author", "likes", "helpful"]
		)

		if not articles:
			frappe.logger().info("No Help Articles found to sync")
			return

		synced_count = 0
		for article in articles:
			# Clean HTML content
			clean_content = frappe.utils.strip_html_tags(article.content or "")

			if not clean_content.strip():
				continue

			# Get category name if linked
			category_name = ""
			if article.category:
				category_doc = frappe.db.get_value("Help Category", article.category, "category_name")
				category_name = category_doc or article.category

			content = f"""Help Article: {article.title}
Category: {category_name}
Content: {clean_content}
"""

			insert_document(
				content=content,
				title=article.title,
				source="Help Article",
				metadata={
					"doctype": "Help Article",
					"name": article.name,
					"category": category_name,
					"author": article.author,
					"likes": article.likes or 0,
					"helpful": article.helpful or 0
				}
			)
			synced_count += 1

		frappe.logger().info(f"Synced {synced_count} Help Articles to knowledge base")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Help Article Sync Error")


def sync_faqs():
	"""
	Sync FAQs to knowledge base.

	Checks for common FAQ doctypes:
	- FAQ (custom)
	- Website FAQ
	- Frequently Asked Question
	"""
	try:
		# Check for various FAQ doctype names
		faq_doctypes = ["FAQ", "Website FAQ", "Frequently Asked Question"]
		faq_doctype = None

		for dt in faq_doctypes:
			if frappe.db.exists("DocType", dt):
				faq_doctype = dt
				break

		if not faq_doctype:
			# Try to get FAQs from Web Page content
			sync_faq_from_web_pages()
			return

		# Get FAQs
		faqs = frappe.get_all(
			faq_doctype,
			filters={"published": 1} if frappe.get_meta(faq_doctype).has_field("published") else {},
			fields=["name", "question", "answer", "category"] if frappe.get_meta(faq_doctype).has_field("category") else ["name", "question", "answer"]
		)

		if not faqs:
			frappe.logger().info(f"No FAQs found in {faq_doctype}")
			return

		synced_count = 0
		for faq in faqs:
			question = faq.get("question", "")
			answer = faq.get("answer", "")

			if not question or not answer:
				continue

			# Clean HTML from answer
			clean_answer = frappe.utils.strip_html_tags(answer)

			content = f"""FAQ Question: {question}
Answer: {clean_answer}
Category: {faq.get('category', 'General')}
"""

			insert_document(
				content=content,
				title=question,
				source=faq_doctype,
				metadata={
					"doctype": faq_doctype,
					"name": faq.name,
					"category": faq.get("category", "General"),
					"type": "FAQ"
				}
			)
			synced_count += 1

		frappe.logger().info(f"Synced {synced_count} FAQs to knowledge base")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "FAQ Sync Error")


def sync_faq_from_web_pages():
	"""
	Extract FAQ content from Web Pages.

	Some sites store FAQs in Web Pages with specific routes like /faq, /faqs, /help
	"""
	try:
		# Look for FAQ-related web pages
		faq_routes = ["/faq", "/faqs", "/help", "/support", "/frequently-asked-questions"]

		web_pages = frappe.get_all(
			"Web Page",
			filters={
				"published": 1,
				"route": ["in", faq_routes]
			},
			fields=["name", "title", "main_section", "route"]
		)

		if not web_pages:
			frappe.logger().info("No FAQ web pages found")
			return

		synced_count = 0
		for page in web_pages:
			content = page.main_section or ""
			clean_content = frappe.utils.strip_html_tags(content)

			if not clean_content.strip():
				continue

			doc_content = f"""FAQ Page: {page.title}
URL: {page.route}
Content: {clean_content}
"""

			insert_document(
				content=doc_content,
				title=f"FAQ - {page.title}",
				source="Web Page",
				metadata={
					"doctype": "Web Page",
					"name": page.name,
					"route": page.route,
					"type": "FAQ"
				}
			)
			synced_count += 1

		frappe.logger().info(f"Synced {synced_count} FAQ web pages to knowledge base")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Web Page FAQ Sync Error")


def sync_company_info():
	"""
	Sync company information to knowledge base.

	Includes:
	- Company details (address, contact)
	- About Us content
	- Contact information
	- Business hours
	"""
	try:
		# Get default company
		default_company = frappe.db.get_single_value("Global Defaults", "default_company")

		if default_company:
			company = frappe.get_doc("Company", default_company)

			content = f"""Company Information:
Company Name: {company.company_name}
Country: {company.country or 'Not specified'}
Default Currency: {company.default_currency or 'Not specified'}
Domain: {getattr(company, 'domain', 'Not specified') or 'Not specified'}
Website: {getattr(company, 'website', 'Not specified') or 'Not specified'}
Phone: {getattr(company, 'phone_no', 'Not specified') or 'Not specified'}
Email: {getattr(company, 'email', 'Not specified') or 'Not specified'}
"""

			insert_document(
				content=content,
				title=f"About {company.company_name}",
				source="Company",
				metadata={
					"doctype": "Company",
					"name": company.name,
					"type": "Company Info"
				}
			)

		# Sync About Us page if exists
		if frappe.db.exists("DocType", "About Us Settings"):
			about_us = frappe.get_single("About Us Settings")

			if about_us.company_introduction:
				clean_intro = frappe.utils.strip_html_tags(about_us.company_introduction)

				content = f"""About Us:
{clean_intro}
"""

				insert_document(
					content=content,
					title="About Us",
					source="About Us Settings",
					metadata={
						"doctype": "About Us Settings",
						"type": "Company Info"
					}
				)

		# Sync Contact Us settings if exists
		if frappe.db.exists("DocType", "Contact Us Settings"):
			contact_us = frappe.get_single("Contact Us Settings")

			content_parts = ["Contact Information:"]

			if contact_us.address_title:
				content_parts.append(f"Address: {contact_us.address_title}")
			if contact_us.address_line1:
				content_parts.append(f"{contact_us.address_line1}")
			if contact_us.address_line2:
				content_parts.append(f"{contact_us.address_line2}")
			if contact_us.city:
				content_parts.append(f"City: {contact_us.city}")
			if contact_us.state:
				content_parts.append(f"State: {contact_us.state}")
			if contact_us.country:
				content_parts.append(f"Country: {contact_us.country}")
			if contact_us.pincode:
				content_parts.append(f"Pincode: {contact_us.pincode}")
			if contact_us.email_id:
				content_parts.append(f"Email: {contact_us.email_id}")
			if contact_us.phone:
				content_parts.append(f"Phone: {contact_us.phone}")

			if len(content_parts) > 1:
				insert_document(
					content="\n".join(content_parts),
					title="Contact Us",
					source="Contact Us Settings",
					metadata={
						"doctype": "Contact Us Settings",
						"type": "Company Info"
					}
				)

		frappe.logger().info("Synced company information to knowledge base")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Company Info Sync Error")


@frappe.whitelist()
def manual_sync_knowledge_base():
	"""
	Manually trigger knowledge base sync.

	Can be called from Settings page or API.
	"""
	frappe.enqueue(
		"ai_comms_hub.api.rag.sync_erpnext_knowledge",
		queue="long",
		timeout=600
	)

	return {"status": "started", "message": "Knowledge base sync started in background"}


@frappe.whitelist()
def add_custom_knowledge(title, content, category="General"):
	"""
	Add custom knowledge to the knowledge base.

	Args:
		title (str): Document title
		content (str): Document content
		category (str): Category for organization

	Returns:
		dict: Result with document ID
	"""
	result = insert_document(
		content=content,
		title=title,
		source="Custom Knowledge",
		metadata={
			"category": category,
			"added_by": frappe.session.user,
			"type": "Custom"
		}
	)

	return result


@frappe.whitelist()
def search_knowledge(query, limit=5):
	"""
	API endpoint to search the knowledge base.

	Args:
		query (str): Search query
		limit (int): Maximum results to return

	Returns:
		list: Matching documents
	"""
	return query_knowledge_base(query, top_k=int(limit))
