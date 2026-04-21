from __future__ import annotations

import argparse
import os
import time

from enrichment.crunchbase import find_company_profile
from enrichment.jobs import build_hiring_signal_brief
from enrichment.ai_maturity import score_ai_maturity
from enrichment.competitor_gap import build_competitor_gap_brief
from enrichment.bench import build_bench_match_summary

from agent.scoring import classify_icp_segment
from agent.policies import decide_outreach_policy
from agent.email_agent import generate_email, generate_followup_email
from agent.reply_handler import analyze_reply, update_conversation_state

from briefs.models import ConversationState

from integrations.tracing import log_trace
from integrations.email_client import send_email
from integrations.hubspot import (
    build_lead_payload,
    upsert_lead_record,
    log_engagement_note,
)
from integrations.calcom import propose_time_slots, create_booking
from integrations.state_store import (
    load_latest_conversation_state,
    save_conversation_state,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Conversion Engine pipeline.")
    parser.add_argument("--company", required=True, help="Company name to process")
    parser.add_argument(
        "--reply",
        required=False,
        help="Optional reply text to simulate a second turn",
    )
    parser.add_argument(
        "--recipient",
        required=False,
        help="Recipient email address",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Actually send the email instead of draft-only output",
    )
    return parser.parse_args()


def run_pipeline(
    company_name: str,
    reply_text: str | None = None,
    recipient: str | None = None,
    send: bool = False,
) -> None:
    started_at = time.perf_counter()

    if send:
        os.environ["EMAIL_MODE"] = "live"

    company = find_company_profile(company_name)
    signals = build_hiring_signal_brief(company_name)
    ai = score_ai_maturity(company_name, signals)
    gap = build_competitor_gap_brief(company_name, ai)
    bench = build_bench_match_summary(signals, ai)

    segment_result = classify_icp_segment(company, signals, ai, gap)
    policy_result = decide_outreach_policy(segment_result, bench)

    email = None
    email_delivery = None
    reply_analysis = None
    followup_email = None
    followup_delivery = None
    proposed_slots = None
    booking_result = None
    hubspot_lead_result = None
    hubspot_note_result = None

    target_recipient = recipient or os.getenv(
        "DEFAULT_EMAIL_RECIPIENT",
        "test@example.com",
    )

    existing_state = load_latest_conversation_state(
        company_name=company.company_name,
        recipient=target_recipient,
    )

    state = existing_state or ConversationState(
        company_name=company.company_name,
        channel="email",
        stage="researched",
        next_action="send_outreach",
    )

    if policy_result["should_contact"]:
        email = generate_email(
            company=company,
            signals=signals,
            ai=ai,
            gap=gap,
            segment_result=segment_result,
            policy_result=policy_result,
        )

        # target_recipient = recipient or os.getenv(
        #     "DEFAULT_EMAIL_RECIPIENT",
        #     "test@example.com",
        # )

        email_delivery = send_email(
            to_email=target_recipient,
            subject=email["subject"],
            body=email["body"],
            metadata={
                "company_name": company.company_name,
                "segment": segment_result["segment"],
                "confidence": segment_result["confidence"],
                "type": "initial_outreach",
            },
        )

        state = ConversationState(
            company_name=company.company_name,
            channel="email",
            stage="contacted",
            last_outbound_message=email["body"],
            next_action="await_reply",
            is_handoff_required=policy_result["require_handoff"],
            is_qualified=False,
            is_booked=False,
        )

        if reply_text:
            reply_analysis = analyze_reply(reply_text)
            state = update_conversation_state(state, reply_text, reply_analysis)

            followup_email = generate_followup_email(
                company.company_name,
                reply_analysis,
            )

            followup_delivery = send_email(
                to_email=target_recipient,
                subject=followup_email["subject"],
                body=followup_email["body"],
                metadata={
                    "company_name": company.company_name,
                    "reply_type": reply_analysis.reply_type,
                    "type": "followup",
                },
            )

            if reply_analysis.reply_type == "interested":
                proposed_slots = propose_time_slots()
                selected_time = proposed_slots[0]

                booking_result = create_booking(
                    company_name=company.company_name,
                    email=target_recipient,
                    selected_time=selected_time,
                )

                state.is_booked = True
                state.stage = "booked"
                state.next_action = "booking_confirmed"

    lead_payload = build_lead_payload(
        company=company,
        signals=signals,
        ai_profile=ai,
        gap_brief=gap,
        bench_summary=bench,
        segment_result=segment_result,
        policy_result=policy_result,
        conversation_state=state,
    )

    hubspot_lead_result = upsert_lead_record(lead_payload)

    note_text_parts = [
        f"Pipeline processed for {company.company_name}.",
        f"Segment: {segment_result['segment']} ({segment_result['confidence']}).",
        f"Policy: should_contact={policy_result['should_contact']}, tone={policy_result['tone_mode']}.",
        f"Conversation stage: {state.stage}.",
    ]

    if reply_analysis is not None:
        note_text_parts.append(
            f"Reply classified as {reply_analysis.reply_type} with next action {reply_analysis.next_action}."
        )

    if booking_result is not None:
        note_text_parts.append("Discovery call booking was created.")

    hubspot_note_result = log_engagement_note(
        company_name=company.company_name,
        note=" ".join(note_text_parts),
        metadata={
            "segment_result": segment_result,
            "policy_result": policy_result,
            "conversation_state": state.model_dump(),
            "reply_analysis": None if reply_analysis is None else reply_analysis.model_dump(),
            "booking_result": booking_result,
        },
    )

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

    save_conversation_state(
        company_name=company.company_name,
        recipient=target_recipient,
        state=state,
        metadata={
            "segment_result": segment_result,
            "policy_result": policy_result,
            "reply_analysis": None if reply_analysis is None else reply_analysis.model_dump(),
            "booking_result": booking_result,
        },
    )

    trace_payload = {
        "company_name": company_name,
        "company_profile": company,
        "hiring_signal_brief": signals,
        "ai_maturity_profile": ai,
        "competitor_gap_brief": gap,
        "bench_match_summary": bench,
        "segment_result": segment_result,
        "policy_result": policy_result,
        "initial_email": email,
        "initial_email_delivery": email_delivery,
        "reply_text": reply_text,
        "reply_analysis": reply_analysis,
        "followup_email": followup_email,
        "followup_email_delivery": followup_delivery,
        "proposed_slots": proposed_slots,
        "booking_result": booking_result,
        "conversation_state": state,
        "hubspot_lead_result": hubspot_lead_result,
        "hubspot_note_result": hubspot_note_result,
        "duration_ms": duration_ms,
    }

    log_trace(event_type="prospect_pipeline_run", payload=trace_payload)

    print("\n=== COMPANY ===")
    print(company.model_dump())

    print("\n=== SEGMENT ===")
    print(segment_result)

    print("\n=== POLICY ===")
    print(policy_result)

    if email is None:
        print("\n=== DECISION ===")
        print("Do not contact.")
    else:
        print("\n=== INITIAL EMAIL ===")
        print("Subject:", email["subject"])
        print("Body:\n", email["body"])

        print("\n=== INITIAL EMAIL DELIVERY ===")
        print(email_delivery)

    if reply_analysis is not None:
        print("\n=== REPLY ANALYSIS ===")
        print(reply_analysis.model_dump())

    if proposed_slots:
        print("\n=== PROPOSED SLOTS ===")
        for slot in proposed_slots:
            print("-", slot)

    if followup_email is not None:
        print("\n=== FOLLOW-UP EMAIL ===")
        print("Subject:", followup_email["subject"])
        print("Body:\n", followup_email["body"])

        print("\n=== FOLLOW-UP DELIVERY ===")
        print(followup_delivery)

    print("\n=== CONVERSATION STATE ===")
    print(state.model_dump())

    print("\n=== HUBSPOT LEAD RESULT ===")
    print(hubspot_lead_result)

    print("\n=== HUBSPOT NOTE RESULT ===")
    print(hubspot_note_result)

    if booking_result is not None:
        print("\n=== BOOKING RESULT ===")
        print(booking_result)

    print("\n=== STATE STORE ===")
    if existing_state is None:
        print("No previous conversation state found.")
    else:
        print("Loaded previous conversation state.")
        print(existing_state.model_dump())

    print("\n=== TRACE ===")
    print("Logged run to data/trace_log.jsonl")
    print(f"Duration: {duration_ms} ms")


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        company_name=args.company,
        reply_text=args.reply,
        recipient=args.recipient,
        send=args.send,
    )
