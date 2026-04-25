---
mainfont: DejaVu Sans
geometry: margin=0.55in
fontsize: 9pt
---

# The Conversion Engine — Decision Memo

## Page 1 — The Decision

**Executive summary.** We built an email-first, signal-grounded outbound system for Tenacious that researches synthetic prospects, generates hiring-signal and competitor-gap briefs, qualifies replies, writes HubSpot records, and coordinates Cal.com booking with SMS reserved for warm scheduling handoff. Current trace-backed results show 100% of generated outbound traces used the research-led competitor-gap path, a measured stalled-thread rate of 14.29%, and $0.11 trace cost per qualified synthetic lead. Recommendation: run a controlled Segment 1 pilot only after TRP review, with all Tenacious-branded content marked draft and live outbound gated behind explicit approval.
TRP-provided evaluation artifacts are included in the repository as reference benchmarks and are not recomputed locally.

**Cost per qualified lead.** From `metrics/final_metrics.json`, trace files record 22 qualified synthetic leads and $2.36 total trace cost, giving a measured cost per qualified lead of **$0.11**. This is not a live-market CPL claim; it is a trace-backed unit-cost estimate from the submitted harness. The Tenacious grading target is under $5 per qualified lead, so the pilot should retain that threshold as the operating budget guardrail.

**Stalled-thread rate delta.** Tenacious’s current manual process stalls **30–40%** of qualified conversations in the first two weeks. The submitted traces classify 4 stalled threads across 28 status-bearing thread records, for a measured synthetic stalled-thread rate of **14.29%**. Pilot success criterion: keep verified stalled qualified threads below **25%** after 30 days, otherwise roll back to manual-review mode.

**Competitive-gap outbound performance.** The updated challenge asks for the fraction of outbound that led with a research finding versus a generic Tenacious pitch. The current trace set has 30 research-led/gap-tagged outbound events and 0 generic-tagged outbound events, so the demonstrated gap-led fraction is **100%**. Because there is no generic control arm in the current traces, the reply-rate delta is **not measured**; the pilot must add a 70/30 gap-vs-generic holdout to measure whether research-led outreach beats generic positioning.

**Pilot scope recommendation.** Start with **Segment 1 — recently funded Series A/B startups** because this segment has a clear buying window, uses the least sensitive restructuring language, and maps naturally to Tenacious’s engineering-squad offer. Volume: 50 synthetic-reviewed leads/week before any live pilot. Budget: remain under $5 per qualified lead and under $100/month until live CPL is measured. Success criterion after 30 days: verified signal-error rate <5%, stalled qualified threads <25%, zero bench over-commitment incidents, and a measurable reply-rate lift versus the generic holdout.

\newpage

## Page 2 — The Skeptic’s Appendix

**Four failure modes tau2-Bench does not capture.** First, offshore-perception risk: language that sounds like labor arbitrage may alienate CTOs or hiring managers even if technically accurate. Second, bench mismatch: promising Python, data, ML, or infra capacity not present in the bench summary damages trust immediately. Third, wrong-signal brand risk: a false claim about hiring velocity, funding, layoffs, leadership change, or competitor practice makes the outreach feel careless. Fourth, multi-thread inconsistency: separate conversations with a founder and VP Engineering at the same company can contradict each other unless company-level memory is isolated and audited.

**Public-signal lossiness.** False negatives occur when sophisticated companies keep AI work private: the system may score them low and under-pitch capability-gap consulting. False positives occur when companies publish AI-heavy marketing but show little implementation evidence: the system may over-pitch advanced AI work. The mitigation is confidence-aware phrasing: weak evidence must trigger questions, not assertions, and high AI-readiness claims require multiple high-weight inputs.

**Gap-analysis risks.** A top-quartile competitor practice is not automatically a good benchmark. A prospect may intentionally avoid a sector trend because of regulation, cost discipline, product focus, or technical debt sequencing. The agent must frame gaps as “observed public differences” rather than deficiencies. The business risk is sounding condescending to a CTO who has already made a deliberate tradeoff.

**Brand-reputation comparison.** Signal-grounded outbound is only worth the risk if factual quality remains high. If 1,000 signal-grounded emails are sent and 5% contain wrong signal data, that creates 50 brand-damaging messages; at an assumed $500 reputation cost per wrong-signal email, the downside is $25,000. That assumption is intentionally conservative and must be treated as a planning assumption, not a Tenacious-provided number. Above 10% verified signal error, outbound should pause automatically.

**Honest unresolved failure.** The current trace set does not include a generic-control reply-rate arm, so the system proves it can generate and route research-led outreach but does not yet prove that competitor-gap positioning beats generic Tenacious positioning. If deployed unchanged, Tenacious could over-invest in a sophisticated research pitch without knowing the incremental lift.

**Kill-switch clause.** Pause outbound if verified signal-error rate exceeds 10%, reply rate falls below the generic-control arm for two consecutive weekly batches, stalled qualified threads exceed 25%, any bench over-commitment occurs, or more than two prospects object to factual claims in a single week. Roll back to manual review until the signal pipeline and phrasing policy are revalidated.
