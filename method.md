# Act IV Method: Risk-Weighted Evidence Policy Router

## Target failure mode

The target failure mode is **signal over-claiming that cascades into bench over-commitment and brand risk**. This is the highest-ROI failure from Act III because one wrong Tenacious claim can damage a CTO/founder relationship before a human delivery lead ever joins the conversation. It also compounds downstream: unsupported signal claims create the wrong ICP pitch, trigger defensive replies, and tempt the agent to promise capacity before the bench summary supports it.

## Mechanism

The implemented mechanism is a deterministic policy router around the outreach/follow-up layer. It converts each reply into a small set of business-risk gates before any response is released:

1. **Confidence-aware phrasing gate** — weak public evidence is phrased as a question or hypothesis, never as a claim.
2. **Bench-gated commitment policy** — staffing numbers, start dates, and capability commitments require a bench check and delivery-lead confirmation.
3. **Competitor-gap tone guard** — competitor comparisons are framed as operating patterns, not as assertions that a prospect is behind peers.
4. **Thread-isolation rule** — multi-contact conversations at the same company cannot reference another contact unless the prospect introduced it.
5. **Timezone scheduling gate** — calendar offers require explicit timezone confirmation and zone-labeled options.
6. **Cost-bounded response rule** — adversarial prompts receive short bounded answers; no open-ended research loop is started inside the reply path.

The full local evaluation harness is in `eval/act4/run_act4_eval.py`.

## Conditions evaluated

- **Day-1 baseline**: generic sales follow-up behavior without policy gates.
- **Automated-optimization baseline**: keyword-optimized guardrail responder with no explicit Tenacious business-cost weighting.
- **Full method**: the policy router above, evaluated on the same deterministic 20-probe held-out slice from the Act III probe library.

## Results

See `ablation_results.json` and `held_out_traces.jsonl`.

| Condition | n | pass@1 | 95% CI | Cost/task | p95 latency |
|---|---:|---:|---|---:|---:|
| Day-1 baseline | 20 | 0.40 | [0.219, 0.613] | $0.002 | 0.54s |
| Automated optimization baseline | 20 | 0.40 | [0.219, 0.613] | $0.006 | 0.95s |
| Full method | 20 | 1.00 | [0.839, 1.000] | $0.004 | 0.73s |

## Statistical test

Delta A = full method − Day-1 baseline = **+0.60 pass@1**. A two-proportion z-test gives `z = 4.14`, two-sided `p = 0.00003`, one-sided `p = 0.00002`. This passes the Act IV requirement that Delta A be positive with `p < 0.05`.

Delta B = full method − automated optimization baseline = **+0.60 pass@1** on the same compute budget class. The method is also cheaper than the automated baseline in this local harness because it avoids an extra optimization/model pass.

Delta C = full method − published tau2 reference proxy = **+0.58** using the challenge's published retail ceiling proxy of 0.42 as informational context only.

## Limitations

This is a local sealed-slice simulation derived from the Act III probe library, not the official program-held sealed partition. The harness is intentionally deterministic and transparent so the official scorer can replace the task file while preserving the same condition interfaces. The next hardening step is to wire the same gates directly into the live reply handler and rerun against official held-out tasks.
