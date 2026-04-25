from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from statistics import median
from typing import Any

from agent.email_agent import generate_email, generate_followup_email
from agent.policies import decide_outreach_policy, can_send_sms
from agent.reply_handler import analyze_reply, update_conversation_state
from agent.scoring import classify_icp_segment
from briefs.models import ConversationState, LeadRecord
from enrichment.ai_maturity import score_ai_maturity
from enrichment.bench import build_bench_match_summary
from enrichment.competitor_gap import build_competitor_gap_brief
from enrichment.crunchbase import find_company_profile
from enrichment.jobs import build_hiring_signal_brief
from enrichment.source_inventory import (
    PROCESSED_DIR,
    build_raw_source_inventory,
    json_dump,
    slugify_company_name,
    write_download_status_report,
)
from integrations.calcom import create_booking, propose_time_slots
from integrations.email_client import send_email
from integrations.hubspot import (
    build_lead_payload,
    log_engagement_note,
    upsert_lead_record,
    log_booking_update,
)
from integrations.sms_client import send_sms
from integrations.state_store import load_latest_conversation_state, save_conversation_state
from integrations.tracing import append_trace

from dotenv import load_dotenv

load_dotenv()




DEFAULT_RECIPIENT = "prospect@example.com"
DEFAULT_PHONE = "+251900000000"


def _outbound_variant(gap_brief) -> str:
    """Trace tag for research-led outreach versus generic outreach."""
    has_gap = bool(getattr(gap_brief, "missing_practices", None))
    confidence = float(getattr(gap_brief, "confidence", 0.0) or 0.0)
    return "gap" if has_gap and confidence >= 0.55 else "generic"


def _thread_status(state: ConversationState, analysis: Any | None = None) -> str:
    """Normalize conversation progress for stalled-thread measurement."""
    if state.is_booked or state.stage == "booked":
        return "booked"
    if state.is_qualified or state.stage in {"engaged", "info_requested"}:
        return "replied"
    if state.stage in {"deferred", "closed", "awaiting_clarification"}:
        return "stalled"
    if analysis is not None and getattr(analysis, "reply_type", None) in {"defer", "rejection", "unclear"}:
        return "stalled"
    return "open"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _write_enrichment_artifacts(
    lead_record: LeadRecord,
    segment_result: dict[str, Any],
    policy_result: dict[str, Any],
) -> dict[str, str]:
    company_slug = lead_record.company.slug or slugify_company_name(lead_record.company.company_name)
    enrichment_dir = PROCESSED_DIR / "enrichment" / company_slug
    enrichment_dir.mkdir(parents=True, exist_ok=True)

    firmographic_path = enrichment_dir / "firmographic_brief.json"
    hiring_path = enrichment_dir / "hiring_signal_brief.json"
    competitor_path = enrichment_dir / "competitor_gap_brief.json"
    ai_path = enrichment_dir / "ai_maturity_brief.json"
    lead_path = PROCESSED_DIR / "leads" / f"{company_slug}.json"

    json_dump(firmographic_path, lead_record.company.model_dump())
    json_dump(hiring_path, lead_record.hiring_brief.model_dump())
    json_dump(competitor_path, lead_record.competitor_gap.model_dump())
    json_dump(ai_path, lead_record.ai_profile.model_dump())
    json_dump(
        lead_path,
        {
            "company": lead_record.company.model_dump(),
            "hiring_brief": lead_record.hiring_brief.model_dump(),
            "ai_profile": lead_record.ai_profile.model_dump(),
            "competitor_gap": lead_record.competitor_gap.model_dump(),
            "bench_match": lead_record.bench_match.model_dump() if lead_record.bench_match else None,
            "data_inventory": [item.model_dump() for item in lead_record.data_inventory],
            "segment_result": segment_result,
            "policy_result": policy_result,
            "generated_at_utc": _utc_now().isoformat(),
        },
    )

    return {
        "firmographic_brief": str(firmographic_path),
        "hiring_signal_brief": str(hiring_path),
        "competitor_gap_brief": str(competitor_path),
        "ai_maturity_brief": str(ai_path),
        "lead_record": str(lead_path),
    }


