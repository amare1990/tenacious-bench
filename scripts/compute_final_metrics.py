from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRACE_FILES = [
    ROOT / "data" / "trace_log.jsonl",
    ROOT / "eval" / "trace_log.jsonl",
    ROOT / "held_out_traces.jsonl",
]
TRP1_TRACE = ROOT / "eval" / "trp1-eval" / "trace_log.jsonl"
TRP1_SCORE = ROOT / "eval" / "trp1-eval" / "score_log.json"
METRICS_PATH = ROOT / "metrics" / "final_metrics.json"
EVIDENCE_PATH = ROOT / "evidence_graph.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def nested_get(row: dict[str, Any], *keys: str) -> Any:
    cur: Any = row
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def infer_variant(row: dict[str, Any]) -> str:
    explicit = row.get("outbound_variant") or nested_get(row, "payload", "outbound_variant")
    if explicit in {"gap", "generic"}:
        return explicit
    led = row.get("led_with_research_finding")
    if led is None:
        led = nested_get(row, "payload", "led_with_research_finding")
    if led is not None:
        return "gap" if bool(led) else "generic"
    text = json.dumps(row, ensure_ascii=False).lower()
    return "gap" if "competitor_gap" in text or "peer" in text or "top_quartile" in text else "generic"


def infer_thread_status(row: dict[str, Any]) -> str:
    explicit = row.get("thread_status") or nested_get(row, "payload", "thread_status")
    if explicit:
        return str(explicit)
    state = row.get("conversation_state") or nested_get(row, "payload", "conversation_state") or {}
    if state.get("is_booked") or state.get("stage") == "booked":
        return "booked"
    if state.get("is_qualified") or state.get("stage") in {"engaged", "info_requested"}:
        return "replied"
    if state.get("stage") in {"deferred", "closed", "awaiting_clarification"}:
        return "stalled"
    analysis = row.get("analysis") or nested_get(row, "payload", "analysis") or {}
    if analysis.get("reply_type") in {"defer", "rejection", "unclear"}:
        return "stalled"
    return "open"


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    idx = max(0, min(len(vals) - 1, round((p / 100.0) * (len(vals) - 1))))
    return vals[idx]


