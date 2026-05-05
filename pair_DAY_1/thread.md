# Thread

1/ My partner asked: why does LoRA work at all — and how do you choose rank instead of copying defaults?

Context: fine-tuning a Qwen 2.5 3B judge on a small 618-pair preference dataset.

2/ The key idea: fine-tuning does not learn new knowledge from scratch. It reorients existing features.

So the update ΔW is not full-rank. It lives in a low-dimensional subspace.

3/ LoRA exploits this:

ΔW ≈ B·A, where rank r ≪ d.

Instead of updating millions of parameters, you learn a few directions of change.

4/ Why is this valid?

Because task-specific gradients are structured: narrow domain, correlated updates, and a few latent factors like tone, persuasion, and constraint handling.

The gradient signal concentrates into a few dominant directions.

5/ What rank actually means:

r = number of independent adaptation directions.

r=4–8 captures the core signal.  
r=16 is a safe upper bound.  
r=32+ risks diminishing returns or overfitting.

6/ For a 618-pair dataset, the task is narrow.

The model is mostly learning persuasion quality, tone alignment, and constraint violations.

That means the intrinsic task dimension is small, so low rank is enough.

7/ So why did rank=16 work?

Not because it was necessarily optimal, but because it was probably above the true intrinsic rank.

The extra capacity likely went mostly unused.

8/ Practical takeaway:

Do not copy defaults blindly.

Run a quick sweep: r=4, r=8, r=16.

Pick the smallest rank that saturates validation performance.

9/ The real principle:

LoRA works because fine-tuning updates are inherently low-rank.

Not just as an approximation trick, but as a property of how pretrained models adapt to narrow tasks.

10/ Full explainer:

https://medium.com/@amaremek/stop-copying-lora-defaults-how-to-actually-choose-rank-for-fine-tuning-f6311f9f0ef7

Published thread:

https://x.com/amaremek/status/2051407182923452753