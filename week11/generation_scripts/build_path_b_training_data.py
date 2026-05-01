import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "tenacious_bench_v0.1"
OUT_DIR = ROOT / "training_data" / "path_b_preference"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(123)

PARTITIONS = ["train", "dev"]

GOOD_TEMPLATES = {
    "weak_signal_overassertion": """Subject: Question: is hiring demand higher than the public roles suggest?

Hi {name},
I saw {company} has {roles} open {stack} roles. I cannot tell from the outside whether that reflects the full hiring queue or only the public portion.
Tenacious supports managed {stack} engineering teams when the queue is larger than the posts suggest.
If the real demand is higher, would 15 minutes next week be useful?
Best,
Yabi""",

    "bench_overcommitment": """Subject: Re: {stack} engineering capacity

Hi {name},
Thanks for the context. I do not want to overcommit from email.
Based on current available capacity, the responsible next step is a scoping call with a Tenacious delivery lead to confirm stack, timeline, and availability before we commit numbers.
If the timeline is firm, I can route this today.
Best,
Yabi""",

    "pricing_violation": """Subject: Re: pricing scope

Hi {name},
I can share public pricing bands, but I should not quote a full multi-phase contract value from email.
A specific quote depends on stack, seniority, overlap, delivery-lead involvement, and timeline. The clean path is a short scoping call with our delivery lead.
Would you like me to send that calendar?
Best,
Yabi""",

    "banned_phrase": """Subject: Context: engineering capacity

Hi {name},
I saw the public signal around {company}'s {stack} hiring. If that reflects a larger delivery queue, Tenacious can support managed engineering capacity while your full-time search continues.
Would 15 minutes next week be useful to compare the need against available capacity?
Best,
Yabi""",

    "generic_template": """Subject: Context: {company}'s {stack} hiring

Hi {name},
I saw {company} has {roles} public {stack} roles. If those roles reflect a larger delivery queue, Tenacious can support managed engineering capacity while your hiring process continues.
If the public roles are the full demand, ignore this. If not, would 15 minutes be useful?
Best,
Yabi""",

    "condescending_gap": """Subject: Question: {company}'s AI roadmap

Hi {name},
I saw signals that some adjacent teams are investing in AI or ML platform capacity. I cannot tell from the outside whether {company} has already scoped that work or intentionally deferred it.
If it is on the roadmap, Tenacious can support a bounded discovery scope before a larger build.
Would a short comparison of options be useful?
Best,
Yabi""",

    "fabricated_signal": """Subject: Question: {company}'s engineering plans

Hi {name},
I do not want to assume anything beyond the public signal. I saw {roles} open {stack} roles and wanted to ask whether that reflects a larger delivery need.
If you are already covered, ignore this. If the queue is larger than the public roles, would 15 minutes next week be useful?
Best,
Yabi""",

    "multi_ask": """Subject: Question: {stack} capacity

Hi {name},
I saw {company}'s public {stack} hiring signal and wanted to ask one thing: is the delivery queue larger than the public roles suggest?
If yes, Tenacious can compare the need against available managed engineering capacity.
Would 15 minutes next week be useful?
Best,
Yabi""",

    "ai_maturity_misroute": """Subject: Question: first AI function

Hi {name},
Given {company}'s current public signals, I would not assume a production agentic-systems roadmap.
If AI is on the next twelve-month roadmap, the practical first step may be a scoped data or ML platform assessment rather than a full MLOps function.
Would a short comparison of first-step options be useful?
Best,
Yabi""",

    "missing_signal_reference": """Subject: Context: {company}'s {stack} hiring

Hi {name},
I saw {company} has {roles} open {stack} roles. I cannot tell from the outside whether that is the full demand or a public slice of a larger queue.
If the need is larger, Tenacious can support managed engineering capacity while your search continues.
Would 15 minutes next week be useful?
Best,
Yabi""",
}


def load_tasks(partition):
    rows = []
    for path in sorted((DATASET / partition).glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            task = json.load(f)
        rows.append(task)
    return rows


def get_context(task):
    inp = task.get("input", {})
    if not isinstance(inp, dict):
        inp = {}

    brief = inp.get("hiring_signal_brief", {})
    if not isinstance(brief, dict):
        brief = {}

    company = inp.get("company") or inp.get("prospect_company") or "your company"
    name = inp.get("prospect_name") or inp.get("name") or "there"

    return {
        "name": name,
        "company": company,
        "stack": brief.get("primary_stack", "engineering"),
        "roles": brief.get("role_count", "several"),
    }


def make_prompt(task):
    inp = task.get("input", {})
    rubric = task.get("rubric", {})

    return json.dumps(
        {
            "instruction": (
                "Evaluate or rewrite Tenacious prospect outreach. Preserve the Tenacious voice: "
                "direct, grounded, honest, professional, and non-condescending. "
                "Avoid banned phrases, unsupported claims, pricing fabrication, overcommitment, "
                "and multi-ask outreach."
            ),
            "task_input": inp,
            "rubric": rubric,
        },
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def make_chosen(task):
    fm = task.get("failure_mode", "missing_signal_reference")
    template = GOOD_TEMPLATES.get(fm, GOOD_TEMPLATES["missing_signal_reference"])
    return template.format(**get_context(task))


def make_pair(task):
    return {
        "id": task.get("task_id"),
        "failure_mode": task.get("failure_mode"),
        "source_mode": task.get("source_mode"),
        "prompt": make_prompt(task),
        "chosen": make_chosen(task),
        "rejected": task.get("candidate_output", ""),
        "metadata": {
            "path": "B",
            "training_objective": "preference_judge_or_critic",
            "chosen_source": "rule_based_tenacious_rewrite",
            "rejected_source": "benchmark_candidate_output",
        },
    }


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    train_tasks = load_tasks("train")
    dev_tasks = load_tasks("dev")

    train_pairs = [make_pair(t) for t in train_tasks]
    dev_pairs = [make_pair(t) for t in dev_tasks]

    random.shuffle(train_pairs)
    random.shuffle(dev_pairs)

    write_jsonl(OUT_DIR / "train_preferences.jsonl", train_pairs)
    write_jsonl(OUT_DIR / "dev_preferences.jsonl", dev_pairs)

    card = {
        "path": "B",
        "format": "preference_pairs",
        "train_pairs": len(train_pairs),
        "dev_pairs": len(dev_pairs),
        "excluded_partition": "held_out",
        "notes": [
            "Held-out tasks are not used for training data construction.",
            "Rejected responses come from benchmark candidate outputs.",
            "Chosen responses are rule-based Tenacious-compliant rewrites.",
        ],
    }

    with (OUT_DIR / "training_data_card.json").open("w", encoding="utf-8") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)

    print(f"Wrote train pairs: {len(train_pairs)}")
    print(f"Wrote dev pairs:   {len(dev_pairs)}")
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
