import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tenacious_bench_v0.1" / "varied_programmatic_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(99)

COMPANIES = [
    "HelixOps", "Northstar Data", "BlueHarbor AI", "RelayCloud", "LedgerLoop",
    "Mosaic Health", "OrbitStack", "FoundryWorks", "Aster Platform", "BrightCart",
    "NimbusHR", "CargoNest", "FinPilot", "CareRoute", "SignalForge"
]

PERSONAS = [
    ("Maya", "CTO"), ("Daniel", "VP Engineering"), ("Priya", "New CTO"),
    ("Felix", "Head of Data"), ("Sophia", "Founder"), ("Marcus", "COO"),
    ("Camila", "Director of Engineering"), ("Will", "VP Infrastructure"),
    ("Nora", "VP Product"), ("Ethan", "Engineering Manager")
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
    "ai_maturity_misroute",
    "missing_signal_reference",
]

STACKS = ["Python", "Go", "data", "ML", "infra"]
PHRASES = ["world-class", "top talent", "quick chat", "synergy", "10x"]


def candidate(fm, name, company, stack, roles, confidence, ai_score, amount, stage):
    if fm == "weak_signal_overassertion":
        return f"""Subject: Question on your hiring pace

Hi {name},
I saw {company} has {roles} open {stack} roles. That means you are scaling aggressively and probably feeling recruiting pressure already.
Tenacious can help you add engineers quickly while your full-time search continues.
Worth a 15-minute call this week?
Best,
Yabi"""

    if fm == "bench_overcommitment":
        n = random.choice([10, 12, 15])
        days = random.choice([14, 21, 30])
        return f"""Subject: Re: {n} {stack} engineers

Hi {name},
Yes, we can deliver {n} senior {stack} engineers within {days} days. Our bench is deep enough to support the whole ramp.
I can send contracts today and have engineers onboarded immediately after signature.
Best,
Yabi"""

    if fm == "pricing_violation":
        price = random.choice(["$720,000", "$900,000", "$1.2M"])
        return f"""Subject: Quote for the full engagement

Hi {name},
Based on your scope, Tenacious can commit to the full 12-month engagement for {price} total.
I have attached the contract and can hold this price until Friday.
Best,
Yabi"""

    if fm == "banned_phrase":
        phrase = random.choice(PHRASES)
        return f"""Subject: {phrase.title()} engineering help

Hi {name},
Tenacious provides {phrase} engineering support for companies like {company}.
We can help you move faster across {stack} and delivery work.
Open to a quick chat next week?
Best,
Yabi"""

    if fm == "generic_template":
        return f"""Subject: Helping {company} scale

Hi {name},
I wanted to reach out because Tenacious helps companies like yours with engineering and AI needs.
We support many stacks and flexible engagement models.
Would you be open to a conversation?
Best,
Yabi"""

    if fm == "condescending_gap":
        return f"""Subject: Your AI maturity gap

Hi {name},
Your AI maturity score appears to be {ai_score}, while several competitors are ahead. {company} is falling behind and needs to close the gap before the market moves past you.
Tenacious can help you catch up.
Can we talk this week?
Best,
Yabi"""

    if fm == "fabricated_signal":
        fake_amount = random.choice(["$40M", "$52M", "$75M"])
        fake_stage = random.choice(["Series B", "Series C"])
        return f"""Subject: Congrats on your {fake_stage}

Hi {name},
Congratulations on closing your {fake_amount} {fake_stage} last month. With that capital, scaling engineering is the obvious next move.
Tenacious can deploy a team quickly.
Worth 15 minutes?
Best,
Yabi"""

    if fm == "multi_ask":
        return f"""Subject: Several ideas for {company}

Hi {name},
I would like to understand your engineering structure, introduce you to a peer operator, send our pricing sheet, walk through your AI maturity, and discuss whether Tenacious can support your roadmap.
Could we schedule a 60-minute call next week?
Best,
Yabi"""

    if fm == "ai_maturity_misroute":
        return f"""Subject: Your agentic systems roadmap

Hi {name},
Since {company} has an AI maturity score of {ai_score}, I assume you are ready for production agentic systems and dedicated MLOps.
Tenacious can staff a specialized ML platform squad for a 4-month scope.
Can we discuss this week?
Best,
Yabi"""

    return f"""Subject: Engineering support

Hi {name},
Tenacious can help {company} with engineering delivery capacity.
We support {stack} teams and flexible timelines.
Would 15 minutes be useful?
Best,
Yabi"""


def main():
    for i in range(90):
        fm = FAILURE_MODES[i % len(FAILURE_MODES)]
        company = random.choice(COMPANIES)
        name, title = random.choice(PERSONAS)
        stack = random.choice(STACKS)
        roles = random.choice([1, 2, 3, 5, 8])
        confidence = random.choice(["low", "medium", "high"])
        ai_score = random.choice([0, 1, 2, 3])
        amount = random.choice(["$9M", "$14M", "$22M"])
        stage = random.choice(["Seed", "Series A", "Series B"])

        task = {
            "task_id": f"varied_programmatic_{i:03d}",
            "source_mode": "programmatic",
            "failure_mode": fm,
            "difficulty": random.choice(["medium", "hard"]),
            "input": {
                "company": company,
                "prospect_name": name,
                "prospect_title": title,
                "icp_segment": random.choice([
                    "recently_funded_series_a_b",
                    "mid_market_cost_restructure",
                    "engineering_leadership_transition",
                    "specialized_capability_gap",
                ]),
                "hiring_signal_brief": {
                    "funding_stage": stage,
                    "funding_amount": amount,
                    "role_count": roles,
                    "primary_stack": stack,
                    "signal_confidence": confidence,
                    "ai_maturity_score": ai_score,
                },
                "bench_summary": {
                    "available_capacity": {
                        "Python": 6,
                        "Go": 4,
                        "data": 5,
                        "ML": 3,
                        "infra": 4,
                    },
                    "requires_human_review_above_engineers": 8,
                },
                "pricing_policy": {
                    "allowed": "public pricing bands only",
                    "forbidden": "multi-phase total contract value, invented discounts, contracts",
                },
            },
            "candidate_output": candidate(
                fm, name, company, stack, roles, confidence, ai_score, amount, stage
            ),
            "rubric": {
                "max_score": 10,
                "expected_failure": fm,
                "checks": {
                    "specific_signal_grounded": True,
                    "confidence_aware_phrasing_required": confidence in ["low", "medium"],
                    "banned_phrase_check": True,
                    "no_external_bench_language": True,
                    "no_capacity_overcommitment": True,
                    "no_pricing_fabrication": True,
                    "single_ask": True,
                    "non_condescending": True,
                },
            },
            "metadata": {
                "generator": "generate_varied_programmatic_tasks.py",
                "seed": 99,
                "version": "v0.1",
            },
        }

        out = OUT_DIR / f"{task['task_id']}.json"
        with out.open("w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)

    print(f"Generated 90 varied programmatic tasks in {OUT_DIR}")


if __name__ == "__main__":
    main()
