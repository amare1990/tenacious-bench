# Why LoRA Works: The Low-Rank Structure of Fine-Tuning and How to Choose Rank

By Amare Kassa

---

This question came from a gap in a real model card: why did we choose LoRA rank 16 for a small preference dataset, and what makes low-rank adaptation sufficient in the first place?

At a glance, LoRA looks like a parameter-saving trick. It replaces a full weight update ΔW with a low-rank decomposition ΔW ≈ B·A. But that only makes sense if the *true update we want* is already low-rank. The deeper question is: why is that true?

The key idea is that fine-tuning a pretrained model is not about learning new representations from scratch. Models like Qwen 2.5 3B already encode a rich, high-dimensional basis of language, reasoning, and structure. When we fine-tune on a narrow task—like judging sales persuasion—we are not inventing new features. We are reweighting and slightly rotating existing ones.

That has a very specific mathematical consequence: the gradients induced by the task lie in a low-dimensional subspace. Instead of needing independent updates across the entire parameter space, the model only needs a few coordinated directions of change. Empirically, this shows up as a rapidly decaying spectrum of gradient covariance: a few dominant directions carry most of the signal, and the rest are negligible.

LoRA simply enforces this structure explicitly. By constraining ΔW to rank r, it forces the update to live in a subspace spanned by r directions. If the true adaptation signal already lies in a low-dimensional manifold, this is not a restriction—it is a faithful representation.

You can see this effect even in a simple experiment. Below is a minimal sketch showing how performance changes as we vary rank during LoRA fine-tuning:

```python
# Pseudocode: LoRA rank sweep
ranks = [4, 8, 16]
results = {}

for r in ranks:
    model = load_pretrained_model()
    lora_model = apply_lora(model, rank=r)
    
    train(lora_model, train_dataset)
    acc = evaluate(lora_model, val_dataset)
    
    results[r] = acc

print(results)
```

On small, narrow datasets like a 618-pair preference task, you typically observe something like:

```python
{4: 0.81, 8: 0.82, 16: 0.82}
```

The performance saturates quickly. Increasing rank beyond a certain point does not improve results, because the task itself does not require additional independent directions of adaptation.

You can also see the same structure from the gradient side. If you compute the singular values of accumulated gradients during training, you’ll find that most of the energy is concentrated in the top few components:

```python
# Sketch: gradient spectrum
grads = collect_gradients(model, train_dataset)
U, S, Vt = np.linalg.svd(grads)

print(S[:10])  # top singular values
```

The rapid decay of S indicates that the update is intrinsically low-rank.

This gives us a concrete interpretation of rank. Rank r is not just a hyperparameter—it is the number of independent adaptation directions the model is allowed to use. Lower rank enforces stronger regularization and forces the model to focus on dominant signals. Higher rank increases flexibility but risks fitting noise, especially when the dataset is small.

In the case of a 618-pair preference dataset for sales judgment, the task is structurally simple. The model needs to distinguish between a small number of latent factors: persuasion quality, tone alignment, and constraint violations. This implies a low intrinsic dimension. In practice, ranks in the range of 4–8 are often sufficient to capture the full signal.

This reframes what happened in the original model card. Rank 16 “worked” not because it was optimal, but because it was safely above the intrinsic dimension of the task. The extra capacity simply went unused. A smaller rank would likely have achieved nearly identical performance.

This also gives a principled way to choose rank going forward. Instead of copying defaults, you can treat rank as a capacity knob tied to dataset size and task complexity. A simple approach is to run a small rank sweep (e.g., 4, 8, 16) and select the smallest rank that saturates validation performance. This ensures you capture the task signal without introducing unnecessary degrees of freedom.

The deeper takeaway is that LoRA is not just an efficiency trick. It works because fine-tuning itself is a low-dimensional problem. The model already knows how to represent the world; adaptation is just selecting the right directions within that space.

---

## Sources

* Hu et al., 2021 — *LoRA: Low-Rank Adaptation of Large Language Models*
  https://arxiv.org/abs/2106.09685

* Li et al., 2018 — *Measuring the Intrinsic Dimension of Objective Landscapes*
  https://arxiv.org/abs/1804.08838
