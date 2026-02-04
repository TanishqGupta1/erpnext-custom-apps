import frappe
from frappe import _
import json
import re


@frappe.whitelist()
def detect_language(text, use_ai=True):
	"""
	Detect the language of the given text.

	Args:
		text: Text to analyze
		use_ai: Whether to use AI for detection (more accurate)

	Returns:
		Dictionary with language code, name, and confidence
	"""
	if not text or len(text.strip()) < 3:
		return {
			"language_code": "en",
			"language_name": "English",
			"confidence": 0.0,
			"method": "default"
		}

	settings = frappe.get_single("Language Settings")

	if use_ai and settings.use_ai_detection:
		return detect_language_ai(text, settings)
	else:
		return detect_language_basic(text)


def detect_language_ai(text, settings):
	"""Use AI model for language detection."""
	try:
		from openai import OpenAI

		# Get API key from settings or AI Comms Hub Settings
		api_key = settings.openai_api_key
		if not api_key:
			hub_settings = frappe.get_single("AI Comms Hub Settings")
			api_key = hub_settings.openai_api_key

		if not api_key:
			return detect_language_basic(text)

		client = OpenAI(api_key=api_key)

		# Get supported languages for context
		supported = [l.language_code for l in settings.supported_languages if l.is_enabled]
		supported_str = ", ".join(supported) if supported else "any language"

		response = client.chat.completions.create(
			model=settings.detection_model or "gpt-4o-mini",
			messages=[
				{
					"role": "system",
					"content": f"""You are a language detection expert. Analyze the text and identify its language.
Respond with JSON only: {{"language_code": "xx", "language_name": "Name", "confidence": 0.95}}
Supported languages: {supported_str}
Use ISO 639-1 language codes."""
				},
				{
					"role": "user",
					"content": f"Detect the language of this text:\n\n{text[:1000]}"
				}
			],
			temperature=0,
			max_tokens=100
		)

		result_text = response.choices[0].message.content.strip()

		# Parse JSON from response
		json_match = re.search(r'\{[^}]+\}', result_text)
		if json_match:
			result = json.loads(json_match.group())
			result["method"] = "ai"
			return result

	except Exception as e:
		frappe.log_error(f"AI language detection error: {str(e)}")

	return detect_language_basic(text)


def detect_language_basic(text):
	"""Basic language detection using character patterns."""
	text = text.lower().strip()

	# Character set patterns for common languages
	patterns = {
		"zh": r'[\u4e00-\u9fff]',  # Chinese
		"ja": r'[\u3040-\u309f\u30a0-\u30ff]',  # Japanese hiragana/katakana
		"ko": r'[\uac00-\ud7af\u1100-\u11ff]',  # Korean
		"ar": r'[\u0600-\u06ff]',  # Arabic
		"he": r'[\u0590-\u05ff]',  # Hebrew
		"th": r'[\u0e00-\u0e7f]',  # Thai
		"hi": r'[\u0900-\u097f]',  # Hindi/Devanagari
		"ru": r'[\u0400-\u04ff]',  # Russian/Cyrillic
		"el": r'[\u0370-\u03ff]',  # Greek
	}

	for lang_code, pattern in patterns.items():
		if re.search(pattern, text):
			lang_names = {
				"zh": "Chinese",
				"ja": "Japanese",
				"ko": "Korean",
				"ar": "Arabic",
				"he": "Hebrew",
				"th": "Thai",
				"hi": "Hindi",
				"ru": "Russian",
				"el": "Greek"
			}
			return {
				"language_code": lang_code,
				"language_name": lang_names.get(lang_code, "Unknown"),
				"confidence": 0.85,
				"method": "pattern"
			}

	# Common word patterns for European languages
	spanish_words = ["el", "la", "de", "que", "en", "es", "por", "con", "para", "como"]
	french_words = ["le", "la", "de", "et", "est", "en", "que", "pour", "avec", "dans"]
	german_words = ["der", "die", "das", "und", "ist", "von", "mit", "auf", "fur", "ein"]
	portuguese_words = ["o", "a", "de", "que", "em", "para", "com", "nao", "uma", "os"]
	italian_words = ["il", "la", "di", "che", "e", "per", "con", "non", "sono", "una"]

	words = text.split()
	word_set = set(words)

	lang_scores = {
		"es": len(word_set.intersection(spanish_words)),
		"fr": len(word_set.intersection(french_words)),
		"de": len(word_set.intersection(german_words)),
		"pt": len(word_set.intersection(portuguese_words)),
		"it": len(word_set.intersection(italian_words)),
	}

	max_score = max(lang_scores.values())
	if max_score >= 2:
		best_lang = max(lang_scores, key=lang_scores.get)
		lang_names = {
			"es": "Spanish",
			"fr": "French",
			"de": "German",
			"pt": "Portuguese",
			"it": "Italian"
		}
		return {
			"language_code": best_lang,
			"language_name": lang_names[best_lang],
			"confidence": min(0.7, 0.3 + (max_score * 0.1)),
			"method": "word_pattern"
		}

	# Default to English
	return {
		"language_code": "en",
		"language_name": "English",
		"confidence": 0.5,
		"method": "default"
	}


