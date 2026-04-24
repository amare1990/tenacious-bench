---
mainfont: DejaVu Sans
geometry: margin=0.55in
fontsize: 9pt
---

# The Conversion Engine — Decision Memo

## Page 1 — The Decision

**Executive summary.** We built a signal-grounded outbound system that converts public hiring signals into research-led outreach and automated qualification for Tenacious. On the held-out tau2-Bench slice, the Act IV mechanism improved pass@1 from 0.40 to 1.00, a +0.60 Delta A with p = 0.00003, using signal-confidence-aware phrasing, ICP abstention, and bench-gated commitment. Recommendation: run a 30-day Segment 1 pilot targeting recently funded Series A/B startups, capped at 50 leads/week, with a kill-switch if signal error exceeds 10% or reply rate falls below 3% for two consecutive weeks.

**tau2-Bench results.** Day-1 baseline pass@1 was 0.40. The automated-optimization baseline was 0.40 on the same held-out slice. The final method reached 1.00 pass@1, with Delta A = +0.60 and p = 0.00003. Source files: `ablation_results.json`, `held_out_traces.jsonl`, `evidence_graph.json`.

**Cost per qualified lead.** The target is <$5 per qualified lead. This submission uses synthetic traces and does not claim live production CPL. The measured Act IV evaluation cost is trace-level only; for pilot planning, the system should remain capped under $100/month until live reply and qualification rates are measured.

**Stalled-thread rate delta.** Tenacious’s current manual process stalls 30–40% of qualified conversations in the first two weeks. The system reduces this risk by enforcing follow-up state, routing warm scheduling to SMS, and booking via Cal.com. Live stalled-thread delta is not yet measured; the pilot success criterion should be <25% stalled qualified threads after 30 days.

**Competitive-gap outbound performance.** The system supports research-led outreach using AI maturity and competitor-gap briefs. This submission demonstrates artifact generation and policy gating, but does not claim a live reply-rate delta. Pilot measurement should compare research-led outbound against generic Tenacious positioning, with target reply rate >=8%.

**Annualized dollar impact.** Using Tenacious benchmarks: discovery-to-proposal 35–50%, proposal-to-close 25–40%, and outsourcing ACV $240K–$720K. At 50 leads/week and an 8–10% reply rate, one segment creates roughly 208–260 annual conversations. At 40% discovery-to-proposal and 30% proposal-to-close, this implies 25–31 deals before capacity limits. At $240K–$720K ACV, the gross opportunity range is material enough to justify a controlled pilot, but not enough to justify unsupervised live deployment.

**Pilot recommendation.** Start with Segment 1 only: recently funded Series A/B startups. Volume: 50 leads/week. Budget cap: $100/month until live CPL is measured. Success criterion: >=8% reply rate, <25% stalled qualified threads, <5% verified signal-error rate, and zero bench over-commitment incidents.

\newpage

## Page 2 — The Skeptic’s Appendix

**Four failure modes tau2-Bench does not capture.** First, offshore-perception risk: language that sounds like labor arbitrage may alienate CTOs or hiring managers even if technically accurate. Second, bench mismatch: promising Python, data, ML, or infra capacity not present in the bench summary damages trust immediately. Third, wrong-signal brand risk: a false claim about hiring velocity, funding, layoffs, or leadership change makes the outreach feel careless. Fourth, multi-thread inconsistency: separate conversations with a founder and VP Engineering at the same company can contradict each other unless company-level memory is isolated and audited.

**Public-signal lossiness.** False negatives occur when sophisticated companies keep AI work private: the system may score them low and under-pitch capability-gap consulting. False positives occur when companies publish AI-heavy marketing but show little implementation evidence: the system may over-pitch advanced AI work. The mitigation is confidence-aware phrasing: weak evidence must trigger questions, not assertions.

**Gap-analysis risks.** A top-quartile competitor practice is not automatically a good benchmark. A prospect may intentionally avoid a sector trend because of regulation, cost discipline, product focus, or technical debt sequencing. The agent must frame gaps as “observed public differences” rather than deficiencies. The business risk is sounding condescending to a CTO who has already made a deliberate tradeoff.

**Brand-reputation comparison.** If 1,000 signal-grounded emails are sent and 5% contain wrong signal data, that is 50 brand-damaging messages. Assuming $500 reputational cost per wrong-signal email, the risk is $25,000. The upside can dominate only if reply lift is real and signal-error rate remains below 5%. Above 10%, the system should pause automatically.

**Honest unresolved failure.** The weakest unresolved area is probe realism. Some probe traces still reward safe generic replies rather than high-quality Tenacious-specific behavior. If deployed unchanged, this could under-detect tone drift and weak qualification behavior.

**Kill-switch clause.** Pause outbound if verified signal-error rate exceeds 10%, reply rate falls below 3% for two consecutive weeks, any bench over-commitment occurs, or more than two prospects object to factual claims in a single week. Roll back to manual review mode until the signal pipeline and phrasing policy are revalidated.
