# Why your sales agent gives the same answer to every question

By Yonas Mekonnen

---

Amare noticed something strange in his evaluation results. His conversion engine kept producing this:

> "Tenacious can provide offshore engineers quickly. Would you like a 30-minute call?"

Not for one type of probe. For all of them. Weak-evidence overclaiming, unsupported staffing commitments, tone drift — different failure categories, same output. In some cases the judge marked it as passed.

This is not a prompt engineering problem. It is what likelihood maximization actually does at scale.

---

## Why the model always finds the same answer

LLMs are trained to predict the next token by maximizing log-likelihood. In a corpus of professional communication, certain phrases appear thousands of times across wildly different contexts: "Would you like to schedule a call?" "I'd be happy to help." They fit almost any business conversation, so they accumulate enormous probability mass. They are the statistical mode — the single most probable output the model has learned for professional inputs.

Greedy decoding makes this worse. At each step the model picks the most probable next token. Probability mass collapses onto that mode. This is what Holtzman et al. (2020) identified as degenerate text generation: optimize for likelihood and you get templates that fit everywhere and commit to nothing.

RLHF piles on. Reward models are trained on human preference ratings, and human raters consistently score fluent, professional-sounding responses higher than responses that engage with adversarial constraints. The model has learned that the generic fallback is high-reward. Nothing in standard preference training pushes back on that.

---

## Measuring it before touching anything

If the model is collapsing to a template, its outputs will be semantically similar across diverse inputs regardless of what the probes were testing. You can measure this directly:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

def detect_response_collapse(responses: list[str], threshold: float = 0.90) -> dict:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(responses, normalize_embeddings=True)
    sim_matrix = embeddings @ embeddings.T
    np.fill_diagonal(sim_matrix, 0)
    n = len(responses)
    avg_sim = sim_matrix.sum() / (n * (n - 1))
    return {
        "avg_pairwise_similarity": round(float(avg_sim), 4),
        "collapse_detected": avg_sim > threshold,
        "most_similar_pair": np.unravel_index(sim_matrix.argmax(), sim_matrix.shape),
    }

# responses = [trace["model_output"] for trace in traces]
# print(detect_response_collapse(responses))
```

Run this on `held_out_traces.jsonl`. If `avg_pairwise_similarity` comes back above 0.90 across probes from different failure categories, you have confirmed collapse. The `most_similar_pair` index shows which two probes produced the most redundant outputs — start the investigation there.

There is no point changing anything before you know the shape of the problem.

---

## The judge has the same bias

Here is the uncomfortable part: Amare's judge is a fine-tuned Qwen2.5-0.5B trained on preference data. If that preference data rewarded fluent, on-brand responses without requiring engagement with the specific failure category, the judge learned the same bias as the model it evaluates. It scores the generic response favorably because it is well-formed and mentions the company name. It never checks whether the response actually engaged with the probe.

The fix is one prompt change: add a specificity criterion. Instead of "is this a good sales response?", ask "does this response directly address the specific constraint in this probe? Score 0 if this response could have been generated for any input." For Amare's six failure categories, that check needs to happen explicitly for each one. A generic response fails it automatically.

---

## What the preference dataset taught the model

The deeper problem is that neither the model nor the judge was ever shown that generic is wrong. Gao et al. (2022) demonstrated reward model overoptimization on a predictable curve: the harder you optimize a proxy reward signal, the more the model finds ways to satisfy the proxy without doing the actual task. If most "chosen" examples in the preference dataset happen to be fluent and contextually generic, the model learned that fluency is the signal.

The fix is contrastive negatives: preference pairs where a generic response is labeled "rejected" and a category-specific response is labeled "chosen." Even 20-30 pairs per failure category shifts the distribution. Without them, fine-tuning just sharpens the existing bias.

---

## What to do, in cost order

Run the collapse detector on existing traces first — costs nothing, tells you how bad the problem is. Then add the specificity criterion to the judge prompt — still costs nothing, and it will immediately surface the responses that were slipping through. If the problem persists after that, build out the contrastive negatives. That is the only fix that addresses the cause rather than just exposing the failure more clearly.

---

## Read these

- Holtzman et al. (2020), "The Curious Case of Neural Text Degeneration," ICLR 2020. [arxiv.org/abs/1904.09751](https://arxiv.org/abs/1904.09751). Why likelihood maximization produces generic, repetitive text, and what nucleus sampling does about it.
- Gao et al. (2022), "Scaling Laws for Reward Model Overoptimization." [arxiv.org/abs/2210.10760](https://arxiv.org/abs/2210.10760). The empirical curve showing where proxy reward optimization diverges from true performance.
- Tool: `sentence-transformers` with `all-MiniLM-L6-v2`. The collapse detector above runs on any batch of model outputs with two installs: `pip install sentence-transformers numpy`.
- If you want to attack this at decoding time without retraining: look up contrastive decoding (Li et al., 2022), which explicitly down-weights tokens the model assigns high probability to regardless of context.
