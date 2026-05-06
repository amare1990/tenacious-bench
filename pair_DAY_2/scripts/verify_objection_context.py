import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent.email_agent import generate_followup_email


class FakeAnalysis:
    reply_type = "objection"

    def model_dump(self):
        return {
            "reply_type": "objection",
            "reply_text": "Why did you think we were hiring aggressively?",
            "probe_id": "P-005",
            "category": "signal_overclaiming",
            "context": {
                "confidence": "low",
                "signals": ["weak public hiring signal"],
            },
        }


if __name__ == "__main__":
    analysis = FakeAnalysis()
    result = generate_followup_email(
        "ProbeCo",
        analysis,
        context=analysis.model_dump(),
        policy_result={
            "tone_mode": "exploratory",
            "claim_strength": "soft",
            "allow_capacity_language": False,
        },
    )

    print(result["source"])
    print(result["body"])
    assert result["source"] == "constraint_checked_objection"
    assert "Constraint check:" in result["body"]
    assert "Avoid generic sales fallback" in result["body"]
    assert "do not overclaim" in result["body"]