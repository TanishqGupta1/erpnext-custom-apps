import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, get_time, nowtime
from datetime import datetime
import re


class EscalationRule(Document):
	def validate(self):
		self.validate_priority()
		self.validate_keywords()

	def validate_priority(self):
		"""Ensure priority is within valid range."""
		if self.priority < 1:
			self.priority = 1
		elif self.priority > 10:
			self.priority = 10

	def validate_keywords(self):
		"""Clean up keyword fields."""
		if self.trigger_keywords:
			self.trigger_keywords = self.clean_keywords(self.trigger_keywords)
		if self.exclude_keywords:
			self.exclude_keywords = self.clean_keywords(self.exclude_keywords)
		if self.intent_trigger:
			self.intent_trigger = self.clean_keywords(self.intent_trigger)

	def clean_keywords(self, keywords):
		"""Clean and normalize keywords."""
		if not keywords:
			return ""
		words = [w.strip().lower() for w in keywords.split(",") if w.strip()]
		return ", ".join(words)

	def is_active(self):
		"""Check if rule is currently active based on schedule."""
		if not self.is_enabled:
			return False

		if not self.schedule_enabled:
			return True

		now = datetime.now()

		# Check day
		if self.active_days:
			active_days = [d.strip() for d in self.active_days.split(",")]
			current_day = now.strftime("%A")
			if current_day not in active_days:
				return False

		# Check time
		if self.active_hours_start and self.active_hours_end:
			current_time = now.time()
			start_time = get_time(self.active_hours_start)
			end_time = get_time(self.active_hours_end)

			if start_time <= end_time:
				if not (start_time <= current_time <= end_time):
					return False
			else:  # Overnight schedule
				if not (current_time >= start_time or current_time <= end_time):
					return False

		return True

	def evaluate(self, hub_doc, message_content=None):
		"""
		Evaluate if this rule should trigger for a conversation.

		Args:
			hub_doc: Communication Hub document
			message_content: Latest message content (optional)

		Returns:
			Tuple (should_escalate, reason)
		"""
		if not self.is_active():
			return False, None

		# Check channel filter
		if not self.matches_channel(hub_doc.channel):
			return False, None

		# Check customer filter
		if not self.matches_customer(hub_doc):
			return False, None

		# Evaluate conditions based on type
		conditions_met = []
		reasons = []

		if self.condition_type in ["Keyword", "Combined"]:
			matched, reason = self.check_keywords(message_content or "", hub_doc)
			if matched:
				conditions_met.append(True)
				reasons.append(reason)
			elif self.match_all_conditions:
				return False, None

		if self.condition_type in ["Sentiment", "Combined"]:
			matched, reason = self.check_sentiment(hub_doc)
			if matched:
				conditions_met.append(True)
				reasons.append(reason)
			elif self.match_all_conditions:
				return False, None

		if self.condition_type in ["Intent", "Combined"]:
			matched, reason = self.check_intent(hub_doc)
			if matched:
				conditions_met.append(True)
				reasons.append(reason)
			elif self.match_all_conditions:
				return False, None

		if self.condition_type in ["Message Count", "Combined"]:
			matched, reason = self.check_message_count(hub_doc)
			if matched:
				conditions_met.append(True)
				reasons.append(reason)
			elif self.match_all_conditions:
				return False, None

		if self.condition_type in ["Response Time", "Combined"]:
			matched, reason = self.check_response_time(hub_doc)
			if matched:
				conditions_met.append(True)
				reasons.append(reason)
			elif self.match_all_conditions:
				return False, None

		# Determine if we should escalate
		if self.match_all_conditions:
			should_escalate = len(conditions_met) > 0 and all(conditions_met)
		else:
			should_escalate = any(conditions_met)

		if should_escalate:
			combined_reason = f"Rule '{self.rule_name}': " + "; ".join(reasons)
			return True, combined_reason

		return False, None

	def matches_channel(self, channel):
		"""Check if rule applies to this channel."""
		if self.channel_filter == "All":
			return True

		if self.specific_channels:
			channels = [c.strip().lower() for c in self.specific_channels.split(",")]
			return channel.lower() in channels

		return True

	def matches_customer(self, hub_doc):
		"""Check if rule applies to this customer type."""
		if self.customer_type_filter == "All" and not self.vip_customers_only:
			return True

		# TODO: Implement customer type and VIP checking
		# This would require checking against Customer DocType

		return True

	def check_keywords(self, message_content, hub_doc):
		"""Check keyword conditions."""
		if not self.trigger_keywords:
			return False, None

		message_lower = message_content.lower()

		# Also check subject and context
		full_text = message_lower
		if hub_doc.subject:
			full_text += " " + hub_doc.subject.lower()
		if hub_doc.context:
			full_text += " " + hub_doc.context.lower()

		# Check exclude keywords first
		if self.exclude_keywords:
			exclude_words = [w.strip() for w in self.exclude_keywords.split(",")]
			for word in exclude_words:
				if word and word in full_text:
					return False, None

		# Check trigger keywords
		trigger_words = [w.strip() for w in self.trigger_keywords.split(",")]
		matched_keywords = []

		for word in trigger_words:
			if word and word in full_text:
				matched_keywords.append(word)

		if matched_keywords:
			return True, f"Matched keywords: {', '.join(matched_keywords)}"

		return False, None

	def check_sentiment(self, hub_doc):
		"""Check sentiment conditions."""
		if not self.sentiment_trigger or not hub_doc.sentiment:
			return False, None

		sentiment = hub_doc.sentiment.lower()

		if self.sentiment_trigger == "Negative" and sentiment == "negative":
			return True, f"Negative sentiment detected"
		elif self.sentiment_trigger == "Very Negative" and sentiment == "very negative":
			return True, f"Very negative sentiment detected"
		elif self.sentiment_trigger == "Any Negative" and "negative" in sentiment:
			return True, f"Negative sentiment detected: {sentiment}"

		return False, None

	def check_intent(self, hub_doc):
		"""Check intent conditions."""
		if not self.intent_trigger or not hub_doc.intent:
			return False, None

		trigger_intents = [i.strip().lower() for i in self.intent_trigger.split(",")]
		current_intent = hub_doc.intent.lower()

		for intent in trigger_intents:
			if intent and intent in current_intent:
				return True, f"Matched intent: {intent}"

		return False, None

	def check_message_count(self, hub_doc):
		"""Check message count conditions."""
		if not self.message_count_trigger:
			return False, None

		if hub_doc.total_messages and hub_doc.total_messages >= self.message_count_threshold:
			return True, f"Message count ({hub_doc.total_messages}) exceeds threshold ({self.message_count_threshold})"

		return False, None

	def check_response_time(self, hub_doc):
		"""Check response time conditions."""
		if not self.response_time_trigger:
			return False, None

		# TODO: Implement actual response time checking
		# This would require tracking response times in the hub

		return False, None

	def record_trigger(self):
		"""Record that this rule was triggered."""
		frappe.db.set_value(
			"Escalation Rule",
			self.name,
			{
				"times_triggered": self.times_triggered + 1,
				"last_triggered": now_datetime()
			},
			update_modified=False
		)


