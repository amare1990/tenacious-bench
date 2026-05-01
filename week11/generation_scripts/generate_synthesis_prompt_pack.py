import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "generation_scripts" / "synthesis_prompt_pack"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FAILURE_MODES = [
    "weak_signal_overassertion",
    "bench_overcommitment",
    "pricing_violation",
    "banned_phrase",
    "generic_template",
    "condescending_gap",
    "fabricated_signal",
    "multi_ask",
    "ai_maturity_misroute",
    "missing_signal_reference",
]

BASE_PROMPT = """
Generate 5 Tenacious sales-evaluation benchmark tasks.

Return JSON only: a list of 5 objects.

Each task must contain:
- source_mode: "synthesis"
- failure_mode: "{failure_mode}"
- difficulty: "medium" or "hard"
- input:
  - company
  - prospect_name
  - prospect_title
  - icp_segment
  - hiring_signal_brief
  - bench_summary
  - pricing_policy
- candidate_output: a BAD outreach draft that violates exactly this failure mode: {failure_mode}
- rubric:
  - max_score: 10
  - expected_failure: "{failure_mode}"
  - checks:
    - specific_signal_grounded
    - confidence_aware_phrasing_required
    - banned_phrase_check
    - no_external_bench_language
    - no_capacity_overcommitment
    - no_pricing_fabrication
    - single_ask
    - non_condescending

Tenacious rules:
- Cold outreach body max 120 words.
- No "bench" in prospect-facing copy.
- No banned phrases: world-class, top talent, quick chat, synergy, 10x, circling back.
- Weak signals require questions, not assertions.
- Do not fabricate funding, layoffs, role counts, or leadership changes.
- Do not quote total contract value.
- Do not overcommit engineers beyond bench_summary.
- Do not frame prospect as behind or incompetent.

Make tasks realistic and diverse.
""".strip()


def main():
    for i, failure_mode in enumerate(FAILURE_MODES):
        prompt = BASE_PROMPT.format(failure_mode=failure_mode)
        out = OUT_DIR / f"synthesis_prompt_{i:02d}_{failure_mode}.txt"
        out.write_text(prompt, encoding="utf-8")

    print(f"Wrote {len(FAILURE_MODES)} synthesis prompts to {OUT_DIR}")


if __name__ == "__main__":
    main()
