
---

# ACT III Implementation

### `target_failure_mode.md`

# Target Failure Mode — Highest-ROI Attack for Act IV

## Selected failure mode

**Signal over-claiming under weak or conflicting public evidence.**

This includes probes P-005 through P-008 and overlaps with signal reliability probes P-027 through P-029 and gap over-claiming probes P-030 through P-032.

## Why this is the highest-ROI failure mode

Tenacious outbound is explicitly built around signal-grounded personalization: hiring signals, AI-maturity evidence, and competitor gap framing. If the agent overstates those signals, the core differentiator becomes the core liability.

A wrong signal is worse than a generic email because it tells the buyer that Tenacious did research, but did it badly. That damages the brand more than ordinary low-quality outbound.

## Business-cost derivation

Assumptions for Act IV measurement:

* Tenacious sends 1,000 outbound emails in a pilot.
* Signal-grounded outbound produces a 7%–12% reply rate.
* Generic outbound is assumed to produce a lower reply rate.
* 5% of signal-grounded emails may contain materially wrong or overstated public-signal claims unless constrained.
* Each wrong-signal email has reputational cost because it reaches high-value founders, CTOs, or VP Engineering buyers.

Expected cost path:

1. **False confidence in public evidence** leads to an overstated claim.
2. The buyer challenges the claim.
3. The agent either doubles down or apologizes weakly.
4. The buyer marks Tenacious as careless, spammy, or poorly researched.
5. Future outreach to the account becomes harder, even if the underlying Tenacious service is strong.

## Why not choose multi-thread leakage first?

Multi-thread leakage is more severe per incident, but it should be addressed as a hard privacy/infrastructure constraint. It is less likely to be improved meaningfully by a language-level Act IV mechanism alone.

## Why not choose bench over-commitment first?

Bench over-commitment is also severe, but the fix is comparatively direct: a bench-gated commitment policy. Signal over-claiming is subtler, more frequent, and central to the system's value proposition.

## Act IV mechanism direction

Implement **signal-confidence-aware phrasing**:

* Every claim about hiring, AI maturity, and competitor gap receives an evidence-confidence score.
* Low-confidence evidence produces cautious language.
* Conflicting evidence triggers abstention or exploratory phrasing.
* Unsupported gaps are framed as public-signal absence, never as actual capability absence.
* If the prospect challenges the evidence, the agent must downgrade confidence and preserve tone.

## Success metric for Act IV

The mechanism should reduce signal-overclaim failures on held-out probes while preserving reply-oriented specificity.

Primary metric:

* **Signal honesty pass rate** on held-out traces.

Secondary metrics:

* Reply-quality score.
* Tone-preservation score after challenge turns.
* Cost per generated outbound message.
* Rate of abstention on genuinely ambiguous evidence.

## Hypothesis

A signal-confidence-aware phrasing mechanism will outperform the Day-1 baseline because it directly attacks the highest-frequency, highest-brand-risk failure in Tenacious's differentiated outbound motion.