@frappe.whitelist()
def evaluate_escalation(hub_id, message_content=None):
	"""
	Evaluate all escalation rules for a conversation.

	Args:
		hub_id: Communication Hub ID
		message_content: Latest message content

	Returns:
		Dictionary with escalation result
	"""
	hub_doc = frappe.get_doc("Communication Hub", hub_id)

	# Get all enabled rules ordered by priority
	rules = frappe.get_all(
		"Escalation Rule",
		filters={"is_enabled": 1},
		fields=["name"],
		order_by="priority desc"
	)

	for rule_data in rules:
		rule = frappe.get_doc("Escalation Rule", rule_data.name)
		should_escalate, reason = rule.evaluate(hub_doc, message_content)

		if should_escalate:
			# Apply escalation
			result = apply_escalation(hub_doc, rule, reason)
			rule.record_trigger()
			return result

	return {"escalated": False, "reason": None}


def apply_escalation(hub_doc, rule, reason):
	"""
	Apply escalation action to a conversation.

	Args:
		hub_doc: Communication Hub document
		rule: Escalation Rule document
		reason: Escalation reason

	Returns:
		Dictionary with escalation result
	"""
	result = {
		"escalated": True,
		"reason": reason,
		"rule": rule.rule_name,
		"action": rule.escalation_action
	}

	if rule.escalation_action == "Escalate":
		hub_doc.status = "Escalated"
		hub_doc.escalation_reason = reason
		hub_doc.escalated_at = now_datetime()
		hub_doc.escalated_by_ai = 1
		hub_doc.save(ignore_permissions=True)

	elif rule.escalation_action == "Escalate and Assign":
		hub_doc.status = "Escalated"
		hub_doc.escalation_reason = reason
		hub_doc.escalated_at = now_datetime()
		hub_doc.escalated_by_ai = 1

		if rule.assign_to_user:
			hub_doc.assigned_to = rule.assign_to_user
			result["assigned_to"] = rule.assign_to_user

		hub_doc.save(ignore_permissions=True)

		# Send notification
		if rule.notification_template:
			send_escalation_notification(hub_doc, rule, reason)

	elif rule.escalation_action == "Switch to HITL":
		hub_doc.ai_mode = "HITL"
		hub_doc.status = "Pending Review"
		hub_doc.escalation_reason = reason
		hub_doc.save(ignore_permissions=True)
		result["switched_to_hitl"] = True

	elif rule.escalation_action == "Notify Only":
		if rule.notification_template:
			send_escalation_notification(hub_doc, rule, reason)
		result["notification_sent"] = True

	# Send auto response if configured
	if rule.auto_respond and rule.auto_response_message:
		result["auto_response"] = rule.auto_response_message

	frappe.db.commit()
	return result


def send_escalation_notification(hub_doc, rule, reason):
	"""Send notification for escalation."""
	try:
		# Create system notification
		frappe.publish_realtime(
			event="escalation_alert",
			message={
				"hub_id": hub_doc.name,
				"customer": hub_doc.customer_name,
				"channel": hub_doc.channel,
				"reason": reason,
				"rule": rule.rule_name
			},
			user=rule.assign_to_user or "Administrator"
		)
	except Exception as e:
		frappe.log_error(f"Failed to send escalation notification: {str(e)}")


@frappe.whitelist()
def get_escalation_rules_stats():
	"""Get statistics for escalation rules."""
	rules = frappe.get_all(
		"Escalation Rule",
		fields=["name", "rule_name", "is_enabled", "condition_type", "times_triggered", "last_triggered"],
		order_by="times_triggered desc"
	)

	total_rules = len(rules)
	active_rules = len([r for r in rules if r.is_enabled])
	total_triggers = sum(r.times_triggered or 0 for r in rules)

	return {
		"total_rules": total_rules,
		"active_rules": active_rules,
		"total_triggers": total_triggers,
		"rules": rules
	}
