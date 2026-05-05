## `pair_DAY_1/grounding_commit.md`

# Grounding Commit

## Artifacts Updated

- `pair_DAY_1/scripts/detect_response_collapse.py`
- `pair_DAY_1/collapse_detector_result.md`
- Evaluation / judge criteria for held-out trace scoring

## Change

I added a response-collapse detector that computes pairwise semantic similarity across model outputs using sentence embeddings. The first version measured similarity globally across all 60 held-out responses. That produced an average similarity of `0.415`, which did not indicate global collapse.

After inspecting the traces, I refined the interpretation: the important failure is not global collapse across every response, but **template-level collapse within conditions**. The baseline condition repeatedly outputs:

> “Tenacious can provide offshore engineers quickly. Would you like a 30-minute call?”

across unrelated categories such as `signal_overclaiming`, `bench_overcommitment`, and `tone_drift`.

I also updated the evaluation criteria to include an explicit specificity rule.

## Before

The judge/evaluation criteria allowed responses to pass if they sounded fluent, professional, and broadly sales-appropriate. This allowed generic responses to pass even when they did not address the specific probe constraint.

For example, a response could sound polished while ignoring whether the input was testing overclaiming, tone drift, scheduling, signal reliability, or bench availability.

## After

The judge now includes an explicit specificity constraint:

> A response must directly address the specific constraint in the probe. If the same response could plausibly be used for multiple unrelated probes, assign FAIL.

The updated criteria also ask:

- Does the response reference the input constraint?
- Does the response use evidence from the prompt?
- Would this same response still make sense if the input changed?
- Does the response address the probe category rather than merely sounding professional?

## Why This Changed

Before this work, I treated the repeated Tenacious fallback response as a prompt-level issue. My partner’s explainer showed that the deeper mechanism is response-collapse: likelihood maximization and preference-style evaluation can reward high-probability, professional-sounding templates even when they fail the actual task.

Running the detector and inspecting traces showed that my initial “no collapse” conclusion was too broad. The system is not globally collapsed, but it does reuse templates within specific conditions. That means the failure is partly in generation and partly in evaluation design.

## What Improved

The system now has a measurable diagnostic for response collapse instead of relying on anecdotal examples. The evaluation criteria now enforce specificity and constraint engagement, not just fluency.

This improves the alignment between evaluation scores and real task performance:

- “Well-formed but generic” responses should now fail.
- “Constraint-aware” responses should pass.
- Condition-level template reuse is now visible instead of being hidden by a global average.


---