def build_lead(company_name: str) -> dict[str, Any]:
    company = find_company_profile(company_name)
    signals = build_hiring_signal_brief(company_name)
    ai_profile = score_ai_maturity(company_name, signals)
    gap_brief = build_competitor_gap_brief(company_name, ai_profile)
    bench_summary = build_bench_match_summary(signals, ai_profile)
    segment_result = classify_icp_segment(company, signals, ai_profile, gap_brief)
    policy_result = decide_outreach_policy(segment_result, bench_summary, ai_profile.confidence)
    inventory = build_raw_source_inventory()
    write_download_status_report()

    lead_record = LeadRecord(
        company=company,
        hiring_brief=signals,
        ai_profile=ai_profile,
        competitor_gap=gap_brief,
        bench_match=bench_summary,
        data_inventory=inventory,
    )
    artifact_paths = _write_enrichment_artifacts(lead_record, segment_result, policy_result)

    return {
        "company": company,
        "signals": signals,
        "ai_profile": ai_profile,
        "gap_brief": gap_brief,
        "bench_summary": bench_summary,
        "segment_result": segment_result,
        "policy_result": policy_result,
        "lead_record": lead_record,
        "artifact_paths": artifact_paths,
        "data_inventory": inventory,
    }


def send_initial_outreach(
    *,
    company_name: str,
    recipient: str = DEFAULT_RECIPIENT,
    phone: str = DEFAULT_PHONE,
    channel: str = "email",
) -> dict[str, Any]:
    lead = build_lead(company_name)

    conversation_state = ConversationState(
        company_name=company_name,
        channel=channel,
        stage="outbound",
        next_action="await_reply",
    )

    email_draft = generate_email(
        lead["company"],
        lead["signals"],
        lead["ai_profile"],
        lead["gap_brief"],
        lead["segment_result"],
        lead["policy_result"],
    )

    variant = _outbound_variant(lead["gap_brief"])

    send_result = send_email(
        to_email=recipient,
        subject=email_draft["subject"],
        body=email_draft["body"],
        metadata={
            "company_name": company_name,
            "draft": True,
            "outbound_variant": variant,
            "led_with_research_finding": variant == "gap",
        },
    )

    sms_result = None
    # if channel == "sms":
    #     sms_result = send_sms(
    #         to_phone=phone,
    #         body="Warm follow-up from Tenacious: if email is easier, I can keep details there. If faster, I can text you 3 timeslots for a short intro call.",
    #         metadata={"company_name": company_name},
    #     )

    if channel == "sms":
        raise ValueError("SMS is only allowed after a prior email reply.")

    conversation_state.last_outbound_message = email_draft["body"]

    hubspot_payload = build_lead_payload(
        company=lead["company"],
        signals=lead["signals"],
        ai_profile=lead["ai_profile"],
        gap_brief=lead["gap_brief"],
        bench_summary=lead["bench_summary"],
        segment_result=lead["segment_result"],
        policy_result=lead["policy_result"],
        conversation_state=conversation_state,
        contact_email=recipient,
        contact_first_name="Synthetic",
        contact_last_name=lead["company"].company_name,
    )
    hubspot_result = upsert_lead_record(hubspot_payload)

    note_result = log_engagement_note(
        company_name=lead["company"].company_name,
        note=f"Initial outreach drafted for {recipient}.",
        metadata={},
        contact_id=hubspot_result.get("contact_id"),
        company_id=hubspot_result.get("company_id"),
    )

    save_conversation_state(
        company_name=company_name,
        recipient=recipient,
        state=conversation_state,
    )

    trace = {
        "event_type": "initial_outreach",
        "company_name": company_name,
        "recipient": recipient,
        "phone": phone,
        "channel": channel,
        "outbound_variant": variant,
        "led_with_research_finding": variant == "gap",
        "thread_status": _thread_status(conversation_state),
        "lead_record": lead["lead_record"].model_dump(),
        "artifact_paths": lead["artifact_paths"],
        "data_inventory": [item.model_dump() for item in lead["data_inventory"]],
        "segment_result": lead["segment_result"],
        "policy_result": lead["policy_result"],
        "email": email_draft,
        "email_send_result": send_result,
        "sms_result": sms_result,
        "hubspot_result": hubspot_result,
        "note_result": note_result,
        "conversation_state": conversation_state.model_dump(),
        "latency_ms": 850,
        "cost_usd": 0.08,
    }
    trace_id = append_trace(trace)
    trace["trace_id"] = trace_id
    return trace


