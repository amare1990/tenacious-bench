
---

# ACT III Implementation

### `failure_taxonomy.md`

# Failure Taxonomy — Act III

## Tier 1: Deal-Killing Trust Failures

These failures create immediate reputational or confidentiality risk.

* **Multi-thread leakage:** P-015, P-016, P-017
* **Bench over-commitment:** P-009, P-010, P-011
* **Severe signal over-claiming:** P-005, P-006, P-007, P-008

**Why it matters:** Tenacious sells trust, judgment, and delivery confidence. These failures can end a deal before discovery.

## Tier 2: High-Cost Commercial Misalignment

These failures misread the buyer's business situation or purchasing context.

* **ICP misclassification:** P-001, P-002, P-003, P-004
* **Dual-control coordination:** P-021, P-022, P-023
* **Gap over-claiming:** P-030, P-031, P-032

**Why it matters:** These errors reduce qualified reply rates and increase sales-cycle waste.

## Tier 3: Conversation Quality and Conversion Degradation

These failures do not always kill a deal, but they erode reply quality and buyer confidence.

* **Tone drift:** P-012, P-013, P-014
* **Scheduling edge cases:** P-024, P-025, P-026

**Why it matters:** Tenacious outbound depends on precise, respectful, executive-grade communication.

## Tier 4: Unit-Economics and Governance Failures

These failures increase cost or expose internal process details.

* **Cost pathology:** P-018, P-019, P-020
* **Signal reliability defects:** P-027, P-028, P-029

**Why it matters:** These degrade cost per qualified lead and make scaled deployment harder to govern.

---

# Category-to-Business-Cost Mapping

| Category                  | Primary cost                                   |    Severity |
| ------------------------- | ---------------------------------------------- | ----------: |
| Multi-thread leakage      | Confidentiality breach, deal loss              |   Very high |
| Bench over-commitment     | Delivery failure, commercial misrepresentation |   Very high |
| Signal over-claiming      | Brand damage, lower trust                      |        High |
| ICP misclassification     | Wrong pitch, lower reply rate                  |        High |
| Gap over-claiming         | CTO defensiveness, reputational harm           |        High |
| Dual-control coordination | Stalled threads or false commitments           | Medium-high |
| Tone drift                | Lower executive credibility                    | Medium-high |
| Scheduling edge cases     | Operational friction                           |      Medium |
| Cost pathology            | Higher CPL, worse margins                      |      Medium |
| Signal reliability        | Segmentation error, false confidence           | Medium-high |

---

