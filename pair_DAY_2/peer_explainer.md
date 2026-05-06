# Why Tool Outputs Get Ignored: What Your Tenacious-Bench System Actually Shows

## The Question

Inside a modern tool-using agent, what determines whether a tool output actually shapes the model's response — versus being present in the context but having no real effect on what gets generated?

Amare saw this in his `tenacious-bench` system: probes were supplying structured constraints — failure category, hiring signal, tone flags, overcommitment warnings — and the agent was producing generic outputs as if the context never arrived. After looking at the actual code, the answer is sharper than the abstract mechanism. There are two separate failures happening, and only one of them is about the LLM ignoring context.

---

## What the Code Actually Shows

### Failure One: The Probe Context Never Reaches the Model

In `eval/probes/run_probes.py`, the probe evaluation harness builds a `FakeAnalysis` object:

```python
class FakeAnalysis:
    reply_type = "objection"

    def model_dump(self):
        return {
            "reply_type": self.reply_type,
            "reply_text": probe["input"],
            "probe_id": probe["id"],
            "category": probe["category"],
            "context": probe.get("context", {}),  # confidence: low, signals, etc.
        }

followup = generate_followup_email(
    company_name="ProbeCo",
    analysis=FakeAnalysis(),
)
```

The `context` field — which contains `confidence: low`, the weak signal evidence, the failure category — is attached to `FakeAnalysis.model_dump()`. But `generate_followup_email()` in `email_agent.py` never passes this context to the LLM. It reads `reply_type` and routes to a template. The structured constraints exist in the test harness but are invisible to the model.

This is why all 32 probes in `probe_trace_log.json` return the same output:

```
"output": "Re: ProbeCo\n\nUnderstood. Thanks for the reply."
```

That is not the LLM ignoring context. That is a code-level fallback firing every time because `generate_followup_email()` has no case for `reply_type = "objection"`:

```python
# email_agent.py
if analysis.reply_type == 'interested':   return { ... }
if analysis.reply_type == 'information_request': return { ... }
if analysis.reply_type == 'defer':        return { ... }
if analysis.reply_type == 'unclear':      return { ... }
# no objection case — falls through to:
return {'subject': f'Re: {company_name}', 'body': 'Understood. Thanks for the reply.', 'source': 'fallback'}
```

The model is never called. The generic output is hardcoded. This is the root cause of the probe results.

---

### Failure Two: Policy Constraints Are Advisory Text, Not Binding Instructions

For the cases where the LLM is called — in `email_agent.py`'s `_generate_email_with_llm()` — the policy constraints are serialised as plain text key-value pairs:

```python
user_prompt = f"""
Company: {company.company_name}
...
Tone mode: {policy_result['tone_mode']}
Claim strength: {policy_result['claim_strength']}
""".strip()
```

The model sees `Tone mode: exploratory` and `Claim strength: soft` as unstructured lines in a user message. These are not tool outputs. They are not schema-validated. They carry the same weight as any other text in the prompt — which means the model's pretraining prior for "what a good B2B sales email looks like" competes directly with them and frequently wins.

This is the real LLM-context-ignoring problem. And here is the mechanism behind it.

---

## The Load-Bearing Mechanism

The model generates each token by sampling the highest-probability continuation of its context. It has two competing signals:

1. **Pretraining prior**: strong statistical patterns from millions of B2B sales emails. The model has a well-learned distribution for what a qualifying outreach sounds like.
2. **Prompt guidance**: `Tone mode: exploratory`, `Claim strength: soft`.

When the model is not forced to generate reasoning tokens that explicitly reference the constraint before writing the response body, the pretraining prior dominates. The output matches the surface form of a policy-aware response while being driven entirely by the prior. The constraint is acknowledged; the reasoning trajectory is unchanged.

This is not a bug. It is how next-token prediction works. The path of highest probability does not require integrating a two-word label buried in a user prompt.

**The fix is forcing a scratchpad step.** The model must generate intermediate tokens that reference the constraint before generating the response. Here is the difference:

```python
# Current: advisory text — prior wins
user_prompt = f"""
...
Tone mode: {policy_result['tone_mode']}
Claim strength: {policy_result['claim_strength']}
Prospect reply: {prospect_reply}
"""

# Fixed: forced scratchpad — constraint enters the reasoning path
user_prompt = f"""
Policy:
- tone_mode: {policy_result['tone_mode']}
- claim_strength: {policy_result['claim_strength']}
- allow_capacity_language: {policy_result['allow_capacity_language']}

Prospect reply: {prospect_reply}

Before drafting, complete this:
Constraint check: Given tone_mode={policy_result['tone_mode']} and claim_strength={policy_result['claim_strength']}, I must [complete this sentence].

Response:
"""
```

The `Constraint check:` line forces the model to generate tokens that encode the policy into the probability distribution of everything that follows. The policy is no longer a passive label — it is a load-bearing token sequence the model must complete before producing the reply.

---

## Three Adjacent Concepts Worth Connecting

**1. Tool Schema Design — The Missing Layer**
Amare asked what role tool schema design plays in this failure. The honest answer from the code: his system has no tool schemas. `policy_result` is a Python dict serialised to plain text. A real tool schema changes this fundamentally. When a model is given an OpenAI-format tool definition with typed parameters, it must emit a structured JSON token sequence to invoke the tool — the schema forces the model into a specific generation path before it can produce the response. Plain-text labels carry no such forcing. The difference between `Tone mode: exploratory` and a typed `tone_mode` field in a tool schema is the difference between advice the model can ignore and a generation constraint it must satisfy to proceed. Amare's system skipped this layer entirely, which is why the constraint enforcement sits in the fallback rules rather than in the model's generation path.

**2. Lost in the Middle (Liu et al., 2023)**
Constraints buried mid-prompt between a long system prompt and the prospect reply sit in the position where attention weight is lowest. Moving policy constraints to the top of the user message — or repeating them immediately above the generation instruction — measurably improves integration without any architectural change.

**3. The ReAct Pattern and Validation (Yao et al., 2022)**
ReAct formalises the scratchpad fix above: interleaving `Thought:` and `Action:` steps forces the model to generate reasoning tokens before final output. The reasoning tokens are not decoration — they are the mechanism by which constraints get encoded into the probability distribution of the response. Because the LLM path is still probabilistic, a cheap second-pass judge call checking whether the response contradicts any boolean field in `policy_result` — `allow_capacity_language`, `require_handoff` — provides a hard verification layer on top. Amare's `policies.py` already computes these booleans. They are not currently used to validate output.

---

## What to Fix in the System

Three concrete changes, ordered by impact:

1. **Add the objection case** to `generate_followup_email()` in `email_agent.py`. Every probe currently fires the hardcoded fallback. The LLM is never called during probe evaluation.

2. **Pass probe context into the generation prompt**. In `run_probes.py`, `confidence`, `signals`, and `failure_category` exist on the `FakeAnalysis` context dict but never reach the model. Thread them through to the user prompt.

3. **Force a constraint check step** before the response body. Replace the plain-text `Tone mode: X` lines with a `Constraint check: [complete this]` prefix that the model must fill in before drafting.

---

## Sources

1. **Liu et al. (2023). "Lost in the Middle: How Language Models Use Long Contexts."** arXiv:2307.03172. Canonical empirical paper on position-dependent attention. Directly explains why `Tone mode: exploratory` mid-prompt carries less weight than the same constraint placed at the top of the message.

2. **Yao et al. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models."** arXiv:2210.03629. Original paper establishing interleaved reasoning-action traces as the mechanism for making retrieved context load-bearing. The scratchpad fix above is a direct application of this pattern.
