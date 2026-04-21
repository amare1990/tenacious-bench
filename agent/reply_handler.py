from __future__ import annotations

from briefs.models import ConversationState, ReplyAnalysis


def analyze_reply(reply_text: str) -> ReplyAnalysis:
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
