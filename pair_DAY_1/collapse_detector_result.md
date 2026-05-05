
---

## `pair_DAY_1/collapse_detector_result.md`


# Collapse Detector Result

## Command

```bash
uv run python pair_DAY_1/scripts/detect_response_collapse.py
````

## Output

```json
{
  "num_responses": 60,
  "avg_pairwise_similarity": 0.415,
  "collapse_detected": false,
  "most_similar_pair": [49, 59]
}
```

## Interpretation

The first detector run did **not** show global response collapse across the entire held-out set. The average pairwise semantic similarity across all 60 responses was `0.415`, below the `0.90` collapse threshold.

However, this global score is misleading because the dataset mixes multiple behavioral regimes: `baseline`, `auto_optimization`, and `method`. When I inspected the traces by condition, the failure became clearer: collapse is not global across every response, but **template-level collapse within specific conditions**.

In the `baseline` condition, several traces from different failure categories produce the exact same fallback response:

> “Tenacious can provide offshore engineers quickly. Would you like a 30-minute call?”

Concrete examples include:

* `act4-baseline-002` — `signal_overclaiming`
* `act4-baseline-003` — `bench_overcommitment`
* `act4-baseline-004` — `tone_drift`

These are semantically different probes, but the model reused the same generic sales response. This confirms the core failure mode from my partner’s explainer: the model can fall back to a high-probability professional-sales template instead of addressing the specific constraint in the input.

The `auto_optimization` condition shows a softer version of the same behavior. The repeated template changes from the original Tenacious pitch to a safer phrase such as:

> “Thanks for the context. I can share a measured observation and avoid assuming more than the public signal supports.”

This is an improvement over the baseline, but it is still reusable across unrelated categories. It reduces obvious overclaiming while preserving generic template behavior.

The `method` condition is the strongest version. Outputs become more category-aware and often include a specific sentence tied to the probe category. However, even here the responses retain a templated structure:

> “Thanks for the context.”
> `[category-specific sentence]`
> “Useful next step: a brief exploratory call only if the signal and timing are relevant on your side.”

## Conclusion

The failure mode is not “the entire model always gives identical answers.” The more precise diagnosis is:

> The system learns reusable high-probability sales templates and applies them within conditions, while the evaluator does not consistently penalize lack of probe-specific engagement.

This explains why the global similarity score did not detect collapse: it averaged across multiple regimes and hid condition-level template reuse. The next evaluation improvement should therefore measure response collapse by condition and add a specificity rule that fails responses which could plausibly apply to unrelated probes.


---



