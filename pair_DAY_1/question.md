
---

# Question


* The model frequently produces **generic fallback responses**, such as:

  > “Tenacious can provide offshore engineers quickly. Would you like a 30-minute call?”
* These responses often **ignore the input constraints** (e.g., hiring nuance, overcommitment, tone challenges)
* In some cases, these responses are even marked as **passed**, despite failing to address the underlying reasoning task

**My question is:**

> What mechanism causes an LLM-based sales agent (or judge) to collapse to generic high-probability fallback responses across diverse failure categories, and how do the training data distribution, prompt structure, and evaluation criteria interact to either reinforce or fail to penalize this behavior?

More concretely:

* Why does the model ignore structured signals like ICP nuance, constraint violations, and conversational context?
* Why does a single generic response pattern appear across multiple failure categories?
* How can evaluation frameworks (like mine) fail to consistently penalize this collapse?

**Grounding in my work:**

Answering this would directly impact:

* How I design prompts and guardrails in the conversion engine
* How I structure evaluation logic in `held_out_traces.jsonl`
* Whether my system is actually measuring reasoning quality or just response fluency
* How I prevent production systems from defaulting to generic “salesy” outputs

**Why this matters beyond my project:**

This failure mode is critical for any FDE system using LLMs for:

* Sales automation
* Agent reasoning
* LLM-as-a-judge evaluation

If generic fallback behavior is not properly understood and penalized:

* Systems appear to perform well while failing real tasks
* Evaluation metrics become misleading
* Production agents degrade into shallow, repetitive behavior

**What a good answer should clarify:**

A strong explainer should:

* Identify why LLMs default to **high-probability generic responses**
* Explain how **training objectives and decoding** contribute to this collapse
* Show how **evaluation design can mask or expose the issue**
* Provide concrete strategies to **detect, measure, and mitigate fallback behavior**
