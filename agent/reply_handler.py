from __future__ import annotations

from briefs.models import ConversationState, ReplyAnalysis
from integrations.llm_client import (
    call_openrouter_json,
    is_llm_reply_analysis_enabled,
    LLMClientError,
)


_ALLOWED_REPLY_TYPES = {
    "interested",
    "information_request",
    "defer",
    "rejection",
    "unclear",
}

_ALLOWED_SENTIMENTS = {
    "positive",
    "neutral",
    "negative",
}

_ALLOWED_NEXT_ACTIONS = {
    "offer_scheduling",
    "send_followup_details",
    "set_followup_later",
    "close_thread",
    "respond_carefully",
}


def analyze_reply(reply_text: str) -> ReplyAnalysis:
    """
    Try LLM-based analysis first when enabled; fall back to rules if anything fails.
    """
    if is_llm_reply_analysis_enabled():
        try:
            return _analyze_reply_with_llm(reply_text)
        except LLMClientError:
            pass
        except ValueError:
            pass

    return _analyze_reply_rule_based(reply_text)


def _analyze_reply_with_llm(reply_text: str) -> ReplyAnalysis:
    system_prompt = """
You are classifying a sales prospect email reply for a B2B outreach workflow.

Return ONLY a JSON object with exactly these keys:
- reply_type
- confidence
- sentiment
- next_action
- reasoning

Allowed reply_type values:
- interested
- information_request
- defer
- rejection
- unclear

Allowed sentiment values:
- positive
- neutral
- negative

Allowed next_action values:
- offer_scheduling
- send_followup_details
- set_followup_later
- close_thread
- respond_carefully

Rules:
- Use "interested" only if the reply clearly indicates interest or willingness to talk.
- Use "information_request" if the reply asks for more details before deciding.
- Use "defer" if timing is the issue rather than fit.
- Use "rejection" if the reply declines or asks to stop/remove contact.
- Use "unclear" if intent is ambiguous.
- confidence must be a number between 0 and 1.
- reasoning must be brief and factual.
""".strip()

    user_prompt = f"Prospect reply:\n{reply_text}"

    data = call_openrouter_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
    )

    reply_type = str(data.get("reply_type", "")).strip()
    sentiment = str(data.get("sentiment", "")).strip()
    next_action = str(data.get("next_action", "")).strip()
    reasoning = str(data.get("reasoning", "")).strip()

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid confidence from LLM") from exc

    if reply_type not in _ALLOWED_REPLY_TYPES:
        raise ValueError(f"Invalid reply_type from LLM: {reply_type}")
    if sentiment not in _ALLOWED_SENTIMENTS:
        raise ValueError(f"Invalid sentiment from LLM: {sentiment}")
    if next_action not in _ALLOWED_NEXT_ACTIONS:
        raise ValueError(f"Invalid next_action from LLM: {next_action}")
    if not (0.0 <= confidence <= 1.0):
        raise ValueError(f"Confidence out of range: {confidence}")

    return ReplyAnalysis(
        reply_type=reply_type,
        confidence=round(confidence, 2),
        sentiment=sentiment,
        next_action=next_action,
        reasoning=reasoning or "LLM classified the reply.",
    )


def _analyze_reply_rule_based(reply_text: str) -> ReplyAnalysis:
    text = reply_text.strip().lower()

    interested_markers = [
        "interested",
        "sounds good",
        "worth a conversation",
        "let's talk",
        "lets talk",
        "can we talk",
        "book",
        "schedule",
        "next week",
        "send times",
    ]

    more_info_markers = [
        "tell me more",
        "more info",
        "send more",
        "can you share",
        "details",
        "what do you do",
    ]

    defer_markers = [
        "not now",
        "later",
        "circle back",
        "follow up later",
        "next quarter",
        "busy right now",
    ]

    reject_markers = [
        "not interested",
        "no thanks",
        "remove me",
        "stop",
        "unsubscribe",
    ]

    if any(marker in text for marker in reject_markers):
        return ReplyAnalysis(
            reply_type="rejection",
            confidence=0.95,
            sentiment="negative",
            next_action="close_thread",
            reasoning="Reply includes a clear rejection or unsubscribe-style signal.",
        )

    if any(marker in text for marker in interested_markers):
        return ReplyAnalysis(
            reply_type="interested",
            confidence=0.9,
            sentiment="positive",
            next_action="offer_scheduling",
            reasoning="Reply includes direct interest or scheduling intent.",
        )

    if any(marker in text for marker in more_info_markers):
        return ReplyAnalysis(
            reply_type="information_request",
            confidence=0.85,
            sentiment="neutral",
            next_action="send_followup_details",
            reasoning="Reply asks for more information before committing to a meeting.",
        )

    if any(marker in text for marker in defer_markers):
        return ReplyAnalysis(
            reply_type="defer",
            confidence=0.85,
            sentiment="neutral",
            next_action="set_followup_later",
            reasoning="Reply indicates timing friction rather than a clear rejection.",
        )

    return ReplyAnalysis(
        reply_type="unclear",
        confidence=0.55,
        sentiment="neutral",
        next_action="respond_carefully",
        reasoning="Reply intent is ambiguous and should be handled conservatively.",
    )


def update_conversation_state(
    state: ConversationState,
    reply_text: str,
    analysis: ReplyAnalysis,
) -> ConversationState:
    new_stage = state.stage
    is_handoff_required = state.is_handoff_required
    is_qualified = state.is_qualified
    is_booked = state.is_booked

    if analysis.reply_type == "interested":
        new_stage = "engaged"
        is_qualified = True

    elif analysis.reply_type == "information_request":
        new_stage = "info_requested"

    elif analysis.reply_type == "defer":
        new_stage = "deferred"

    elif analysis.reply_type == "rejection":
        new_stage = "closed"

    elif analysis.reply_type == "unclear":
        new_stage = "awaiting_clarification"

    if analysis.next_action == "offer_scheduling":
        is_handoff_required = False

    return ConversationState(
        company_name=state.company_name,
        channel=state.channel,
        stage=new_stage,
        last_outbound_message=state.last_outbound_message,
        last_inbound_message=reply_text,
        next_action=analysis.next_action,
        is_handoff_required=is_handoff_required,
        is_qualified=is_qualified,
        is_booked=is_booked,
    )
