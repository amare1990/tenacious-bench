# Evening Call Summary Day 1

Written by Amare Kassa | Confirmed by Yonas Eshete

On Yonas’s explainer (LoRA intrinsic dimension): The LoRA formulation came through but some sections stated that gradient updates are low-rank without explaining why. I asked for the actual mechanism not just that it happens, but what property of fine-tuning causes it. I also asked for a rank recommendation tied to my specific dataset size rather than a general heuristic. Yonas revised to explain the task-specific subspace argument and pretraining feature reuse, and added a concrete number: rank 4–8 is likely sufficient for 618 pairs, rank 16 is a safe upper bound. That answered what I needed.

On my explainer in the initial review, I found that the explainer correctly described the LoRA formulation (ΔW = BA) and the intuition that fine-tuning updates lie in a low-dimensional subspace. However, I pointed out a key gap: it did not clearly explain _why_ gradient updates are low-rank in practice, nor did it connect that mechanism directly to the rank choice stated in my partner’s model_card.md (rank 16 for a 618-pair dataset).

During the discussion, I pushed on two points:

1. The explanation stated that gradients are low-rank but did not explain the underlying cause (task-specific subspace + reuse of pretrained features).
2. The rank recommendation was implicit rather than explicit — it did not clearly answer whether rank 16 was appropriate or excessive for this dataset.

In response, my partner revised the explainer to:

- explicitly explain that fine-tuning reweights existing pretrained features, causing gradients to concentrate in a low-dimensional task-specific subspace
- connect rank directly to intrinsic task dimensionality rather than treating it as a default hyperparameter
- provide a concrete recommendation: for a 618-pair preference dataset, rank 4–8 likely captures the full signal, with rank 16 acting as a safe upper bound

After revision, the explainer was more precise, better grounded in the actual model_card.md artifact, and directly answered the original question of how to choose rank instead of copying defaults.