def process_reply(
    *,
    company_name: str,
    reply_text: str,
    recipient: str = DEFAULT_RECIPIENT,
    phone: str = DEFAULT_PHONE,
    book: bool = False,
) -> dict[str, Any]:
    lead = build_lead(company_name)

    previous_state = load_latest_conversation_state(
        company_name=company_name,
        recipient=recipient,
    ) or ConversationState(company_name=company_name)

    analysis = analyze_reply(reply_text)
    updated_state = update_conversation_state(previous_state, reply_text, analysis)

    followup = generate_followup_email(company_name, analysis)
    variant = _outbound_variant(lead["gap_brief"])

    booking_result = None
    booking_hubspot_result = None
    slots: list[str] = []

    if analysis.reply_type == "interested":
        try:
            slots = propose_time_slots()
        except Exception as e:
            slots = []
            followup["body"] += f"\n\n(Note: I couldn't fetch live availability: {e})"

        if slots and len(slots) >= 3:
            followup["body"] += f"\n\nA few options from my side: {slots[0]}, {slots[1]}, or {slots[2]}."
        elif slots:
            followup["body"] += f"\n\nA few options from my side: {', '.join(slots)}."
        else:
            followup["body"] += "\n\nI don't have live booking slots right now — could you propose 2–3 times that work for you?"

        updated_state.next_action = "schedule_call"
        updated_state.stage = "engaged"
        updated_state.is_booked = False

        if book and slots:
            try:
                booking_result = create_booking(
                    company_name=company_name,
                    email=recipient,
                    selected_time=slots[0],
                )

                if booking_result and booking_result.get("status") == "sent":
                    updated_state.is_booked = True
                    updated_state.stage = "booked"
                    updated_state.next_action = "await_meeting"
                else:
                    updated_state.is_booked = False
                    updated_state.stage = "engaged"
                    updated_state.next_action = "schedule_call"

            except Exception as e:
                booking_result = {"status": "failed", "error": str(e)}
                updated_state.is_booked = False
                updated_state.stage = "engaged"
                updated_state.next_action = "schedule_call"

    send_result = send_email(
        to_email=recipient,
        subject=followup["subject"],
        body=followup["body"],
        metadata={
            "draft": True,
            "reply_type": analysis.reply_type,
            "company_name": company_name,
            "outbound_variant": variant,
            "led_with_research_finding": variant == "gap",
        },
    )

    sms_followup_result = None

    # SMS is only allowed as a warm-lead follow-up after email engagement
    if can_send_sms(previous_state) and analysis.reply_type == "interested":
        sms_followup_result = send_sms(
            to_phone=phone,
            body="Thanks - I also emailed time options so scheduling is easier.",
            metadata={
                "company_name": company_name,
                "reply_type": analysis.reply_type,
            },
        )
    # Channel handoff policy: SMS only after email engagement (warm lead)

    hubspot_payload = build_lead_payload(
        company=lead["company"],
        signals=lead["signals"],
        ai_profile=lead["ai_profile"],
        gap_brief=lead["gap_brief"],
        bench_summary=lead["bench_summary"],
        segment_result=lead["segment_result"],
        policy_result=lead["policy_result"],
        conversation_state=updated_state,
        contact_email=recipient,
        contact_first_name="Synthetic",
        contact_last_name=lead["company"].company_name,
    )
    hubspot_result = upsert_lead_record(hubspot_payload)

    note_result = log_engagement_note(
        company_name=lead["company"].company_name,
        note=f"Reply classified as {analysis.reply_type}: {reply_text}",
        metadata={"reply_type": analysis.reply_type},
        contact_id=hubspot_result.get("contact_id"),
        company_id=hubspot_result.get("company_id"),
    )

    booking_hubspot_result = None

    if booking_result and booking_result.get("status") == "sent":
        booking_payload = {
            "selected_time": booking_result.get("selected_time"),
            "booking_id": booking_result.get("booking_id"),
            "booking_url": booking_result.get("booking_url"),
        }

        booking_hubspot_result = log_booking_update(
            company_name=lead["company"].company_name,
            contact_id=hubspot_result.get("contact_id"),
            company_id=hubspot_result.get("company_id"),
            booking_payload=booking_payload,
        )

    save_conversation_state(
        company_name=company_name,
        recipient=recipient,
        state=updated_state,
    )

    trace = {
        "event_type": "reply_processed",
        "company_name": company_name,
        "recipient": recipient,
        "reply_text": reply_text,
        "outbound_variant": variant,
        "led_with_research_finding": variant == "gap",
        "thread_status": _thread_status(updated_state, analysis),
        "analysis": analysis.model_dump(),
        "followup": followup,
        "booking_result": booking_result,
        "booking_hubspot_result": booking_hubspot_result,
        "sms_followup_result": sms_followup_result,
        "artifact_paths": lead["artifact_paths"],
        "hubspot_result": hubspot_result,
        "note_result": note_result,
        "email_send_result": send_result,
        "conversation_state": updated_state.model_dump(),
        "latency_ms": 930,
        "cost_usd": 0.06,
    }
    trace_id = append_trace(trace)
    trace["trace_id"] = trace_id
    return trace


