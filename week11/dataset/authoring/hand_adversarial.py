# week11/dataset/authoring/hand_adversarial.py

from typing import List, Dict

def generate_hand_adversarial_tasks() -> List[Dict]:
    """
    Hand-authored adversarial tasks designed to stress:
    - conflicting constraints
    - ambiguous inputs
    - edge-case reasoning
    """

    tasks = [
        {
            "id": "adv_001",
            "input": "Company has 0 employees but reports enterprise-scale infra. Recommend stack.",
            "expected_behavior": "Detect inconsistency and request clarification.",
            "difficulty": "hard",
            "failure_mode": "inconsistency",
            "source_mode": "hand_adversarial",
        },
        {
            "id": "adv_002",
            "input": "Optimize cost with unlimited budget constraint.",
            "expected_behavior": "Flag contradictory objective.",
            "difficulty": "medium",
            "failure_mode": "constraint_conflict",
            "source_mode": "hand_adversarial",
        },
        {
            "id": "adv_003",
            "input": "Given partial schema and missing keys, produce validated output.",
            "expected_behavior": "Handle missing fields safely or abstain.",
            "difficulty": "hard",
            "failure_mode": "schema_violation",
            "source_mode": "hand_adversarial",
        },
    ]

    return tasks


if __name__ == "__main__":
    tasks = generate_hand_adversarial_tasks()
    for t in tasks:
        print(t)
