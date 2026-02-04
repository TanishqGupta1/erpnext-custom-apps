"""
Sentiment Analysis and Intent Classification Service

This module provides sentiment analysis and intent classification
for customer messages using LLM-based analysis.
"""

import frappe
from frappe import _
import json
import re


# Sentiment keywords for rule-based fallback
SENTIMENT_KEYWORDS = {
    "positive": [
        "thank", "thanks", "great", "excellent", "amazing", "wonderful", "perfect",
        "love", "appreciate", "helpful", "awesome", "fantastic", "good", "happy",
        "pleased", "satisfied", "brilliant", "superb", "best", "well done"
    ],
    "negative": [
        "bad", "terrible", "awful", "horrible", "worst", "hate", "angry", "upset",
        "disappointed", "frustrated", "annoying", "poor", "useless", "pathetic",
        "ridiculous", "unacceptable", "disgusting", "furious", "complaint", "refund"
    ],
    "urgent": [
        "urgent", "asap", "immediately", "emergency", "critical", "now", "help",
        "desperate", "serious", "important"
    ]
}

# Intent patterns for classification
INTENT_PATTERNS = {
    "order_status": [
        r"where.*(order|package|delivery|shipment)",
        r"track.*(order|package|shipment)",
        r"(order|delivery|shipping).*(status|update)",
        r"when.*(arrive|deliver|ship|receive)",
        r"order.*number"
    ],
    "refund_request": [
        r"(want|need|request).*(refund|money back)",
        r"cancel.*(order|subscription)",
        r"return.*(product|item|order)",
        r"get.*money.*back",
        r"chargeback"
    ],
    "technical_support": [
        r"(not|isn't|doesn't|won't).*(work|load|open|start)",
        r"error|bug|issue|problem|broken",
        r"how.*(do|can|to).*(use|setup|configure|install)",
        r"help.*(with|me)",
        r"(can't|cannot|unable).*(access|login|connect)"
    ],
    "billing_inquiry": [
        r"(charge|bill|invoice|payment|price|cost)",
        r"(overcharged|double.*charge|wrong.*amount)",
        r"(payment|card).*(declined|failed|issue)",
        r"subscription.*(cost|price|charge)"
    ],
    "product_inquiry": [
        r"(do you have|is there|available)",
        r"(price|cost|how much).*of",
        r"(product|item).*(info|information|details|specs)",
        r"(compare|difference|between)",
        r"stock|inventory|availability"
    ],
    "complaint": [
        r"(file|make|submit).*(complaint|grievance)",
        r"(speak|talk).*(manager|supervisor)",
        r"(worst|terrible|horrible).*experience",
        r"(never|will not).*again",
        r"(report|escalate)"
    ],
    "greeting": [
        r"^(hi|hello|hey|good morning|good afternoon|good evening)",
        r"^(howdy|greetings)"
    ],
    "thanks": [
        r"^(thank|thanks|thx)",
        r"(appreciate|grateful)"
    ],
    "goodbye": [
        r"(bye|goodbye|see you|take care)",
        r"(have a good|have a nice)"
    ]
}