def main() -> None:
    rows: list[dict[str, Any]] = []
    for path in TRACE_FILES:
        rows.extend(load_jsonl(path))

    outbound = [r for r in rows if (r.get("event_type") or nested_get(r, "payload", "event_type")) in {"initial_outreach", "prospect_pipeline_run"}]
    replies = [r for r in rows if (r.get("event_type") or nested_get(r, "payload", "event_type")) in {"reply_processed", "reply"} or r.get("reply_text")]

    variant_counts = {"gap": 0, "generic": 0}
    for r in outbound:
        variant_counts[infer_variant(r)] += 1

    reply_counts = {"gap": 0, "generic": 0}
    for r in replies:
        reply_counts[infer_variant(r)] += 1

    rates: dict[str, float | None] = {}
    for variant in ["gap", "generic"]:
        denom = variant_counts[variant]
        rates[f"reply_rate_{variant}"] = None if denom == 0 else round(reply_counts[variant] / denom, 4)

    statuses = [infer_thread_status(r) for r in rows if r.get("conversation_state") or r.get("thread_status")]
    total_threads = len(statuses)
    stalled_threads = sum(1 for s in statuses if s == "stalled")
    qualified = sum(1 for r in rows if nested_get(r, "conversation_state", "is_qualified") or nested_get(r, "payload", "conversation_state", "is_qualified"))
    total_cost = sum(float(r.get("cost_usd") or nested_get(r, "payload", "cost_usd") or 0.0) for r in rows)
    latencies = [float(r.get("latency_ms") or nested_get(r, "payload", "latency_ms") or 0.0) for r in rows if (r.get("latency_ms") or nested_get(r, "payload", "latency_ms"))]

    metrics: dict[str, Any] = {
        "source_trace_files": [str(p.relative_to(ROOT)) for p in TRACE_FILES if p.exists()],
        "outbound_total": len(outbound),
        "outbound_variant_counts": variant_counts,
        "competitive_gap_outbound_fraction": None if len(outbound) == 0 else round(variant_counts["gap"] / len(outbound), 4),
        "reply_counts_by_variant": reply_counts,
        "reply_rate_gap": rates["reply_rate_gap"],
        "reply_rate_generic": rates["reply_rate_generic"],
        "reply_rate_delta_gap_minus_generic": None if rates["reply_rate_gap"] is None or rates["reply_rate_generic"] is None else round(rates["reply_rate_gap"] - rates["reply_rate_generic"], 4),
        "thread_status_counts": {s: statuses.count(s) for s in sorted(set(statuses))},
        "stalled_thread_rate": None if total_threads == 0 else round(stalled_threads / total_threads, 4),
        "qualified_leads": qualified,
        "total_cost_usd": round(total_cost, 4),
        "cost_per_qualified_lead_usd": None if qualified == 0 else round(total_cost / qualified, 4),
        "p50_latency_ms": None if not latencies else round(median(latencies), 2),
        "p95_latency_ms": percentile(latencies, 95),
        "trp1_eval_present": TRP1_TRACE.exists() or TRP1_SCORE.exists(),
    }

    if TRP1_SCORE.exists():
        try:
            metrics["trp1_score_log"] = json.loads(TRP1_SCORE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            metrics["trp1_score_log"] = "present_but_not_json"

    evidence = {
        "claims": [
            {"claim_id": "competitive_gap_outbound_fraction", "value": metrics["competitive_gap_outbound_fraction"], "source_ref": "metrics/final_metrics.json + trace files", "trace_files": metrics["source_trace_files"]},
            {"claim_id": "reply_rate_gap", "value": metrics["reply_rate_gap"], "source_ref": "metrics/final_metrics.json + trace files", "trace_files": metrics["source_trace_files"]},
            {"claim_id": "reply_rate_generic", "value": metrics["reply_rate_generic"], "source_ref": "metrics/final_metrics.json + trace files", "trace_files": metrics["source_trace_files"]},
            {"claim_id": "reply_rate_delta_gap_minus_generic", "value": metrics["reply_rate_delta_gap_minus_generic"], "source_ref": "metrics/final_metrics.json + trace files", "trace_files": metrics["source_trace_files"]},
            {"claim_id": "stalled_thread_rate", "value": metrics["stalled_thread_rate"], "source_ref": "metrics/final_metrics.json + trace files", "trace_files": metrics["source_trace_files"]},
            {"claim_id": "cost_per_qualified_lead_usd", "value": metrics["cost_per_qualified_lead_usd"], "source_ref": "metrics/final_metrics.json + trace files", "trace_files": metrics["source_trace_files"]},
            {"claim_id": "p50_latency_ms", "value": metrics["p50_latency_ms"], "source_ref": "metrics/final_metrics.json + trace files", "trace_files": metrics["source_trace_files"]},
            {"claim_id": "p95_latency_ms", "value": metrics["p95_latency_ms"], "source_ref": "metrics/final_metrics.json + trace files", "trace_files": metrics["source_trace_files"]},
            {"claim_id": "tenacious_manual_stalled_thread_rate", "value": "30-40%", "source_ref": "TRP1 Week 10 challenge document / Tenacious executive interview"},
            {"claim_id": "tenacious_outsourcing_acv", "value": "$240K-$720K", "source_ref": "TRP1 Week 10 challenge document / Tenacious internal weighted by segment"},
            {"claim_id": "tenacious_project_consulting_acv", "value": "$80K-$300K", "source_ref": "TRP1 Week 10 challenge document / Tenacious internal last 8 deals"},
            {"claim_id": "cold_email_reply_baseline", "value": "1-3%", "source_ref": "TRP1 Week 10 challenge document / LeadIQ 2026 + Apollo benchmarks"},
            {"claim_id": "signal_grounded_reply_top_quartile", "value": "7-12%", "source_ref": "TRP1 Week 10 challenge document / Clay + Smartlead case studies"},
        ]
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
