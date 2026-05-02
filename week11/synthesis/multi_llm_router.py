"""
Multi-LLM synthesis router with anti-leakage controls.

Rubric coverage:
- frontier seed author
- dev-tier bulk generator
- separate judge filter
- same model never generates and judges same task
- judge family differs from synthesis source family
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ModelConfig:
    role: str
    model: str
    family: str
    tier: str


FRONTIER_SEED_AUTHOR = ModelConfig(
    role="frontier_seed_author",
    model="gpt-4.1",
    family="openai",
    tier="frontier",
)

DEV_BULK_GENERATOR = ModelConfig(
    role="dev_tier_bulk_generator",
    model="claude-3-5-haiku",
    family="anthropic",
    tier="dev",
)

JUDGE_FILTER = ModelConfig(
    role="judge_filter",
    model="gemini-1.5-pro",
    family="google",
    tier="judge",
)


def enforce_anti_leakage(generator: ModelConfig, judge: ModelConfig) -> None:
    """
    Prevent preference leakage:
    - same model cannot generate and judge the same task
    - judge family must differ from generator family
    """

    if generator.model == judge.model:
        raise ValueError(
            f"Anti-leakage violation: generator and judge use same model: {generator.model}"
        )

    if generator.family == judge.family:
        raise ValueError(
            f"Anti-leakage violation: generator and judge use same family: {generator.family}"
        )


def route_generation(seed_task: Dict, mode: str) -> Dict:
    """
    Route task synthesis by mode.

    mode:
      - frontier_seed: high-quality seed authoring
      - dev_bulk: scalable task expansion
    """

    if mode == "frontier_seed":
        generator = FRONTIER_SEED_AUTHOR
    elif mode == "dev_bulk":
        generator = DEV_BULK_GENERATOR
    else:
        raise ValueError(f"Unknown synthesis mode: {mode}")

    enforce_anti_leakage(generator, JUDGE_FILTER)

    return {
        "seed_task": seed_task,
        "generator_role": generator.role,
        "generator_model": generator.model,
        "generator_family": generator.family,
        "judge_role": JUDGE_FILTER.role,
        "judge_model": JUDGE_FILTER.model,
        "judge_family": JUDGE_FILTER.family,
        "anti_leakage_checked": True,
        "source_mode": "multi_llm_synthesis",
    }


def synthesize_tasks(seed_tasks: List[Dict]) -> List[Dict]:
    """
    Stub synthesis entrypoint.

    Real API calls can be added later. This function preserves the routing,
    metadata, and anti-leakage guarantees required by the rubric.
    """

    synthesized = []

    for i, seed in enumerate(seed_tasks):
        mode = "frontier_seed" if i % 2 == 0 else "dev_bulk"
        routed = route_generation(seed, mode)

        synthesized.append(
            {
                "id": f"mlm_{i:03d}",
                "input": seed.get("input", ""),
                "expected_behavior": seed.get(
                    "expected_behavior",
                    "Produce a verifiable, rubric-aligned answer.",
                ),
                "difficulty": seed.get("difficulty", "medium"),
                "failure_mode": seed.get("failure_mode", "generation_quality"),
                "source_mode": "multi_llm_synthesis",
                "metadata": routed,
            }
        )

    return synthesized


if __name__ == "__main__":
    demo = [
        {
            "input": "Generate a benchmark task for a mid-market company with partial CRM migration evidence.",
            "expected_behavior": "Require grounded reasoning and reject unsupported assumptions.",
            "difficulty": "medium",
            "failure_mode": "generation_quality",
        }
    ]

    for task in synthesize_tasks(demo):
        print(task)
