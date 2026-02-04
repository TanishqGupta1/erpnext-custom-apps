import frappe
from frappe import _
from frappe.model.document import Document


class LanguageSettings(Document):
	def validate(self):
		self.validate_supported_languages()
		self.validate_api_keys()

	def validate_supported_languages(self):
		"""Ensure there's at least one default language."""
		if not self.supported_languages:
			return

		defaults = [l for l in self.supported_languages if l.is_default]
		if len(defaults) > 1:
			frappe.throw(_("Only one language can be set as default"))
		elif len(defaults) == 0 and self.supported_languages:
			self.supported_languages[0].is_default = 1

	def validate_api_keys(self):
		"""Validate that required API keys are set."""
		if self.enable_auto_translation:
			if self.translation_provider == "OpenAI" and not self.openai_api_key:
				frappe.msgprint(_("OpenAI API key is required for translation"))
			elif self.translation_provider == "Anthropic" and not self.anthropic_api_key:
				frappe.msgprint(_("Anthropic API key is required for translation"))
			elif self.translation_provider == "Google Translate" and not self.google_translate_api_key:
				frappe.msgprint(_("Google Translate API key is required for translation"))
			elif self.translation_provider == "DeepL" and not self.deepl_api_key:
				frappe.msgprint(_("DeepL API key is required for translation"))

	def get_supported_language_codes(self):
		"""Get list of enabled language codes."""
		return [
			l.language_code
			for l in self.supported_languages
			if l.is_enabled
		]

	def get_default_language(self):
		"""Get the default language code."""
		for l in self.supported_languages:
			if l.is_default:
				return l.language_code
		return self.default_language or "en"

	def is_language_supported(self, language_code):
		"""Check if a language is supported."""
		supported = self.get_supported_language_codes()
		return language_code.lower() in [l.lower() for l in supported]


@frappe.whitelist()
def get_language_settings():
	"""Get language settings for the current site."""
	settings = frappe.get_single("Language Settings")
	return {
		"enable_auto_detection": settings.enable_auto_detection,
		"enable_auto_translation": settings.enable_auto_translation,
		"default_language": settings.default_language,
		"fallback_language": settings.fallback_language,
		"respond_in_detected_language": settings.respond_in_detected_language,
		"translation_provider": settings.translation_provider,
		"supported_languages": [
			{
				"code": l.language_code,
				"name": l.language_name,
				"native_name": l.native_name,
				"is_default": l.is_default
			}
			for l in settings.supported_languages
			if l.is_enabled
		]
	}


@frappe.whitelist()
def get_available_languages():
	"""Get list of commonly used languages."""
	return [
		{"code": "en", "name": "English", "native_name": "English"},
		{"code": "es", "name": "Spanish", "native_name": "Espanol"},
		{"code": "fr", "name": "French", "native_name": "Francais"},
		{"code": "de", "name": "German", "native_name": "Deutsch"},
		{"code": "it", "name": "Italian", "native_name": "Italiano"},
		{"code": "pt", "name": "Portuguese", "native_name": "Portugues"},
		{"code": "zh", "name": "Chinese (Simplified)", "native_name": "简体中文"},
		{"code": "zh-TW", "name": "Chinese (Traditional)", "native_name": "繁體中文"},
		{"code": "ja", "name": "Japanese", "native_name": "日本語"},
		{"code": "ko", "name": "Korean", "native_name": "한국어"},
		{"code": "ar", "name": "Arabic", "native_name": "العربية"},
		{"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
		{"code": "ru", "name": "Russian", "native_name": "Русский"},
		{"code": "nl", "name": "Dutch", "native_name": "Nederlands"},
		{"code": "pl", "name": "Polish", "native_name": "Polski"},
		{"code": "tr", "name": "Turkish", "native_name": "Turkce"},
		{"code": "vi", "name": "Vietnamese", "native_name": "Tieng Viet"},
		{"code": "th", "name": "Thai", "native_name": "ภาษาไทย"},
		{"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia"},
		{"code": "ms", "name": "Malay", "native_name": "Bahasa Melayu"},
		{"code": "he", "name": "Hebrew", "native_name": "עברית"},
		{"code": "sv", "name": "Swedish", "native_name": "Svenska"},
		{"code": "da", "name": "Danish", "native_name": "Dansk"},
		{"code": "no", "name": "Norwegian", "native_name": "Norsk"},
		{"code": "fi", "name": "Finnish", "native_name": "Suomi"},
		{"code": "cs", "name": "Czech", "native_name": "Cestina"},
		{"code": "el", "name": "Greek", "native_name": "Ελληνικά"},
		{"code": "hu", "name": "Hungarian", "native_name": "Magyar"},
		{"code": "ro", "name": "Romanian", "native_name": "Romana"},
		{"code": "uk", "name": "Ukrainian", "native_name": "Українська"}
	]