@frappe.whitelist()
def translate_text(text, target_language, source_language=None):
	"""
	Translate text to target language.

	Args:
		text: Text to translate
		target_language: Target language code (ISO 639-1)
		source_language: Source language code (optional, auto-detected if not provided)

	Returns:
		Dictionary with translated text and metadata
	"""
	if not text:
		return {"translated_text": "", "source_language": source_language, "target_language": target_language}

	settings = frappe.get_single("Language Settings")

	if not settings.enable_auto_translation:
		return {
			"translated_text": text,
			"source_language": source_language,
			"target_language": target_language,
			"translated": False,
			"reason": "Translation disabled"
		}

	# Auto-detect source language if not provided
	if not source_language:
		detection = detect_language(text)
		source_language = detection.get("language_code", "en")

	# Skip if same language
	if source_language == target_language:
		return {
			"translated_text": text,
			"source_language": source_language,
			"target_language": target_language,
			"translated": False,
			"reason": "Same language"
		}

	# Choose translation provider
	provider = settings.translation_provider
	if provider == "OpenAI":
		return translate_openai(text, source_language, target_language, settings)
	elif provider == "Anthropic":
		return translate_anthropic(text, source_language, target_language, settings)
	elif provider == "Google Translate":
		return translate_google(text, source_language, target_language, settings)
	elif provider == "DeepL":
		return translate_deepl(text, source_language, target_language, settings)
	else:
		return translate_openai(text, source_language, target_language, settings)


def translate_openai(text, source_language, target_language, settings):
	"""Translate using OpenAI."""
	try:
		from openai import OpenAI

		api_key = settings.openai_api_key
		if not api_key:
			hub_settings = frappe.get_single("AI Comms Hub Settings")
			api_key = hub_settings.openai_api_key

		if not api_key:
			return {
				"translated_text": text,
				"error": "OpenAI API key not configured",
				"translated": False
			}

		client = OpenAI(api_key=api_key)

		# Get language names for better prompting
		lang_names = get_language_names()
		source_name = lang_names.get(source_language, source_language)
		target_name = lang_names.get(target_language, target_language)

		response = client.chat.completions.create(
			model=settings.openai_model or "gpt-4o-mini",
			messages=[
				{
					"role": "system",
					"content": f"""You are a professional translator. Translate the following text from {source_name} to {target_name}.
Maintain the original tone, formatting, and meaning.
Only output the translated text, nothing else."""
				},
				{
					"role": "user",
					"content": text
				}
			],
			temperature=0.3,
			max_tokens=len(text) * 3  # Allow for expansion
		)

		translated_text = response.choices[0].message.content.strip()

		return {
			"translated_text": translated_text,
			"source_language": source_language,
			"target_language": target_language,
			"translated": True,
			"provider": "OpenAI"
		}

	except Exception as e:
		frappe.log_error(f"OpenAI translation error: {str(e)}")
		return {
			"translated_text": text,
			"error": str(e),
			"translated": False
		}