def analyze_sentiment(text):
    """
    Analyze sentiment of text.
    Returns: dict with sentiment, confidence, and details
    """
    if not text:
        return {"sentiment": "Neutral", "confidence": 0.0, "scores": {}}

    text_lower = text.lower()

    # Count keyword matches
    positive_count = sum(1 for word in SENTIMENT_KEYWORDS["positive"] if word in text_lower)
    negative_count = sum(1 for word in SENTIMENT_KEYWORDS["negative"] if word in text_lower)
    urgent_count = sum(1 for word in SENTIMENT_KEYWORDS["urgent"] if word in text_lower)

    # Calculate scores
    total_matches = positive_count + negative_count + 1  # +1 to avoid division by zero
    positive_score = positive_count / total_matches
    negative_score = negative_count / total_matches

    # Determine sentiment
    if negative_count > positive_count and negative_count >= 2:
        sentiment = "Negative"
        confidence = min(0.5 + (negative_score * 0.5), 0.95)
    elif positive_count > negative_count and positive_count >= 2:
        sentiment = "Positive"
        confidence = min(0.5 + (positive_score * 0.5), 0.95)
    elif negative_count > 0:
        sentiment = "Negative"
        confidence = 0.4 + (negative_score * 0.3)
    elif positive_count > 0:
        sentiment = "Positive"
        confidence = 0.4 + (positive_score * 0.3)
    else:
        sentiment = "Neutral"
        confidence = 0.6

    # Adjust for urgency
    is_urgent = urgent_count > 0

    return {
        "sentiment": sentiment,
        "confidence": round(confidence, 2),
        "is_urgent": is_urgent,
        "scores": {
            "positive": positive_count,
            "negative": negative_count,
            "urgent": urgent_count
        }
    }


def classify_intent(text):
    """
    Classify the intent of a message.
    Returns: dict with intent, confidence, and matched patterns
    """
    if not text:
        return {"intent": "general_inquiry", "confidence": 0.0, "matches": []}

    text_lower = text.lower()
    matched_intents = {}

    # Check each intent pattern
    for intent, patterns in INTENT_PATTERNS.items():
        matches = []
        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches.append(pattern)

        if matches:
            matched_intents[intent] = len(matches)

    # Determine primary intent
    if matched_intents:
        primary_intent = max(matched_intents, key=matched_intents.get)
        match_count = matched_intents[primary_intent]
        confidence = min(0.5 + (match_count * 0.15), 0.95)

        return {
            "intent": primary_intent,
            "confidence": round(confidence, 2),
            "all_intents": matched_intents,
            "matches": list(matched_intents.keys())
        }

    return {
        "intent": "general_inquiry",
        "confidence": 0.3,
        "all_intents": {},
        "matches": []
    }


def analyze_message(text):
    """
    Perform full analysis on a message: sentiment + intent.
    """
    sentiment_result = analyze_sentiment(text)
    intent_result = classify_intent(text)

    return {
        "sentiment": sentiment_result,
        "intent": intent_result,
        "requires_escalation": should_escalate(sentiment_result, intent_result)
    }


def should_escalate(sentiment_result, intent_result):
    """
    Determine if message should be escalated based on analysis.
    """
    # Escalate on negative sentiment with high confidence
    if sentiment_result["sentiment"] == "Negative" and sentiment_result["confidence"] > 0.6:
        return True

    # Escalate on urgent messages
    if sentiment_result.get("is_urgent"):
        return True

    # Escalate on certain intents
    escalation_intents = ["refund_request", "complaint"]
    if intent_result["intent"] in escalation_intents:
        return True

    return False


@frappe.whitelist()
def analyze_conversation_message(message_text):
    """API endpoint to analyze a message"""
    result = analyze_message(message_text)
    return result


@frappe.whitelist()
def get_sentiment(text):
    """API endpoint to get sentiment only"""
    return analyze_sentiment(text)


@frappe.whitelist()
def get_intent(text):
    """API endpoint to get intent only"""
    return classify_intent(text)


def update_conversation_analysis(conversation_name):
    """
    Update a conversation's sentiment and intent based on recent messages.
    """
    # Get recent customer messages
    messages = frappe.get_all(
        "Communication Message",
        filters={
            "parent_hub": conversation_name,
            "sender_type": "Customer"
        },
        fields=["content"],
        order_by="creation desc",
        limit=5
    )

    if not messages:
        return

    # Combine messages for analysis
    combined_text = " ".join([m.content for m in messages if m.content])

    # Analyze
    result = analyze_message(combined_text)

    # Update conversation
    frappe.db.set_value(
        "Communication Hub",
        conversation_name,
        {
            "sentiment": result["sentiment"]["sentiment"],
            "intent": result["intent"]["intent"]
        },
        update_modified=False
    )

    return result