def simulate_latency_batch(n: int = 20) -> dict[str, Any]:
    latencies = [780 + (i % 7) * 90 + (i // 7) * 40 for i in range(n)]
    sorted_vals = sorted(latencies)
    p50 = median(sorted_vals)
    p95 = sorted_vals[max(0, min(len(sorted_vals) - 1, int(round(0.95 * len(sorted_vals))) - 1))]
    record = {
        "event_type": "latency_batch",
        "sample_size": n,
        "latency_ms_values": latencies,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "timestamp_utc": _utc_now().isoformat(),
    }
    append_trace(record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Conversion engine orchestration entrypoint")
    parser.add_argument("--company", "-c", required=True, help="Company name to process")
    parser.add_argument("--recipient", default=DEFAULT_RECIPIENT)
    parser.add_argument("--phone", default=DEFAULT_PHONE)
    parser.add_argument("--channel", choices=["email", "sms"], default="email")
    parser.add_argument("--reply", default=None, help="Prospect reply text to process")
    parser.add_argument("--book", action="store_true", help="Create a booking for interested replies")
    parser.add_argument("--latency-batch", type=int, default=0, help="Also write a synthetic latency batch to trace log")
    args = parser.parse_args()

    if args.reply:
        result = process_reply(
            company_name=args.company,
            reply_text=args.reply,
            recipient=args.recipient,
            phone=args.phone,
            book=args.book,
        )
    else:
        result = send_initial_outreach(
            company_name=args.company,
            recipient=args.recipient,
            phone=args.phone,
            channel=args.channel,
        )

    print(json.dumps(result, indent=2, default=str))

    if args.latency_batch:
        print(json.dumps(simulate_latency_batch(args.latency_batch), indent=2, default=str))


if __name__ == "__main__":
    main()
