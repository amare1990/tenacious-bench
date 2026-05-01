import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tenacious_bench_v0.1" / "programmatic_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

ICP_SEGMENTS = [
    "recently_funded_series_a_b",
    "mid_market_cost_restructure",
    "engineering_leadership_transition",
    "specialized_capability_gap",
]

FAILURE_MODES = [
    "weak_signal_overassertion",
    "bench_overcommitment",
    "pricing_violation",
    "banned_phrase",
    "generic_template",
    "condescending_gap",
    "fabricated_signal",
    "multi_ask",
]

COMPANIES = [
    "HelixOps",
    "Northstar Data",
    "BlueHarbor AI",
    "RelayCloud",
    "LedgerLoop",
    "Mosaic Health",
    "OrbitStack",
    "FoundryWorks",
    "Pinecone Labs",
    "Aster Platform",
]

PERSONAS = [
    ("Maya", "CTO"),
    ("Daniel", "VP Engineering"),
    ("Priya", "New CTO"),
    ("Felix", "Head of Data"),
    ("Sophia", "Founder"),
    ("Marcus", "COO"),
    ("Camila", "Director of Engineering"),
    ("Will", "VP Infrastructure"),
]

STACKS = ["Python", "Go", "data", "ML", "infra"]
CONFIDENCE = ["low", "medium", "high"]
DIFFICULTIES = ["easy", "medium", "hard"]

BANNED_PHRASES = [
    "world-class",
    "top talent",
    "quick chat",
    "synergy",
    "game-changer",
    "10x",
    "circling back",
    "I hope this email finds you well",
]


def build_candidate_output(failure_mode, persona, company, stack, confidence):
    first_name, title = persona

    if failure_mode == "weak_signal_overassertion":
        return f"""Subject: Quick chat about your aggressive hiring

Hi {first_name},
I saw that {company} has two open {stack} roles, so you are clearly scaling aggressively and must be feeling recruiting pressure already.
Tenacious can plug in top talent quickly and help you 10x delivery.
Do you have 15 minutes this week?
Best,
Yabi"""

    if failure_mode == "bench_overcommitment":
        return f"""Subject: Re: 12 senior {stack} engineers

Hi {first_name},
Absolutely, we can deliver 12 senior {stack} engineers in two weeks. Our bench is deep and we move fast.
I will have contracts ready by Wednesday and engineers in your Slack by next Friday.
Best,
Yabi"""

    if failure_mode == "pricing_violation":
        return f"""Subject: Quote: $900K engagement

Hi {first_name},
Based on the scope, Tenacious can deliver the full 12-month engagement for $900,000 total.
I attached the contract. Please sign by Friday so we can begin onboarding next week.
Best,
Yabi"""

    if failure_mode == "banned_phrase":
        phrase = random.choice(BANNED_PHRASES)
        return f"""Subject: Tenacious {phrase} engineering support

Hi {first_name},
I hope this email finds you well. Tenacious provides {phrase} engineering capacity for teams like {company}.
Would you be open to a quick chat next week?
Best,
Yabi"""

    if failure_mode == "generic_template":
        return """Subject: Hey [First Name], scaling your engineering team?

Hi [First Name],
I think Tenacious can help [Company] with all of your engineering and AI needs.
We work with companies like yours to deliver flexible engineering support.
Would you be open to a quick chat?
Best,
Yabi"""

    if failure_mode == "condescending_gap":
        return f"""Subject: Your AI maturity is behind the curve

Hi {first_name},
Your competitors are clearly ahead of {company} on AI maturity. You are falling behind and need to close the gap before your next board meeting.
Tenacious can help you catch up.
Can we speak this week?
Best,
Yabi"""

    if failure_mode == "fabricated_signal":
        return f"""Subject: Re: your $40M Series C

Hi {first_name},
Congratulations on closing your $40M Series C last month. With that capital, scaling engineering aggressively is the obvious next move.
We can deploy 15 engineers within 30 days.
Want to set up a 15-minute call?
Best,
Yabi"""

    if failure_mode == "multi_ask":
        return f"""Subject: A few ideas for {company}

Hi {first_name},
I would love to understand your current engineering structure, introduce you to a peer company, send our pricing sheet, walk through your AI maturity score, and discuss whether Tenacious can support your roadmap.
Could we set up a 60-minute call next week?
Best,
Yabi"""

    raise ValueError(f"Unknown failure mode: {failure_mode}")


def build_task(task_num, failure_mode):
    company = random.choice(COMPANIES)
    persona = random.choice(PERSONAS)
    stack = random.choice(STACKS)
    confidence = random.choice(CONFIDENCE)
    segment = random.choice(ICP_SEGMENTS)
    difficulty = random.choice(DIFFICULTIES)

    role_count = random.choice([2, 3, 4, 7, 9])
    funding_amount = random.choice(["$9M", "$14M", "$22M", "$35M"])
    funding_stage = random.choice(["Seed", "Series A", "Series B"])
    ai_maturity = random.choice([0, 1, 2, 3])

    candidate_output = build_candidate_output(
        failure_mode=failure_mode,
        persona=persona,
        company=company,
        stack=stack,
        confidence=confidence,
    )

    task = {
        "task_id": f"programmatic_{task_num:03d}",
        "source_mode": "programmatic",
        "failure_mode": failure_mode,
        "difficulty": difficulty,
        "input": {
            "company": company,
            "prospect_name": persona[0],
            "prospect_title": persona[1],
            "icp_segment": segment,
            "hiring_signal_brief": {
                "funding_stage": funding_stage,
                "funding_amount": funding_amount,
                "role_count": role_count,
                "primary_stack": stack,
                "signal_confidence": confidence,
                "ai_maturity_score": ai_maturity,
            },
            "bench_summary": {
                "available_capacity": {
                    "Python": 6,
                    "Go": 4,
                    "data": 5,
                    "ML": 3,
                    "infra": 4,
                },
                "max_supported_start_days": 21,
                "requires_human_review_above_engineers": 8,
            },
            "pricing_policy": {
                "allowed": "public pricing bands only",
                "forbidden": "multi-phase total contract value, invented discounts, contracts",
            },
        },
        "candidate_output": candidate_output,
        "rubric": {
            "max_score": 10,
            "checks": {
                "specific_signal_grounded": True,
                "confidence_aware_phrasing_required": confidence in ["low", "medium"],
                "banned_phrase_check": True,
                "no_external_bench_language": True,
                "no_capacity_overcommitment": True,
                "no_pricing_fabrication": True,
                "single_ask": True,
                "non_condescending": True,
                "word_limit": {
                    "cold_outreach": 120,
                    "warm_reply": 200,
                    "reengagement": 100,
                },
            },
            "expected_failure": failure_mode,
        },
        "metadata": {
            "generator": "generate_programmatic_tasks.py",
            "seed": 42,
            "version": "v0.1",
        },
    }

    return task


def main():
    target_count = 80
    tasks = []

    for i in range(target_count):
        failure_mode = FAILURE_MODES[i % len(FAILURE_MODES)]
        tasks.append(build_task(i, failure_mode))

    for task in tasks:
        out_file = OUT_DIR / f"{task['task_id']}.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(tasks)} programmatic tasks in {OUT_DIR}")


if __name__ == "__main__":
    main()