def translate_anthropic(text, source_language, target_language, settings):
	"""Translate using Anthropic Claude."""
	try:
		import anthropic

		api_key = settings.anthropic_api_key
		if not api_key:
			hub_settings = frappe.get_single("AI Comms Hub Settings")
			api_key = hub_settings.anthropic_api_key

		if not api_key:
			return {
				"translated_text": text,
				"error": "Anthropic API key not configured",
				"translated": False
			}

		client = anthropic.Anthropic(api_key=api_key)

		lang_names = get_language_names()
		source_name = lang_names.get(source_language, source_language)
		target_name = lang_names.get(target_language, target_language)

		response = client.messages.create(
			model=settings.anthropic_model or "claude-3-haiku-20240307",
			max_tokens=len(text) * 3,
			messages=[
				{
					"role": "user",
					"content": f"""Translate the following text from {source_name} to {target_name}.
Maintain the original tone, formatting, and meaning.
Only output the translated text, nothing else.

Text to translate:
{text}"""
				}
			]
		)

		translated_text = response.content[0].text.strip()

		return {
			"translated_text": translated_text,
			"source_language": source_language,
			"target_language": target_language,
			"translated": True,
			"provider": "Anthropic"
		}

	except Exception as e:
		frappe.log_error(f"Anthropic translation error: {str(e)}")
		return {
			"translated_text": text,
			"error": str(e),
			"translated": False
		}


def translate_google(text, source_language, target_language, settings):
	"""Translate using Google Cloud Translation API."""
	try:
		import requests

		api_key = settings.google_translate_api_key
		if not api_key:
			return {
				"translated_text": text,
				"error": "Google Translate API key not configured",
				"translated": False
			}

		url = "https://translation.googleapis.com/language/translate/v2"
		params = {
			"key": api_key,
			"q": text,
			"source": source_language,
			"target": target_language,
			"format": "text"
		}

		response = requests.post(url, data=params)
		result = response.json()

		if "data" in result and "translations" in result["data"]:
			translated_text = result["data"]["translations"][0]["translatedText"]
			return {
				"translated_text": translated_text,
				"source_language": source_language,
				"target_language": target_language,
				"translated": True,
				"provider": "Google Translate"
			}
		else:
			return {
				"translated_text": text,
				"error": result.get("error", {}).get("message", "Unknown error"),
				"translated": False
			}

	except Exception as e:
		frappe.log_error(f"Google Translate error: {str(e)}")
		return {
			"translated_text": text,
			"error": str(e),
			"translated": False
		}


def translate_deepl(text, source_language, target_language, settings):
	"""Translate using DeepL API."""
	try:
		import requests

		api_key = settings.deepl_api_key
		if not api_key:
			return {
				"translated_text": text,
				"error": "DeepL API key not configured",
				"translated": False
			}

		# DeepL uses uppercase language codes and specific variants
		deepl_target = target_language.upper()
		if deepl_target == "EN":
			deepl_target = "EN-US"
		elif deepl_target == "PT":
			deepl_target = "PT-BR"

		url = "https://api-free.deepl.com/v2/translate"
		headers = {
			"Authorization": f"DeepL-Auth-Key {api_key}",
			"Content-Type": "application/x-www-form-urlencoded"
		}
		data = {
			"text": text,
			"source_lang": source_language.upper(),
			"target_lang": deepl_target
		}

		response = requests.post(url, headers=headers, data=data)
		result = response.json()

		if "translations" in result:
			translated_text = result["translations"][0]["text"]
			return {
				"translated_text": translated_text,
				"source_language": source_language,
				"target_language": target_language,
				"translated": True,
				"provider": "DeepL"
			}
		else:
			return {
				"translated_text": text,
				"error": result.get("message", "Unknown error"),
				"translated": False
			}

	except Exception as e:
		frappe.log_error(f"DeepL translation error: {str(e)}")
		return {
			"translated_text": text,
			"error": str(e),
			"translated": False
		}


