
---

# ACT III Implementation

### `target_failure_mode.md`

# Target Failure Mode — Highest-ROI Attack for Act IV

## Selected failure mode

**Signal over-claiming under weak or conflicting public evidence.**

This includes probes P-005 through P-008 and overlaps with:

* Signal reliability failures (P-027 to P-029)
* Gap over-claiming failures (P-030 to P-032)

---

## Business-cost comparison (decision basis)

### Selected failure — signal over-claiming

Assumptions:

* 1,000 outbound emails in pilot
* 5% contain materially wrong or overstated signals
* $500 average reputational cost per incident

Calculation:

* 1,000 × 5% = 50 wrong-signal emails
* 50 × $500 = **$25,000 downside**

---

### Alternative A — Bench over-commitment

Assumptions:

* 1,000 outbound → 7% reply rate = 70 replies
* 10% involve staffing-capacity discussions = 7 threads
* 30% failure rate

Calculation:

* 7 × 0.30 = 2.1 incidents
* 2.1 × $2,500 = **$5,250 downside**

---

### Alternative B — Scheduling edge cases

Assumptions:

* 70 replies
* 40% reach scheduling = 28 threads
* 30% timezone / coordination failure rate

Calculation:

* 28 × 0.30 = 8.4 incidents
* 8.4 × $250 = **$2,100 downside**

---

### Decision

| Failure mode          | Estimated downside |
| --------------------- | -----------------: |
| Signal over-claiming  |            $25,000 |
| Bench over-commitment |             $5,250 |
| Scheduling edge cases |             $2,100 |

**Signal over-claiming is selected because it has ~5× higher expected downside and occurs earlier in the funnel, directly impacting brand trust and reply rates.**

---

## Why this is the highest-ROI failure mode

Tenacious outbound is built around **signal-grounded personalization**:

* Hiring signals
* AI maturity inference
* Competitor gap framing

If these signals are overstated:

* The system’s core differentiator becomes a liability
* The buyer perceives **poor research rather than low personalization**
* Trust is damaged before a real conversation begins

A wrong signal is strictly worse than a generic message because it signals **confident but incorrect reasoning**.

---

## Expected failure mechanism

1. Weak or stale evidence is treated as strong signal
2. Agent asserts a confident claim
3. Buyer challenges the claim
4. Agent fails to downgrade confidence or retract appropriately
5. Buyer loses trust and disengages

---

## Why not prioritize other failures

### Multi-thread leakage

* Higher severity per incident
* But primarily an **infrastructure / isolation problem**, not a language-level failure
* Less addressable via Act IV reasoning mechanisms

### Bench over-commitment

* High severity but **low frequency**
* Solvable via deterministic gating (policy constraint)
* Does not affect most outbound interactions

---

## Act IV mechanism direction

Implement **signal-confidence-aware phrasing**:

* Every signal (hiring, AI maturity, competitor gap) carries a confidence score
* Low-confidence signals → cautious or exploratory language
* Conflicting signals → explicit acknowledgment
* Missing evidence → abstention instead of inference
* Gap claims framed as:

  * “no public signal observed”
  * never “you are behind”

When challenged:

* Confidence must be downgraded
* Tone must remain neutral and non-defensive

---

## Success metrics

Primary:

* **Signal honesty pass rate** on held-out probe traces

Secondary:

* Reply-quality score
* Tone preservation under challenge
* Cost per generated outbound message
* Abstention rate on ambiguous signals

---

## Hypothesis

A signal-confidence-aware phrasing mechanism will outperform the baseline because it:

* Targets the **highest-frequency, highest-cost failure**
* Preserves trust in Tenacious’s core differentiator
* Reduces reputational risk without sacrificing personalization quality

---


