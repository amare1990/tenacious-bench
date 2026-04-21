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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Conversion Engine pipeline.")
    parser.add_argument("--company", required=True, help="Company name to process")
    parser.add_argument("--reply", required=False, help="Optional reply text to simulate a second turn")
    parser.add_argument("--recipient", required=False, help="Recipient email address")
    parser.add_argument("--send", action="store_true", help="Actually send the email instead of draft-only output")
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

    state = ConversationState(
        company_name=company.company_name,
        channel="email",
        stage="researched",
        next_action="send_outreach",
    )

    reply_analysis = None
    followup_email = None
    followup_delivery = None

    if policy_result["should_contact"]:
        email = generate_email(
            company=company,
            signals=signals,
            ai=ai,
            gap=gap,
            segment_result=segment_result,
            policy_result=policy_result,
        )

        target_recipient = recipient or os.getenv("DEFAULT_EMAIL_RECIPIENT", "test@example.com")

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
            followup_email = generate_followup_email(company.company_name, reply_analysis)

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

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

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
        "conversation_state": state,
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

    if followup_email is not None:
        print("\n=== FOLLOW-UP EMAIL ===")
        print("Subject:", followup_email["subject"])
        print("Body:\n", followup_email["body"])

        print("\n=== FOLLOW-UP DELIVERY ===")
        print(followup_delivery)

    print("\n=== CONVERSATION STATE ===")
    print(state.model_dump())

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