def get_language_names():
	"""Get mapping of language codes to names."""
	return {
		"en": "English",
		"es": "Spanish",
		"fr": "French",
		"de": "German",
		"it": "Italian",
		"pt": "Portuguese",
		"zh": "Chinese",
		"ja": "Japanese",
		"ko": "Korean",
		"ar": "Arabic",
		"hi": "Hindi",
		"ru": "Russian",
		"nl": "Dutch",
		"pl": "Polish",
		"tr": "Turkish",
		"vi": "Vietnamese",
		"th": "Thai",
		"id": "Indonesian",
		"ms": "Malay",
		"he": "Hebrew",
		"sv": "Swedish",
		"da": "Danish",
		"no": "Norwegian",
		"fi": "Finnish",
		"cs": "Czech",
		"el": "Greek",
		"hu": "Hungarian",
		"ro": "Romanian",
		"uk": "Ukrainian"
	}


@frappe.whitelist()
def update_conversation_language(hub_id, language_code=None, auto_detect=True):
	"""
	Update the language settings for a conversation.

	Args:
		hub_id: Communication Hub ID
		language_code: Language code to set (optional)
		auto_detect: Whether to auto-detect from messages

	Returns:
		Updated language information
	"""
	hub_doc = frappe.get_doc("Communication Hub", hub_id)

	if auto_detect and not language_code:
		# Get recent messages for detection
		messages = frappe.get_all(
			"Communication Message",
			filters={
				"communication_hub": hub_id,
				"sender_type": "Customer"
			},
			fields=["content"],
			order_by="creation desc",
			limit=5
		)

		if messages:
			combined_text = " ".join([m.content for m in messages if m.content])
			if combined_text:
				detection = detect_language(combined_text)
				language_code = detection.get("language_code")
				hub_doc.detected_language = language_code
				hub_doc.detection_confidence = detection.get("confidence", 0)

	if language_code:
		hub_doc.preferred_language = language_code

	hub_doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"hub_id": hub_id,
		"detected_language": hub_doc.detected_language,
		"preferred_language": hub_doc.preferred_language,
		"detection_confidence": hub_doc.detection_confidence
	}


@frappe.whitelist()
def translate_response(response_text, hub_id):
	"""
	Translate an AI response based on conversation language settings.

	Args:
		response_text: The response text to translate
		hub_id: Communication Hub ID

	Returns:
		Translated response text
	"""
	hub_doc = frappe.get_doc("Communication Hub", hub_id)

	if not hub_doc.auto_translate:
		return response_text

	# Determine target language
	target_language = hub_doc.preferred_language or hub_doc.detected_language

	if not target_language:
		return response_text

	settings = frappe.get_single("Language Settings")
	source_language = settings.default_language or "en"

	# Skip if same language
	if target_language == source_language:
		return response_text

	# Translate
	result = translate_text(response_text, target_language, source_language)

	if result.get("translated"):
		translated = result["translated_text"]

		# Add translation note if configured
		if settings.include_translation_note and settings.translation_note_template:
			note = settings.translation_note_template
			lang_names = get_language_names()
			note = note.replace("{source_lang}", lang_names.get(source_language, source_language))
			note = note.replace("{target_lang}", lang_names.get(target_language, target_language))
			translated = f"{translated}\n\n_{note}_"

		return translated

	return response_text


@frappe.whitelist()
def get_language_stats():
	"""Get statistics about language usage in conversations."""
	# Language distribution
	language_dist = frappe.db.sql("""
		SELECT
			COALESCE(detected_language, 'Unknown') as language,
			COUNT(*) as count
		FROM `tabCommunication Hub`
		WHERE detected_language IS NOT NULL AND detected_language != ''
		GROUP BY detected_language
		ORDER BY count DESC
	""", as_dict=True)

	# Translation usage
	translation_count = frappe.db.count(
		"Communication Hub",
		{"auto_translate": 1}
	)

	total_with_language = frappe.db.count(
		"Communication Hub",
		{"detected_language": ["!=", ""]}
	)

	return {
		"language_distribution": language_dist,
		"translation_enabled_count": translation_count,
		"total_with_language_detected": total_with_language,
		"detection_rate": round(total_with_language / max(frappe.db.count("Communication Hub"), 1) * 100, 1)
	}
